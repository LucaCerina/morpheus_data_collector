import json
import sys
import os
import threading
from time import perf_counter, sleep

import requests
import udatetime

#import pmodad2
sys.path.append(os.getcwd()+'/necstcamp-polar-backend/ncamp-backend-mode/')
sys.path.append(os.getcwd()+'/necstcamp-polar-backend/')
#import polar_ncamp
import RPi.GPIO as GPIO
import si7021
from SPW2430_noise_NEW import SPW2430
from light_sensor import GA1A12S202
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from sgp30 import Sgp30
from smbus2 import SMBusWrapper


# thread controlling temperature and humidity
def TH_thread(config):
    thsensor = si7021.si7021(1)
    # List to save data when connection is absent
    backlog_record = []
    # header for API requests
    headers = {'Content-Type':'application/json'}
    headers['token'] = config['token']
    URL = 'https://staging.api.necstcamp.necst.it/sleep/send_room_data'

    while(True):
        # Wait 30 seconds
        sleep(30)
        # Read data from sensors
        temperature = thsensor.read_temperature()
        humidity = thsensor.read_humidity()
        # Assemble data
        timestamp = udatetime.to_string(udatetime.now())
        data = {}
        data['token'] = config['token']
        data['input'] = {'room_id': config['room_id'], 'timestamp': timestamp, 'temperature': json.dumps(temperature), 'humidity': json.dumps(humidity)} 
        # Send data to server
        try:
            print("Sending T {0:2.5} H {1:2.5} at time {2:}".format(temperature, humidity, timestamp))
            req = requests.post(url=URL, headers=headers, json=data)

            # Check request result
            if req.status_code != 200:
                print("Req status {}:saving TH record on backlog".format(req.status_code))
                backlog_record.append(data)
            else:
                while len(backlog_record) > 0 and requests.post(url=URL, headers=headers, json=backlog_record[0]).status_code == 200:
                    del backlog_record[0]
        except requests.exceptions.ConnectionError:
            print("Connection refused: saving TH record on backlog")
            backlog_record.append(data)

# Thread controlling CO2 readings
def carbon_thread(config):
    # List to save data when connection is absent
    backlog_record = []
    # header for API requests
    headers = {'Content-Type':'application/json'}
    headers['token'] = config['token']
    URL = 'https://staging.api.necstcamp.necst.it/sleep/send_room_data'
    # Setup GPIO switch for sensor reset
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(20, GPIO.IN)
    
    with SMBusWrapper(1) as bus:
        sgp = Sgp30(bus, baseline_filename = "sgpbaseline.txt")
        if(GPIO.input(20) == 1):
            print("Init baseline and store it")
            sgp.init_sgp()
            sgp.store_baseline()
        else:
            print("get baseline from file")
            sgp.try_set_baseline()
            sgp.store_baseline()
        
        sgp.read_measurements()
        # Warm up the sensor
        for _ in range(20):
            sleep(1)
            sgp.read_measurements()

        while(True):
            # Wait 1 second to keep sensor active
            for _ in range(30):
                sleep(1)
                # Read data from sensors
                co2 = sgp.read_measurements()
                co2 = getattr(co2, "data")[0]
            # Assemble data
            timestamp = udatetime.to_string(udatetime.now())
            data = {}
            data['token'] = config['token']
            data['input'] = {'room_id': config['room_id'], 'timestamp': timestamp, 'co2': json.dumps(co2)} 
            # Send data to server
            try:
                print("Sending CO2 {0:2} at time {1:}".format(co2, timestamp))
                req = requests.post(url=URL, headers=headers, json=data)

                # Check request result
                if req.status_code != 200:
                    print("Req status {}:saving CO2 record on backlog".format(req.status_code))
                    backlog_record.append(data)
                else:
                    while len(backlog_record) > 0 and requests.post(url=URL, headers=headers, json=backlog_record[0]).status_code == 200:
                        del backlog_record[0]
            except requests.exceptions.ConnectionError:
                print("Connection refused: saving CO2 record on backlog")
                backlog_record.append(data)

# Thread to read from TSL sensor ATTENTION SENSOR NEED ADDITONAL FRONTEND TO READ DATA CORRECTLY
def light_thread(config):
    # List to save data when connection is absent
    backlog_record = []
    # header for API requests
    headers = {'Content-Type':'application/json'}
    headers['token'] = config['token']
    URL = 'https://staging.api.necstcamp.necst.it/sleep/send_room_data'
   
    # create the spi bus
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    #create the chip select
    cs = digitalio.DigitalInOut(board.D5)
    mcp = MCP.MCP3008(spi, cs)
    #create an analog input channel on pin 0
    #chan = AnalogIn(mcp, MCP.P1)
    sensore = GA1A12S202(mcp)
    while(True):
        # Come misura della luce prenderei la stessa che aveva usato nel vecchio main che è una media di quelle
        # ottenute in 30 secondi (fa 60 prove con uno sleep di 0.5) 
        light = 0.0
        for _ in range(60):
            light = light + sensore.read_light()
            sleep(0.5)
        light = light / 60.0
       

        # Assemble data
        timestamp = udatetime.to_string(udatetime.now())
        data = {}
        data['token'] = config['token']
        data['input'] = {'room_id': config['room_id'], 'timestamp': timestamp, 'light': json.dumps(light)} 
        # Send data to server
        try:
            print("Sending LHT {0:4.5} at time {1:}".format(light, timestamp))
            req = requests.post(url=URL, headers=headers, json=data)

            # Check request result
            if req.status_code != 200:
                print("Req status {}:saving LIGHT record on backlog".format(req.status_code))
                backlog_record.append(data)
            else:
                while len(backlog_record) > 0 and requests.post(url=URL, headers=headers, json=backlog_record[0]).status_code == 200:
                    del backlog_record[0]
        except requests.exceptions.ConnectionError:
            print("Connection refused: saving LIGHT record on backlog")
            backlog_record.append(data)

# Thread TEMPORARY to read noise from ADC. it sends energy on 30 seconds
def noise_thread(config):
        # List to save data when connection is absent
    backlog_record = []
    # header for API requests
    headers = {'Content-Type':'application/json'}
    headers['token'] = config['token']
    URL = 'https://staging.api.necstcamp.necst.it/sleep/send_room_data'
   
    # Init sensor
    #create the spi  bus
    spi_n = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    #create the chip select
    cs_n = digitalio.DigitalInOut(board.D5)# non sappiamo a quale board collegarlo
    cs_n.direction = digitalio.Direction.OUTPUT
    cs_n.value = True
    #create mcp object
    mcp_n = MCP.MCP3008(spi_n, cs_n)
    #create an analog input channel
    #chan_n = AnalogIn(mcp_n, MCP.P0)#non sapppiamo a che pin è collegato
    sensore_n = SPW2430(mcp_n)


    while(True):
        # Wait 30 seconds
        #sleep(30)
        noise = 0
        counter = 0
        tStart = perf_counter()
        while(perf_counter() < (tStart + 30)):
            noise = noise + sensore_n.read_noise()
            counter = counter + 1
        noise = noise / counter

        # Assemble data
        timestamp = udatetime.to_string(udatetime.now())
        data = {}
        data['input'] = {'room_id': config['room_id'], 'timestamp': timestamp, 'noise': json.dumps(noise)} 
        data['token'] = config['token']
        # Send data to server
        try:
            print("Sending NOI {0:4.5} at time {1:}".format(noise, timestamp))
            req = requests.post(url=URL, headers=headers, json=data)

            # Check request result
            if req.status_code != 200:
                print("Req status {}:saving NOISE record on backlog".format(req.status_code))
                backlog_record.append(data)
            else:
                while len(backlog_record) > 0 and requests.post(url=URL, headers=headers, json=backlog_record[0]).status_code == 200:
                    del backlog_record[0]
        except requests.exceptions.ConnectionError:
            print("Connection refused: saving NOISE record on backlog")
            backlog_record.append(data)

def userLogin(username, password):
    headers = {'Content-Type': 'application/json'}
    data = {'username': username, 'password': password}
    req = requests.post('https://staging.api.necstcamp.necst.it/users/login', headers=headers, json=data)
    userJWT = json.loads(req.content.decode("utf-8"))['token']
    return userJWT

def sendEvent(config, typeEvent):
    headers = {'Content-Type': 'application/json'}
    timestamp = udatetime.to_string(udatetime.now())
    data = {'input' : {'user_id' : 6, 'type': typeEvent, 'timestamp': timestamp}}
    data['token'] = config['token']
    req = requests.post('https://staging.api.necstcamp.necst.it/sleep/set_event', headers=headers, json=data)

    if req.status_code != 200:
        print("ERROR {}:{}".format(req.status_code, req.content))
    else:
        print("EVENT OK")


# Main routine                       
if __name__ == "__main__":
    # Load Configuration JSON
    with open("config.json", "r") as configFile:
        config = json.load(configFile)

    config['token'] = userLogin(config["user"], config["pwd"])

    # Start temperature and humidity thread
    t1 = threading.Thread(target = TH_thread, args=(config,), name="TempHumi")

    # Start CO2 thread
    t2 = threading.Thread(target = carbon_thread, args=(config,), name="CO2")

    # Start Light thread
    t3 = threading.Thread(target = light_thread, args=(config,), name="LIGHT")

    # Start noise thread
    t4 = threading.Thread(target = noise_thread, args=(config,), name="NOISE")

    # Start Polar thread
    #scanner = polar_ncamp.PolarScanner()
    #t5 = threading.Thread(target = scanner.start(), name = "POLAR") 

    t1.start()
    sleep(0.2)
    t2.start()
    sleep(0.2)
    t3.start()
    sleep(0.2)
    t4.start()
    #sleep(0.2)
    #t5.start()

    # DEBUG ONLY send a sleep START event
    sendEvent(config, 'START')
    while(True):
        try:
            sleep(5)
        except KeyboardInterrupt:
            # DEBUG ONLY send a sleep STOP event
            sendEvent(config, 'STOP')
            break

