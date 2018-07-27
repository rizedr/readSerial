#!/usr/bin/env python
import serial
import sys
import time
import datetime
import requests
import dictionary
import os
import time
import logging
import logging.handlers
import dotenv

# configure syslog logging
logger = logging.getLogger('MyLogger')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address = '/var/run/syslog', facility='local1')  #pi (address = '/dev/log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
handler.setFormatter(formatter)
logger.addHandler(handler)
# Configure default logging
#logging.basicConfig(filename='debug.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
#logging.debug("Starting script....")

logger.debug("Starting script..")



#import secrets
VIANT_API=os.getenv("VIANT_API")
VIANT_API_VERSION=os.getenv("VIANT_API_VERSION")
ASSET_ID=os.getenv("ASSET_ID")
ACTION_NAME=os.getenv("ACTION_NAME")
SENSOR_UN=os.getenv("SENSOR_UN")
SENSOR_PW=os.getenv("SENSOR_PW")




# Define sensor id
id = 0

# Select USB0 if radio is connected to first USB port on Pi
logger.debug("Opening serial port")

try:
    ser = serial.Serial("/dev/cu.usbserial-DO00FUX5", 115200) # make sure baud rate is the same
    logger.info("Serial port open successfully")
except:
    logger.warning("Serial port open FAILED") 

# Read Serial port
def read_serial():
    logger.debug("Flushing serial I/O")
    ser.flushInput() 
    ser.flushOutput() 
    while True: # keep reading serial port and write to file till the end of time
        logger.debug("Waiting for serial data ...")
        #print("\nWaiting for serial data ...")
        data = ser.readline() #expecting this format -> "i:1,t:25.44,h:40.23,l:34.00\n"
        logger.info("Data received via serial")
        #print data
        if data[0]=='i': # check if data is not empty and entire string is being sent (first value is always "i", which is node ID)
            final_data = parse(data) # parse data
            #restAPI(final_data) # push data to HA via rest API
        else:
            logger.warning("Incomplete data packet received")

# Parse data string
def parse(data):
    final_data = {}
    for p in data.strip().split(","): #strip() removes trailing \n
        k,v = p.split(":")
        final_data[k] = v if v else 0.00
    logger.debug("Data parsed into dictionary")
    print (final_data)
    return final_data

# Publish data to Viant via restAPI
def restAPI(final_data):
    global id # use global id instead of local
    logger.debug("Building REST request")
    for k,v in final_data.iteritems():
        if k == '#': continue # skip group name
        #id = final_data.pop("i") #get sensor id
        st = dictionary.sensorType[k]
        su = dictionary.sensorUnit[k]
        si = dictionary.sensorIcon[k]
        sn = dictionary.sensorName[k]


        url = 'http://127.0.0.1:8123/api/states/sensor.%s_%s' % (st, id)
        headers = {'x-ha-access': 'Abudabu1!',
                'content-type': 'application/json'}

        data  = '{"state" : "%s", "attributes": {"friendly_name": "%s", "unit_of_measurement": "%s", "icon": "%s"}}' % (v, sn, su, si)
        logger.debug(data)
        req = requests.Request('POST', url, headers=headers, data=data)
        prepared = req.prepare()
        pretty_print_POST(prepared)
        logger.debug("Sending data via REST API")
        try:
            response = requests.post(url, headers=headers, data=data)
            logger.debug(response)
        except Exception as e:
            logger.exception(e)
        print(response.text)
        print("\nSending data via REST API\n")
        s = requests.Session()
        response = s.send(prepared)


# Print POST request in a pretty way
def pretty_print_POST(req):
    print('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


#run
read_serial()
