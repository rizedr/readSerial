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
import os
import json
from dotenv import Dotenv
dotenv = Dotenv(os.path.join(os.path.dirname(__file__), ".env")) 
os.environ.update(dotenv)

#import environment variables
ENVIRONMENT=str(os.getenv("ENVIRONMENT"))
VIANT_API=str(os.getenv("VIANT_API"))
VIANT_API_VERSION=str(os.getenv("VIANT_API_VERSION"))
ASSET_ID=str(os.getenv("ASSET_ID"))
ASSET_STATE=str(os.getenv("ASSET_STATE"))
ASSET_STATE_ATTRIBUTE_NAME=str(os.getenv("ASSET_STATE_ATTRIBUTE_NAME"))
ACTION_NAME=str(os.getenv("ACTION_NAME"))
DELTA=float(os.getenv("DELTA"))
SENSOR_UN=str(os.getenv("SENSOR_UN"))
SENSOR_PW=str(os.getenv("SENSOR_PW"))
DEVICE_ID=os.getenv("DEVICE_ID")
SERIAL_PORT=str(os.getenv("SERIAL_PORT"))

# configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info("Starting script..")
logging.debug("Opening serial port")

try:
    ser = serial.Serial(SERIAL_PORT, 115200) # make sure baud rate is the same
    logging.debug("Serial port open successfully")
except:
    logging.warning("Serial port open FAILED") 

# Read Serial port
def read_serial():
    logging.debug("Flushing serial I/O")
    ser.flushInput() 
    ser.flushOutput() 
    while True: # keep reading serial port and write to file till the end of time
        logging.info("Waiting for serial data ...")
        data = ser.readline() #expecting this format -> "i:1,t:25.44,h:40.23,l:34.00\n"
        logging.info("Data received via serial")
        if data[0]=='i' and 'Setup' not in data:
            logging.info("Complete data packet received")
            parsed_data = parse(data)
            if int(parsed_data['i'])==42:
                updateAsset(parsed_data) 
        else:
            logging.warning("Incomplete data packet received")

# Dummy Read Serial port used for development
def dummy_read_serial():
    logging.info("Starting dummy reads")
    parsed_data = [
        {
            'h': "100",
            'c': "1000",
            't': "10"
        },
        {
            'h': "200",
            'c': "2000",
            't': "20"
        },
        {
            'h': "300",
            'c': "3000",
            't': "30"
        }
    ]
    i = 0
    while True:
        logging.info(i%3)
        updateAsset(parsed_data[i%3])
        i = i + 1

# Parse data string
def parse(data):
    logging.debug("Parsing:" + data)
    parsed_data = {}
    for p in data.strip().split(","): #strip() removes trailing \n
        k,v = p.split(":")
        parsed_data[k] = v if v else 0.00
    logging.debug("Data parsed into dictionary")
    print (parsed_data)
    return parsed_data

# Update the asset - validates state and then calls the action
def updateAsset(parsed_data):
    # Pause the script for DELTA seconds
    time.sleep(DELTA)

    url = VIANT_API + '/' + VIANT_API_VERSION + '/asset/' + ASSET_ID
    logging.debug(TOKEN)
    headers = {'Content-Type': 'application/json',
               'Authorization': TOKEN}
    
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        logging.exception(e)
    

    data = json.loads(response.text)
    logging.debug(data)

    state_attribute = None

    for attribute in data['attributes']:
        logging.debug(attribute)
        if attribute['name'] == ASSET_STATE_ATTRIBUTE_NAME:
            state_attribute = attribute
            logging.debug(state_attribute)

    if state_attribute is None:
        logging.exception('No State Machine attribute found')
        return

    current_state = attribute['value']

    if current_state == ASSET_STATE:
        pushSensorData(parsed_data)
    else:
        logging.warning("Asset not in valid state for update.")

# Publish data to Viant via restAPI
def pushSensorData(parsed_data):
    logging.debug("Building REST request")
    logging.debug(parsed_data)

    url = VIANT_API + '/' + VIANT_API_VERSION + '/asset/' + ASSET_ID + '/' + ACTION_NAME
    logging.debug(TOKEN)
    headers = {'Content-Type': 'application/json',
               'Authorization': TOKEN}
               

    data = '{"Humidity":"' + parsed_data['h'] + '","CO2":"' + parsed_data['c'] + '","Temperature":"' + parsed_data['t'] + '"}'
    logging.debug(data)

    logging.info("Sending data via REST API")
    try:
        response = requests.post(url, headers=headers, data=data)

    except Exception as e:
        logging.exception(e)
    logging.debug(response.text)
    logging.debug("\nSending data via REST API\n")

# Login to Treum API
def login():
    global TOKEN
    url = VIANT_API + '/' + VIANT_API_VERSION + '/auth'
    headers = {'Content-Type':'application/json'}
    payload = '{"username":"'+ SENSOR_UN +'","password":"' + SENSOR_PW +'"}'
    try:
        response = requests.post(url, headers=headers, data=payload)
        TOKEN = "JWT " + json.loads(response.text)['access_token']
        logging.debug(response)
    except Exception as e:
        logging.exception(e)

# Print POST request in a pretty way
def pretty_print_POST(req):
    logging.debug('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


#run
login()

if ENVIRONMENT == "development":
    logging.warning("The script is starting in dummy more. Change ENVIRONMENT variable.")
    dummy_read_serial()
else:
    read_serial()
