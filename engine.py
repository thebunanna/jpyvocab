
from fsrs import FSRS, Card, Rating

import os
from openai import OpenAI
from dotenv import load_dotenv

import csv
import signal
import sys
import textwrap
from datetime import datetime, timezone, timedelta

fsrs_cards = []   
all_cards = []

def get_next_due_card() -> tuple[int, Card]:
    return min(enumerate(fsrs_cards), key=lambda x: x[1].due)

def signal_handler(sig, frame):
    print ('saving cards')
    with open('fsrs_card.csv', 'w+') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for card in fsrs_cards:
            writer.writerow(card.to_dict())
    sys.exit(0)

# Set up the signal handler
signal.signal(signal.SIGINT, signal_handler)

with open('n5_randomized.csv', 'r') as file:
    csv_reader = csv.reader(file)
    all_cards = [x for x in csv_reader]

fields = list (Card().to_dict().keys())
fields.append('last_review')

with open('fsrs_card.csv', 'a+') as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    
    current_cards = file.readlines()

    csv_reader = csv.reader(file)
    fsrs_cards = [x for x in csv_reader]
    
    if (len (fsrs_cards) != len (all_cards)):
        fsrs_cards.extend([Card(due=datetime.now() + timedelta(days=x / 5)) for x in range(len(all_cards) - len(fsrs_cards))])
            
    assert len(fsrs_cards) == len(all_cards)
load_dotenv()

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def get_next() -> tuple[str, Card, list[any]]:
    
    ind, next_card = get_next_due_card()
    # print (all_cards[ind][0], all_cards[ind][2])

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": """Can you generate a Japanese sentence that has the vocab ({}) This vocab has the definition ({})? 
                    
                    I just want only the sentence and nothing else.
                    Do not include punctuation at the end of the sentence
                    """.format(all_cards[ind][0], all_cards[ind][2]),
            }
        ],
        model="gpt-4o"
    )

    text = chat_completion.choices[0].message.content
    
    return text, next_card, all_cards[ind]

import pykakasi
from jamdict import Jamdict
from fsrs import FSRS, Card, Rating, ReviewLog

scheduler = FSRS()
kks = pykakasi.kakasi()
jam = Jamdict()

def get_parsed_str(text:str) -> tuple [str, str]:
    conv = kks.convert(text)
    return " ".join([x['hira'] for x in conv]), " ".join([x['orig'] for x in conv])
        

def get_detailed(text: str, size: int = 40):
    conv = kks.convert(text)
    res = {}
    for item in conv:
        res[item['orig']] = [item['kana'], item['hira']]
        
    filt = ['']
    for item in conv:
        # 12352 - 12447  is hiragana
        if len (item['orig']) == 1 and (ord(item['orig']) >= 12352 and ord(item['orig']) <= 12447):
            filt.append(filt[-1])
            filt[-1] += "%" + item['orig']
        else:
            filt.append(item['orig'])
        entries = jam.lookup(filt[-1], strict_lookup=False).entries
        if len (entries) > 0:
            res[item['orig']].extend([str(entries[0].kanji_forms), str(entries[0].kana_forms), 
                                      *[x for x in textwrap.wrap(str(entries[0].senses), width=size)]])
    # for item in [x for x in filt if x != '']:
    #     entries = jam.lookup(item, strict_lookup=True).entries

    #     if len (entries) > 0:
    #         res += ">>> {}\n".format(entries[0])
            
    return res
            
def review_card(card: Card, ind: int, rating: Rating):
    card, log = scheduler.review_card(card, rating)    
    fsrs_cards[ind] = card
    return card