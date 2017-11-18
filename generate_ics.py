## Adds your timetable from `data.txt` to Google Calendar.
from __future__ import print_function
import os

import json
import datetime
import sys
import re
from icalendar import Calendar, Event

import build_event

DEBUG = False
GENERATE_ICS = True
TIMETABLE_DICT_RE ='([0-9]{1,2}):([0-9]{1,2}):([AP])M-([0-9]{1,2}):([0-9]{1,2}):([AP])M'
timetable_dict_parser = re.compile(TIMETABLE_DICT_RE)

OUTPUT_FILENAME = "timetable.ics"

UNTIL = build_event.generateIndiaTime(2017, 11, 30, 23, 59)

cal = Calendar()
cal.add('prodid', '-//Your Timetable generated by GYFT//mxm.dk//')
cal.add('version', '1.0')

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

def get_stamp(argument, date):
    '''
    argument is a 3-tuple such as
    ('10', '14', 'A') : 1014 HRS on date
    ('10', '4', 'P') : 2204 HRS on date
    '''

    hours_24_format = int(argument[0])

    # Note:
    # 12 PM is 1200 HRS
    # 12 AM is 0000 HRS

    if argument[2] == 'P' and hours_24_format != 12:
        hours_24_format = (hours_24_format + 12) % 24 

    if argument[2] == 'A' and hours_24_format == 12:
        hours_24_format = 0

    return build_event.generateIndiaTime(date.year,
            date.month,
            date.day,
            hours_24_format,
            int(argument[1]))

### days to number
days = {}
days["Monday"] = 0
days["Tuesday"] = 1
days["Wednesday"] = 2
days["Thursday"] = 3
days["Friday"] = 4
days["Saturday"] = 5
###

def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    now = datetime.datetime.now()

    # Get your timetable
    with open('data.txt') as data_file:    
        data = json.load(data_file)
    # Get subjects code and their respective name
    with open('subjects.json') as data_file:    
        subjects = json.load(data_file)
    for day in data:
        startDate = next_weekday(now, days[day])
        for time in data[day]:
            # parsing time from time_table dict
            # currently we only parse the starting time
            # the end time might be having error of 5 minutes
            # ex. : A class ending at 17:55 might be shown ending at 18:00

            parse_results = timetable_dict_parser.findall(time)[0]

            lectureBeginsStamp = get_stamp(parse_results[:3], startDate)
            lectureEndsStamp = get_stamp(parse_results[3:], startDate)

            lectureEndsStamp = lectureEndsStamp + \
                    datetime.timedelta(hours=data[day][time][2]-1)
            
            # Find the name of this class
            # Use subject name if available, else ask the user for the subject
            # name and use that
            # TODO: Add labs to `subjects.json`
            subject_code = data[day][time][0]
            summary = subject_code
            description = subject_code
            if (data[day][time][0] in subjects.keys()):
                summary = subjects[data[day][time][0]].title()
            else:
                print('ERROR: Our subjects database does not have %s in it.' %
                        subject_code);
                summary = input('INPUT: Please input the name of the course %s: ' %
                        subject_code)

                subjects[subject_code] = str(summary)

                summary = summary.title()

            # Find location of this class
            location = data[day][time][1]

            event = build_event.build_event(summary,
                    description,
                    lectureBeginsStamp,
                    lectureEndsStamp,
                    location,
                    "weekly",
                    UNTIL)

            cal.add_component(event)

            if (DEBUG):
                print (event)

    with open(OUTPUT_FILENAME, 'wb') as f:
        f.write(cal.to_ical())
        print("INFO: Your timetable has been written to %s" % OUTPUT_FILENAME)

if __name__ == '__main__':
    main()
