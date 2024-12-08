

import csv
import signal
import sys
import pykakasi
from jamdict import Jamdict
from engine import get_next, get_parsed_str, get_detailed, review_card
import textwrap


kks = pykakasi.kakasi()
jam = Jamdict()

import curses

def main(stdscr):
    curses.curs_set(1)  # Show the cursor
    curses.start_color()
    curses.use_default_colors()

    maxh, maxw = stdscr.getmaxyx()
    
    stdscr.clear()
    stdscr.refresh()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
    
    text, card, info = get_next()    
    
    hira_str, comp_str  = get_parsed_str(text)
    
    comp_str_split = comp_str.split(" ")
    
    input_str = ""
    stdscr.clear()
    stdscr.addstr(info[0] + "\n")
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
        stdscr.addstr(info[0] + "\n")

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
    
    detailed = [[key, *value] for key, value in get_detailed(text, maxw/2).items()]

    ind = 0
    max_ind = len (detailed) - 1
    
    key = None
    while True:
        if key == curses.KEY_RIGHT:
            ind += 1
        elif key == curses.KEY_LEFT:
            ind -= 1
        elif key is not None and (key >= 48 and key <= 51):
            score = key - 47
            review_card(card, ind, score)
            break
        
        
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
            
        # stats here
        
        stdscr.addstr(0, maxw//2, f"{text}")
        stdscr.addstr(1, maxw//2, f"{str (info[:-2])}")
        stdscr.addstr(2, maxw//2, "----------------------")
        stdscr.addstr(3, maxw//2, f"Input : {input_str.split(' ')[ind]}")
        stdscr.addstr(4, maxw//2, f"Actual: {hira_str.split(' ')[ind]}")
            
        stdscr.addstr(maxh - 1, 0, "[<-] [->] [ESC] [0 - Perfect] [1 - Good] [2 - Bad] [3 - Terrible]")
        stdscr.refresh()
        key = stdscr.getch()

    stdscr.getch()

curses.wrapper(main)

while True:
    pass
