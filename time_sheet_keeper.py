from datetime import datetime as dt, timedelta as td
# need td?
import gspread
import oauth2client
import constants  # My own constant values.

gc = gspread.oauth()

consts = constants.get_constants()
sheet_name = consts['SHEET_NAME']
comp_per_hr = consts['PER_HOUR_WAGE']

def format_fields():
    pass

def write_to_sheet():
    pass

def ending_routine(today, record: list, midnight=False):
    assert len(record) > 0 and [len(elt) == 2 for elt in record]
    # just forget about the midnight details for now
    print(record)
    if not midnight:  # can i do a decorator instead of this?
        msg = input('Message\n>>> ')
        
    # how does this work with after midnight?
    sum_dur = td()
    for (start, end) in record:
        assert end > start
        diff = end - start
        sum_dur += diff
        
    first_start = record[0][0]
    last_end = first_start + sum_dur
    formatted_start = f'{first_start.hour}:{first_start.minute}'
    formatted_end = f'{last_end.hour}:{last_end.minute}'
    formatted_day = f'{today.month}/{today.day}/{today.year}'
    hrs = (sum_dur.seconds//60)//60
    mins = sum_dur.seconds//60
    formatted_dur = f'{hrs}:{mins}'
    # i need to add a leading 0 if H or M is only 1 digit
    # also would like to round this up!
    print("now writing...")
    # just write into sheet now
    sh = gc.open(sheet_name) # <------- const to be taken away
    wsh = sh.get_worksheet(0)
    all_recs = wsh.get_all_records()

    # i should probably come back and rename total --> cumulative
    if len(all_recs) == 0:
        total_work = formatted_dur
    else:
        total_work = all_recs[-1]['Cumulative work (HH:MM)']
        total_hrs, total_mins = map(int, total_work.split(':'))
        hrs += total_hrs
        mins += total_mins
        total_work = f'{hrs}:{mins}'

    print('total work', total_work)

    hrs += mins/60
    compensation = round(comp_per_hr*hrs, 2)
    row = [formatted_day, formatted_start, formatted_end, formatted_dur, msg, total_work, compensation]
    print('row', row)
    wsh.append_rows([row])
    
    if midnight:
        # check if prev msg cell is empty
        # if so, do the thing
        pass
    print('done writing! bye!')
    return

def state_state(choice: str) -> str: # ?
    pass

def start_session():
    state = 'RUNNING'
    today = dt.today()
    print('You started a session. Good luck!')
    record = []  # List of tuples where each tuple is a pair of date objects.
    start = dt.now()
    while True:
        if state == 'RUNNING':
            choice = input('pause or end\n>>> ')
            # might abstract all this away into a set_state() function, or not
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
