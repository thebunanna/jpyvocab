

import csv
import signal
import sys
import pykakasi
from jamdict import Jamdict
from engine import Engine, get_parsed_str, get_detailed
from audio import play_text
from translate import translate_text
import textwrap
import time


kks = pykakasi.kakasi()
jam = Jamdict()
engine = Engine()
import curses

def link(uri, label=None):
    if label is None: 
        label = uri
    parameters = ''

    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST 
    escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'

    return escape_mask.format(parameters, uri, label)

def main(stdscr):
    curses.curs_set(1)  # Show the cursor
    curses.start_color()
    curses.use_default_colors()

    maxh, maxw = stdscr.getmaxyx()
    
    stdscr.clear()
    stdscr.refresh()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
    
    while True: 
        text, card, info = engine.get_next()    
        
        t_str, comp_str = get_parsed_str(text)
        hira_str, kata_str = t_str
        comp_str_split = comp_str.split(" ")
        
        input_str = ""
        stdscr.clear()
        stdscr.addstr(info['word'] + "\n")
        stdscr.addstr(text + "\n")
        while True:
            key = stdscr.getch()
            
            if key == 27:  # ESC key to exit
                break
            elif key in (curses.KEY_BACKSPACE, 127, 8):  # Handle backspace
                input_str = input_str[:-1]
            elif key in (curses.KEY_ENTER, 10, 13):  # Enter key to submit
                if len (input_str.split(" ")) >= len(comp_str_split):
                    break
                else:
                    stdscr.addstr(maxh - 1, 0, "Please complete the sentence")
                    continue
            else:
                input_str += chr(key)
            
            stdscr.clear()
            stdscr.addstr(info['word'] + "\n")

            input_str_split = input_str.split(" ")

            for vocab in comp_str_split[:len(input_str_split)-1]:
                stdscr.addstr(vocab, curses.color_pair(2))
            
            if len(input_str_split) <= len(comp_str_split):
                stdscr.addstr(comp_str_split[len(input_str_split) - 1], curses.color_pair(3))    
            
            for vocab in comp_str_split[len(input_str_split):]:
                stdscr.addstr(vocab, curses.color_pair(1))
            
            stdscr.addstr("\n" + input_str)
            stdscr.refresh()
            
        stdscr.clear()   
        stdscr.refresh()
        
        detailed = get_detailed(text, maxw/2)

        ind = 0
        max_ind = len (detailed) - 1
        play_text(text)
        key = None
        while True:
            if key == curses.KEY_RIGHT:
                ind += 1
            elif key == curses.KEY_LEFT:
                ind -= 1
            elif key == ord('r'):
                play_text(text)
            elif key is not None and (key >= 48 and key <= 51):
                score = key - 47
                engine.review_card(card, info['id'], score)
                break
            elif key == ord('b'):
                engine.ban_word(comp_str_split[ind])
                        
            ind = max(0, min(ind, max_ind))
            stdscr.clear()

            for idx, vocab in enumerate(comp_str_split):
                if idx == ind:
                    stdscr.addstr(vocab, curses.color_pair(2))
                else: 
                    stdscr.addstr(vocab, curses.color_pair(1))
                
            for idx, line in enumerate(detailed[ind]):
                if idx == maxh - 1:
                    break
                stdscr.addstr(idx + 1, 0, line)
                
            stats = [
                f"{text}",
                translate_text(text),
                f"Input : {input_str.split(' ')[ind]}",
                f"Actual: {hira_str.split(' ')[ind]}, {kata_str.split(' ')[ind]}",
                f"Banned: {comp_str_split[ind] in engine.banned}",
                "----------------------",
                f"{info['word']} : {info['translated']} : {info['hira']}",
                f"rep - {card.scheduled_days} : state - {card.state}"
            ]
            
            for idx, line in enumerate(stats):
                stdscr.addstr(idx, maxw//2, line)
                
            stdscr.addstr(maxh - 1, 0, "[<-] [->] [ESC] [0 - Again] [1 - Hard] [2 - Good] [3 - Easy]")
            stdscr.refresh()
            key = stdscr.getch()

        stdscr.getch()

curses.wrapper(main)

while True:
    pass
