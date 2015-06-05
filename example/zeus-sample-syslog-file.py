# -*- coding: utf-8 -*-

# Copyright 2015 Cisco Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from zeus.client import ZeusClient
import os
import random
from pyparsing import Word, alphas, Suppress, Combine, nums, string, Optional, Regex
from time import strftime
import datetime
import time

ZEUS_API = "http://api.ciscozeus.io"
BATCH_SIZE = 1000
NUMBER_OF_SAMPLES = 1000
auth_data = None

class Parser(object):
  def __init__(self):
    ints = Word(nums)
 
    month = Word(string.uppercase, string.lowercase, exact=3)
    day   = ints
    hour  = Combine(ints + ":" + ints + ":" + ints)
    
    timestamp = month + day + hour
 
    # hostname
    hostname = Word(alphas + nums + "_" + "-" + ".")
 
    # appname
    appname = Word(alphas + "/" + "-" + "_" + ".") + Optional(Suppress("[") + ints + Suppress("]")) + Suppress(":")
 
    # message
    message = Regex(".*")
  
    # pattern build
    self.__pattern =  timestamp + hostname + appname + message
    
  def parse(self, line):
    parsed = self.__pattern.parseString(line)
 
    payload              = {}
    payload["timestamp"] = strftime("%Y-%m-%d %H:%M:%S")
    payload["hostname"]  = parsed[3]
    payload["appname"]   = parsed[4]
    payload["pid"]       = parsed[5]
    payload["message"]   = parsed[6]
    
    return payload
 
token = raw_input("Enter Token: ")

z = ZeusClient(token, ZEUS_API)
print("Zeus client created with user token " + token)


print("\nGreat! We are now ready to start sending and receiving data.")

print("\nLets now post syslogs from file.")
print("We are going to send a log " + str(NUMBER_OF_SAMPLES) + " times in " +
      "groups of " + str(BATCH_SIZE) + ".")

message = ""

# Syslog sending
print("\nPOST request to http://api.ciscozeus.io/logs/" + token + "/syslog")
parser = Parser()

path= "<path>/example_syslog"
for dir_, _, files in os.walk(path):
    for fileName in files:
        relDir = os.path.relpath(dir_, path)
        relFile = os.path.join(relDir, fileName)
        fin = os.path.dirname(os.path.realpath(__file__)) + "/example_syslog" + str(relFile)[1:]
        with open(fin) as syslogFile:
            messages = [ {"timestamp": time.mktime(datetime.datetime.strptime(parser.parse(line)["timestamp"], "%Y-%m-%d %H:%M:%S").timetuple()), "message": parser.parse(line)["message"] } for line in syslogFile ]
            z.sendLog("syslog", messages)

print("User token: " + token)
print(
    "\nCongratulations! You now have syslogs in Zeus. Easy, " +
    "right?")
print("Lets now retrieve 10 logs from Zeus and see if they are what we sent.")
raw_input("\nPress ENTER to get 10 logs.")
os.system('clear')

# Log consumption
status, l = z.getLog('syslog', limit=10, attribute_name="message",
                     pattern=message)

if status == 200:
    print("\nLogs:")
    for log in l['result']:
        print(str(log['timestamp']) + ": " + log['message'])
    print("\nThere are currently " + str(l['total']) + " logs in your Zeus " +
          "account that match this query.")
else:
    print("\nThere has been an error retrieving logs. Are the parameters " +
          "correctly formatted?")
