from datetime import datetime as dt, timedelta as td
from math import ceil, floor
import gspread
import oauth2client
import constants  # My own constant values.

gc = gspread.oauth()

consts = constants.get_constants()
SHEET_NAME = consts['SHEET_NAME']
COMP_PER_HR = consts['PER_HOUR_WAGE']

def format_fields(today, first_start, last_end, hrs_today: int, mins_today: int) -> list:
    hour_strs = [str(elt) for elt in [first_start.hour, last_end.hour, hrs_today]]
    min_strs = [str(elt) for elt in [first_start.minute, last_end.minute, mins_today]]

    for i in range(3):
        if len(hour_strs[i]) == 1: hour_strs[i] = '0' + hour_strs[i]
        if len(min_strs[i]) == 1: min_strs[i] = '0' + min_strs[i]

    formatted_start = f'{hour_strs[0]}:{min_strs[0]}'
    formatted_end = f'{hour_strs[1]}:{min_strs[1]}'
    formatted_dur = f'{hour_strs[2]}:{min_strs[2]}'
    formatted_day = f'{today.month}/{today.day}/{today.year}'

    assert len(formatted_dur) == 5
    return [formatted_day, formatted_start, formatted_end, formatted_dur]

def write_to_sheet(formatted_fields: list, hrs_today: int, mins_today: int, msg: str, midnight=False):
    sh = gc.open(SHEET_NAME)
    wsh = sh.get_worksheet(0)
    all_recs = wsh.get_all_records()

    # Again, might put this stuff in a function.

    if len(all_recs) == 0:
        # If first run.
        cumulative_work = '00:00'
    else:
        # Not the first time.
        cumulative_work = all_recs[-1]['Cumulative work (HH:MM)']

    cumulative_hrs, cumulative_mins = map(int, cumulative_work.split(':'))
    cumulative_hrs += hrs_today
    cumulative_mins += mins_today
    # format here!!
    cumulative_work = f'{cumulative_hrs}:{cumulative_mins}'
    
    cumulative_hrs += cumulative_mins/60  # Floating point number of hours.
    cumulative_compensation = round(COMP_PER_HR*cumulative_hrs, 2)  # Rounds up.
    
    row = formatted_fields + [msg, cumulative_work, cumulative_hrs, cumulative_compensation]
    print(row)
    wsh.append_rows([row])
    
    if midnight:
        # In case I'm doing this becaue the midnight signal went off,
        # I need to leave the message cell empty.
        # If it's NOT midnight, I need to check the previous message cell,
        # and write into it as well.
        pass
    
    print('Done writing.')

def ending_routine(today, record: list, midnight=False):
    assert len(record) > 0 and [len(elt) == 2 for elt in record]
    if not midnight:
        msg = input('Message\n>>> ')

    print('Calculating...')
    # how does this work with after midnight?
    # i think it works fine
    sum_dur = td()  # This is a timedelta object.
    for (start, end) in record:
        assert end > start
        diff = end - start
        sum_dur += diff  # Timedelta object with seconds & microseconds only.

    hours_float = sum_dur.seconds/3600
    hrs_today = floor(hours_float)
    mins_today = ceil((hours_float - hrs_today)*60)
    # print("hrs & mins today", hrs_today, mins_today)

    first_start = record[0][0]
    print("first start", first_start)
    last_end = first_start + sum_dur
    print("last end", last_end)

    formatted_fields = format_fields(today, first_start, last_end, hrs_today, mins_today)
    
    print("Now writing...")

    write_to_sheet(formatted_fields, hrs_today, mins_today, msg)
    
    return

def set_state(choice: str) -> str: # Doable with so many edge cases?
    pass

def start_session():
    state = 'RUNNING'
    today = dt.today()
    print('You started a session.')
    record = []  # List of tuples where each tuple is a pair of date objects (start, end).
    start = dt.now()
    while True:
        if state == 'RUNNING':
            choice = input('pause or end\n>>> ')
            # might abstract all this away into set_state(), or not
            # i'd need to make a dict to map commands to states
            # and maybe even map something (commands or states) to actions
            if choice == 'p' or choice == 'pause':
                print('Session paused.')
                state = 'PAUSED'
            elif choice == 'e' or choice == 'end':
                print('Session ended.')
                state = 'ENDED'
            end = dt.now()
            record.append((start, end))
        elif state == 'PAUSED':
            choice = input('restart or end\n>>> ')
            if choice == 'r' or choice == 'restart' or choice == 's' or choice == 'start':
                print('Session restarted.')
                state = 'RUNNING'
                start = dt.now()
            elif choice == 'e' or choice == 'end':
                print('Session ended.')
                state = 'ENDED'
                # Don't add anything in this case, because you already added when you paused.
        elif state == 'ENDED':
            ending_routine(today, record)
            break
        else:
            raise(ValueError)

if __name__ == '__main__':
    choice = input('Wanna start working?\n>>> ')
    if choice == 'y' or choice == 'yes':
        start_session()
