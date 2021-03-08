from datetime import datetime as dt, timedelta as td
import gspread
import oauth2client
import constants  # My own constant values.

gc = gspread.oauth()

consts = constants.get_constants()
sheet_name = consts['SHEET_NAME']
comp_per_hr = consts['PER_HOUR_WAGE']

def format_fields(today, first_start, last_end, hrs_today: int, mins_today: int) -> list:
    formatted_day = f'{today.month}/{today.day}/{today.year}'
    formatted_start = f'{first_start.hour}:{first_start.minute}'
    formatted_end = f'{last_end.hour}:{last_end.minute}'

    if len(str(hrs_today)) == 1: hrs_today_str = '0' + str(hrs_today)
    if len(str(mins_today)) == 1: mins_today_str = '0' + str(mins_today)
    # should do the same thing for start & end
    formatted_dur = f'{hrs_today_str}:{mins_today_str}'
    assert len(formatted_dur) == 5
    return [formatted_day, formatted_start, formatted_end, formatted_dur]

def write_to_sheet(formatted_fields: list, hrs_today: int, mins_today: int, msg: str, midnight=False):
    sh = gc.open(sheet_name)
    wsh = sh.get_worksheet(0)
    all_recs = wsh.get_all_records()

    # Again, might put this stuff in a function.

    # If first run.
    if len(all_recs) == 0: cumulative_work = formatted_fields[3]  # Today's duration.
    else: cumulative_work = all_recs[-1]['Cumulative work (HH:MM)']
    
    cumulative_hrs, cumulative_mins = map(int, cumulative_work.split(':'))
    cumulative_hrs += hrs_today
    cumulative_mins += mins_today
    cumulative_work = f'{cumulative_hrs}:{cumulative_mins}'
    # again, append the 0 when there' one digit

    cumulative_hrs += cumulative_mins/60  # Floating point number of hours.
    cumulative_compensation = round(comp_per_hr*hrs_today, 2)
    
    row = formatted_fields + [msg, cumulative_work, cumulative_compensation]
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
    print(record)
    if not midnight:
        msg = input('Message\n>>> ')

    print('Calculating...')    
    # how does this work with after midnight?
    sum_dur = td()  # This is a timedelta object.
    for (start, end) in record:
        assert end > start
        diff = end - start
        sum_dur += diff

    hrs_today = (sum_dur.seconds//60)//60
    mins_today = sum_dur.seconds//60 + 1

    # One block.
    first_start = record[0][0]
    last_end = first_start + sum_dur

    formatted_fields = format_fields(today, first_start, last_end, hrs_today, mins_today)
    
    print("Now writing...")

    write_to_sheet(formatted_fields, hrs_today, mins_today, msg)
    
    return

def state_state(choice: str) -> str: # Doable with so many edge cases?
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
