#!/usr/bin/python
# -*- coding: UTF-8 -*-
# added comment here
import json
import datetime
from datetime import timedelta
import time
import os
import re
import io
import smtplib
import calendar
from smtplib import SMTP
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders


final_lines = []
data = {}
send_email = False
email_dictionary = {}
email_message = ""
timelog_location = ""
timelog_data = {}


# Read the config-file(file.json)
def read_configuration_files():
    global timelog_data
    global data
    global timelog_location
    directory_location = os.path.realpath(
        os.path.join(os.getcwd(),
        os.path.dirname(__file__)))
    with open(os.path.join(directory_location, 'file.json')) as data_file:
        data = json.load(data_file)

    timelog_location = (os.path.join(directory_location, 'timelog.json'))

    # check if file exists. If not, generate file and give
    # the json object some dummy value
    if os.path.isfile(timelog_location):
        with open(timelog_location) as timelog_file:
            timelog_data = json.load(timelog_file)
    else:
        with open(timelog_location, "w+") as timelog_file:
            timelog_data = json.loads('{"dummy" : "0"}')


# simplistic function to send email. SMTP needs to configured
def email_function(message):

    smtp = SMTP()
    smtp.connect(data["email_host"])
    subj = "Some keyword(s) were found from recent logs"
    date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    msg = "From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s"\
          % (data["email_sender_address"],
             data["email_receiver_address"],
             subj, date, message)

    smtp.sendmail(data["email_sender_address"],
                  data["email_receiver_address"], msg)
    smtp.quit()


# function uses regex to search lines from desired time period(usually 1 hour)
def keyword_search(regex_pattern, location, keywords):

    global final_lines
    global send_email
    log_file = open(location, "r")
    log_lines = log_file.readlines()
    help_lines = []

    # fits on the time window, moved to another list#
    for line in log_lines:
        search_key = re.compile('^%s.{1,}' % regex_pattern)
        result = re.search(search_key, line)
        if result:
            help_lines.append(result.group())
            # print result.group()

    # checking if there are any keywords on the list
    # if there are some; those will be appended to a list
    for line in help_lines:
        for keyword in keywords:
            if keyword in line:
                final_lines.append(line)
                send_email = True
                # print line


# opens the time log, performs search
def execution(location, keywords):

    if location in timelog_data:
        last_one = timelog_data[location]
    else:
        last_one = str(datetime.datetime.now() - timedelta(hours=1))

    dt = datetime.datetime.strptime(last_one, '%Y-%m-%d %H:%M:%S.%f')

    # print dt.strftime('%b %d %H:')
    # how long has it been since last execution?
    # the last execution was done yesterday?

    if dt.hour > datetime.datetime.now().hour:
        time_since_last = (24 - dt.hour) + datetime.datetime.now().hour
    else:
        time_since_last = datetime.datetime.now().hour - dt.hour
    # print "It has been", time_since_last, "hours since last execution"

    for i in range(0, time_since_last):
        date_variable = dt + timedelta(hours=i)
        if date_variable.day < 10:
            date_variable = str(date_variable.strftime('%b %d %H:'))
            date_variable = date_variable.replace("0", " ", 1)
            keyword_search(date_variable, location, keywords)
        else:
            date_variable = str(date_variable.strftime('%b %d %H:'))
            keyword_search(date_variable, location, keywords)


def regex_search_function(filepath):

    folder = os.path.split(filepath)[0] + "/"
    file_key = os.path.split(filepath)[1]

    # make a list of files
    file_list = os.listdir(folder)
    return_list = []

    # regex-match. Find every file matching and save to list.
    file_key = "^" + file_key.replace("*", ".*")
    for line in file_list:
        if re.match(file_key, line):
            return_list.append(line)

    # Add location path to filenames
    for i in range(0, len(return_list)):
        return_list[i] = folder + return_list[i]

    return return_list


# main loop for the application
def main_loop():
    global data
    global final_lines
    global email_dictionary
    global timelog_data

    for line in data["log_files"]:
        keywords = line["keywords"]
        location = line["location"]
        # any asterisks in path?
        if "*" in line["location"]:
            searched_lines = regex_search_function(location)
            for s_line in searched_lines:
                location = s_line
                execution(location, keywords)
                email_dictionary[location] = final_lines
                final_lines = []
                timelog_data[line] = str(datetime.datetime.now())

        else:
            execution(location, keywords)
            email_dictionary[location] = final_lines
            final_lines = []
            timelog_data[location] = str(datetime.datetime.now())


# writing dictionary to message list,
# checking if there are any empty keys(we don't want to send any empty lines)
def email_format():
    global email_dictionary
    global email_message
    email_message = '\n'
    for log_name, lines in email_dictionary.items():
        if lines:
            email_message += log_name
            email_message += "~"*70
            for line in lines:
                email_message += line
                email_message += "\n"
    # print email_message


# save json dump to the timelog
def save_dictionary():
    with open(timelog_location, 'w') as outfile:
        json.dump(timelog_data, outfile)


def main():
    global email_message
    read_configuration_files()
    main_loop()
    if send_email:
        email_format()
        email_function(email_message)
    save_dictionary()

main()
