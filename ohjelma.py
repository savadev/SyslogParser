#!/usr/bin/python
# -*- coding: UTF-8 -*-

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
bEmail = False
eDict = {}
timeLogLocation = ""
data = {}
timeLogData = {}
eMessage = ""


#Read the config-file(file.json)
def ReadConfFiles():
	global timeLogData
	global data
	global timeLogLocation
	dirLocation = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	with open(os.path.join(dirLocation, 'file.json')) as data_file:
		data = json.load(data_file)

	timeLogLocation = (os.path.join(dirLocation, 'timelog.json')) 
	#check if file exists. If not, generate file and give the json object some dummy value
	if os.path.isfile(timeLogLocation):
		with open(timeLogLocation) as timeLog_file:
				timeLogData = json.load(timeLog_file)
	else:
		with open(timeLogLocation,"w+") as timeLog_file:
			timeLogData = json.loads('{"dummy" : "0"}')




#simplistic function to send email. SMTP needs to configured
def emailFunction(message):

	smtp = SMTP()
	smtp.connect(data["email_host"])	
	subj = "Some keyword(s) were found from recent logs"
	date = datetime.datetime.now().strftime( "%d/%m/%Y %H:%M" )
	msg = "From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % ( data["email_sender_address"], data["email_receiver_address"], subj, date, message )
	smtp.sendmail(data["email_sender_address"], data["email_receiver_address"], msg)
	smtp.quit()
	

		
#function uses regex to search lines from desired time period(usually 1 hour)
def keywordSearch(regSentence,location, keywords):

	global final_lines
	log_file = open(location, "r")
	log_lines = log_file.readlines()
	help_lines = []

	#fits on the time window, moved to another list

	for line in log_lines:
		searchKey = re.compile('^%s.{1,}' %regSentence )
		result = re.search(searchKey, line)
		if result:
			help_lines.append(result.group())
			#print result.group()
		
	#checking if there are any keywords on the list, if there are some; those will be appended to a list
	for line in help_lines:
		for keyword in keywords:
			if keyword in line:
				final_lines.append(line)
				#print line
						



#opens the time log, performs search
def execution(location,keywords):
	
	
	if location in timeLogData:
		lastOne = timeLogData[location]		
	else:
		lastOne = str(datetime.datetime.now() - timedelta(hours=1))
			
	dt = datetime.datetime.strptime(lastOne, '%Y-%m-%d %H:%M:%S.%f')
		
	#print dt.strftime('%b %d %H:')
	#how long has it been since last execution?
	#the last execution was done yesterday?
		
	if dt.hour > datetime.datetime.now().hour:
		timeSinceLast = (24 - dt.hour) + datetime.datetime.now().hour		
	else:	
		timeSinceLast = datetime.datetime.now().hour - dt.hour  
	#print "It has been", timeSinceLast, "hours since last execution"

	for i in range(0, timeSinceLast):
		apumuuttuja = dt + timedelta(hours=(i))
		if apumuuttuja.day < 10:
			apumuuttuja = str(apumuuttuja.strftime('%b %d %H:')) 
			apumuuttuja = apumuuttuja.replace("0"," ",1)
			keywordSearch(apumuuttuja,location,keywords)
		else:
			apumuuttuja = str(apumuuttuja.strftime('%b %d %H:')) 
			keywordSearch(apumuuttuja,location,keywords)


		


def RegexSearchFunction(filepath):
	
	folder = os.path.split(filepath)[0] + "/"
	Key = os.path.split(filepath)[1]
	
	#make a list of files 
	fileList = os.listdir(folder)

	return_list = []

	#regex-match. Find every file matching and save to list.
	Key = "^" + Key.replace("*", ".*")	
	for line in fileList:
		if re.match(Key, line): 
			return_list.append(line)

	#Add location path to filenames
	for i in range(0, len(return_list)):
		return_list[i] = folder + return_list[i]
	

	
	return return_list


#main loop for the application
def MainLoop():
	global data
	global final_lines
	global eDict
	global timeLogData
	
	for line in data["log_files"]:
		keywords = line["keywords"]
		
		location = line["location"]
		#any asterisks in path? 
		if "*" in line["location"]:
			searched_lines = RegexSearchFunction(location)
			for line in searched_lines:
				location = line
				execution(location,keywords)
				eDict[location] = final_lines
				final_lines = []
				timeLogData[line] = str(datetime.datetime.now())
	
		else:
			execution(location,keywords)
			eDict[location] = final_lines	
			final_lines = []
			timeLogData[location] = str(datetime.datetime.now())
		



#writing dictionary to msg_list, checking if there are any empty keys(we dont want to send any empty lines)
def EmailFormat():
	global eDict
	global eMessage
	eMesssage = '\n'
	for log_name, lines in eDict.items():
		if lines:	
     			emessage += log_name
     			emessage += "~"*70
     		for line in lines:
        		emessage += line
			emessage += "\n"
	#print eMesssage



#save json dump to the timelog 
def SaveDictionary():
	with open(timeLogLocation, 'w') as outfile:
		json.dump(timeLogData, outfile)


def mainFunc():
	global eMessage
	ReadConfFiles()
	MainLoop()
	if eDict:
		EmailFormat()
		emailFunction(eMessage)
	SaveDictionary()

mainFunc()
