import curses

def main(stdscr):
    curses.curs_set(1)  # Show the cursor
    curses.start_color()
    curses.use_default_colors()

    stdscr.clear()
    stdscr.refresh()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
    
    # get next card and generated sentence here
    comp_str = "コーヒーには砂糖を入れますか"
    input_str = ""
    while True:
        key = stdscr.getch()
        
        if key == 27:  # ESC key to exit
            break
        elif key in (curses.KEY_BACKSPACE, 127, 8):  # Handle backspace
            input_str = input_str[:-1]
        elif key in (curses.KEY_ENTER, 10, 13):  # Enter key to submit
            input_str = ""
        else:
            input_str += chr(key)
        
        stdscr.clear()
        for x,y in zip (comp_str, input_str[:len(comp_str)].ljust(len(comp_str))):
            if x == y:
                stdscr.addstr(x, curses.color_pair(2))
            else:
                stdscr.addstr(x, curses.color_pair(1))
        stdscr.addstr("\n" + input_str)
        stdscr.refresh()

curses.wrapper(main)