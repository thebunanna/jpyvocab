
from fsrs import FSRS, Card, Rating, State

import os
from openai import OpenAI
from dotenv import load_dotenv

import csv
import signal
import sys
import textwrap
from datetime import datetime, timezone, timedelta
import sqlite3
con = sqlite3.connect("jpy.db")
con.row_factory = sqlite3.Row

def get_next_due_card() -> tuple[dict, Card]:
    cur = con.cursor()
    card = dict (cur.execute("SELECT * FROM card order by due asc limit 1").fetchone())
    card_obj = Card.from_dict(dict(card))
    if card_obj.due > datetime.now(timezone.utc) + timedelta(days=1):
        current_card_length = int (dict (cur.execute("SELECT COUNT(*) FROM card").fetchone())['COUNT(*)'])
        
        for i in range (5):            
            cur.execute("INSERT INTO card (due, stability, difficulty, elapsed_days, scheduled_days, reps, lapses, state, last_review, vocab_id) \
                VALUES (:due, :stability, :difficulty, :elapsed_days, :scheduled_days, :reps, :lapses, :state, :last_review, :vocab_id)", 
                        {**(Card(due=datetime.now(timezone.utc), last_review=datetime.now(timezone.utc)).to_dict()), 'vocab_id' : current_card_length + 1 + i})
            
        card = dict (cur.execute("SELECT * FROM card order by due asc limit 1").fetchone())
        card_obj = Card.from_dict(dict(card))
    vocab = cur.execute("SELECT * FROM vocab where id = ?", (card['vocab_id'],)).fetchone()
    return dict(vocab), card_obj

fields = list (Card().to_dict().keys())
fields.append('last_review')

load_dotenv()

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def get_next() -> tuple[str, Card, dict[any]]:
    if not hasattr(get_next, 'redo'):
        get_next.redo = set()
        get_next.visted = set()
    vocab, next_card = get_next_due_card()
    # print (all_cards[ind][0], all_cards[ind][2])
    prev_sentences = con.cursor().execute("SELECT sentence FROM sentence WHERE word_id = ? order by id desc LIMIT 5", (vocab['id'],)).fetchall()
    
    if (vocab['id'] in get_next.redo or (vocab['id'] not in get_next.visted and next_card.state != State.Review)) and len(prev_sentences) != 0:
        get_next.visted.add(vocab['id'])
        return dict (prev_sentences[0])['sentence'], next_card, vocab
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": """Can you generate a Japanese sentence that has the vocab ({}) This vocab has the definition ({})? 
                    文が文法的に正しいことを確認してください.
                    I just want only the sentence and nothing else.
                    Do not include punctuation at the end of the sentence
                    Try not to use 'I am' or '私は' at the beginning of this sentence.
                    {}
                    {}
                    """.format(vocab['word'], vocab['translated'],
                               "" if len(prev_sentences) == 0 else "Be different than the following sentences", 
                               str([str(dict(x)['sentence']) + "\n" for x in prev_sentences])),
            }
        ],
        model="gpt-4o"
    )

    text = chat_completion.choices[0].message.content
    with con:
        con.execute("INSERT INTO sentence (sentence, word_id) VALUES (?, ?)", (text, vocab['id']))
    return text, next_card, vocab

import pykakasi
import nagisa

from jamdict import Jamdict
from fsrs import FSRS, Card, Rating, ReviewLog
from fugashi import Tagger
import requests
from bs4 import BeautifulSoup
from functools import lru_cache

scheduler = FSRS()
kks = pykakasi.kakasi()
jam = Jamdict()

@lru_cache(maxsize=128)
def get_parsed_str(text:str) -> tuple [list[str], str]:
    # tagger = nagisa.Tagger(single_word_list=[vocab['word']])
    # conv = tagger.tagging(text).words
    tagger = Tagger('-Owakati')
    conv = tagger.parse(text)
    kata = " ".join ([str (x.feature.kana) for x in tagger(text)])
    hira = " ".join(["".join([y['hira'] for y in kks.convert(str(x))]) for x in tagger(text)])
    return [kata, hira], conv
        

def get_detailed(text: str, size: int = 40):
    def is_hira(text: str):
        return all([ord(x) >= 12353 and ord(x) <= 12447 for x in text])
    def is_not_jp(text: str):
        return all([ord(x) < 128 for x in text])
    [kata, hira] , conv = get_parsed_str(text)
    res = [list(x) for x in zip(conv.split(" "), kata.split(" "), hira.split(" "))]
    conv = conv.split(" ")
    # for item in conv:
    #     res[item] = [item, "".join([y['hira'] for y in kks.convert(item)])]
        
    filt = ['']
    hira_arr = [is_hira(x[0]) or is_not_jp(x[0]) for x in res]
            
    for ind, item in enumerate (conv):
        if hira_arr[ind]:
            continue
            
        searches = [item]
        if ind != 0 and hira_arr[ind - 1]:
            searches.append(conv[ind - 1] + item)
        if ind != len(conv) - 1 and hira_arr[ind + 1]:
            searches.append(item + conv[ind + 1])
        # if hira_arr[ind - 1] and hira_arr[ind + 1]:
        #     searches.append(conv[ind - 1] + item + conv[ind + 1])
        
        for search in searches:
            entries = jam.lookup(search, strict_lookup=False).entries
            if len (entries) > 0:
                res[ind].extend([str(entries[0].kanji_forms), str(entries[0].kana_forms), 
                                        *[x for x in textwrap.wrap(str(entries[0].senses), width=size)]])
                break
            
            response = requests.get(f"https://jisho.org/search/{search}")
            try:            
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                jisho = soup.find("div", {"class": 'concept_light-representation'}).find("span", {"class": 'text'})
                if jisho:
                    entries = jam.lookup(jisho.get_text().strip(), strict_lookup=False).entries
                    if len (entries) > 0:
                        res[ind].extend([str(entries[0].kanji_forms) + f" - {jisho.get_text().strip()}", str(entries[0].kana_forms), 
                                                *[x for x in textwrap.wrap(str(entries[0].senses), width=size)]])
                        break
            except requests.exceptions.HTTPError as e:
                continue
            except AttributeError as e:
                continue
            finally:
                continue
    return res
            
def review_card(card: Card, ind: int, rating: Rating):
    card, log = scheduler.review_card(card, rating)    
    with con:
        con.execute("UPDATE card SET due = :due, stability = :stability, difficulty = :difficulty, elapsed_days = :elapsed_days, scheduled_days = :scheduled_days, reps = :reps, lapses = :lapses, state = :state, last_review = :last_review WHERE vocab_id = :vocab_id", 
                    {"vocab_id": ind, **(card.to_dict())})
    if rating < Rating.Good:
        get_next.redo.add(ind)
    else:
        if ind in get_next.redo:
            get_next.redo.remove(ind)
    return card

# # vocab, card = get_next_due_card()
# # review_card(card, vocab['card_id'], Rating.Easy)
# # print (get_next_due_card())
# print (dict (con.cursor().execute("SELECT * FROM card").fetchone()))

# print (get_next())
# print (get_parsed_str("今日は。今日はいいお天気ですね", {'word': '猫'}))
# print (kks.convert("今日は。今日はいいお天気ですね"))