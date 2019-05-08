import os
import sys
from threading import Thread
from multiprocessing import Process

import udatetime  # RFC3339 required by influxDB
from datetime import timedelta

import bluepy.btle as btle
sys.path.append(os.getcwd()+'/../')
from heartDelegate import HRmonitor, heartDelegate
from time import sleep, time
import zmq
import requests

def transformMessage(message, recvTime):
    output = dict()
    output['measurement'] = "polar_data"
    output['tags'] = {'device': message['deviceID']}
    output['time'] = message['time']
    output['fields'] = {'HR': message['HR'], 'RR': message['RR']}
    return output

def heartRateThread(devName, address, SrvAddr='127.0.0.1'):
    """
    This method instantiate the heart rate monitor and read data from it.
    The method automatically manage read failures and terminate on complete
    disconnection
    """
    # Disconnections counter
    disconnCounter = 0
    # Time sampling
    sampleTimeNew = 0
    sampleTimeOld = 0
    # Reading index
    readIdx = 0

    # Initialize the ZMQ connection
    zContext = zmq.Context()
    zSocket = zContext.socket(zmq.PUSH)
    zSocket.setsockopt(zmq.SNDTIMEO, 300)
    zSocket.setsockopt(zmq.RCVTIMEO, 300)
    zSocket.connect('tcp://'+SrvAddr+':3000')
    deviceID = devName.split(' ')[2]

    # Initialize Heart Rate monitor
    monitor = HRmonitor(devName, address)
    # Activate the monitor only on correct connection
    if(monitor.device != None):
        # Start the monitor
        monitorStarted = monitor.startMonitor()

        # Initialize sampleTime
        sampleTimeOld = time() 
        # Reader continuous loop
        k = 0
        while(True and monitorStarted):
            try:
                reading = monitor.getHeartRate()
                if k > 10:
                    monitor.keepalive()
                    k = 0
                else:
                    k = k + 1
                sampleTimeNew = time()
                #sleep(0.1)
                if(reading["HR"] != 0):
                    # Limit HR to 222bpm and/or avoid false readings
                    if(sampleTimeNew - sampleTimeOld > 0.27):
                        sampleTimeOld = sampleTimeNew
                        timeString = udatetime.to_string(udatetime.fromtimestamp(sampleTimeNew))
                        # output = str(time()) + '\t' + str(beat) + '\t' + str(readIdx) + '\n'
                        # output = str(time()) + '\t' + str(beat) + '\t' + deviceID + '\n'
                        if(reading['RR']):
                            print(reading['RR'])
                            for i in range(len(reading['RR'])):
                                timeString = udatetime.to_string(udatetime.fromtimestamp(sampleTimeNew) + timedelta(milliseconds=reading['RR'][i]))
                                output = {'time': timeString, 'HR':reading["HR"], 'RR':reading["RR"][i], 'deviceID':deviceID}
                                zSocket.send_json(output, zmq.NOBLOCK)
                        else:
                            output = {'time': timeString, 'HR':reading["HR"], 'RR':-1, 'deviceID':deviceID}
                            zSocket.send_json(output, zmq.NOBLOCK)
                        # filePointer.write(output)
                        #zSocket.send_string(output)
                        #zSocket.send_json(output, zmq.NOBLOCK)
                    # Reset disconnection counter for read failures
                    disconnCounter = 0
                else:
                    print("read failure")
                    raise(btle.BTLEException("conn fail"))
            except KeyboardInterrupt:
                # Terminate the thread on manual interrupt TODO: not the best way
                monitor.stopMonitor()
                monitor.terminate()
                break
            except btle.BTLEException as e:
                print("disconnection")
                # Update counter
                disconnCounter += 1
                # Try connection only for momentary disconnections
                if(disconnCounter < 3):
                    monitor.keepalive()
                else:
                    # monitor.terminate()
                    break

        # Close file
        zSocket.close()

class PolarScanner():
    
    def __init__(self):
        # Devices and current threads dictionaries
        self._polarDevices = {}
        self._HRThreads = {}
        self._SrvAddr = '127.0.0.1'

    def triggerHRThread(self, devName, address):
        """
        This method spawns an heart rate monitor thread triggered by the Scanner
        The thread ends when the Polar device disconnects
        """
        self._HRThreads[devName] = Process(name=devName,
                                            target=heartRateThread,
                                            args=[devName, address, self._SrvAddr])
        self._HRThreads[devName].start()

    def controllerHRThread(self):
        """
        This method controls if an heart rate thread is ended (e.g disconnection)
        and delete the device from the list to be found again by the Scanner
        """
        while(True):
            sleep(10.0)
            destroyList = []
            # Generate destruction list without altering dictionary
            for key in self._HRThreads:
                if not self._HRThreads[key].is_alive():
                    destroyList.append(key)
            # Pop destroyed elements from dictionary
            for item in destroyList:
                self._HRThreads.pop(item)
                self._polarDevices.pop(item)
                print("Thread " + item + " destroyed.")

    def serverThread(self, config):
        # ZeroMQ server
        zContext = zmq.Context()
        zServer = zContext.socket(zmq.PULL)
        zServer.bind('tcp://*:3000')
            
        # List to save data when connection is absent
        backlog_record = []
        # header for API requests
        headers = {'Content-Type':'application/json'}
        headers['token'] = config['token']
        URL = 'https://staging.api.necstcamp.necst.it/sleep/send_hr_data'

        print("Polar Listening on port 3000...")
        while True:
            try:
                message = zServer.recv_json()
                print(message)
                # Assemble data
                data = {}
                data['input'] = {'user_id': message['deviceID'], 'timestamp': message['time'], 'hr_data': message['HR']} 
                # Send data to server
                try:
                    print("Sending HR {0:} RR {1:} at time {2:}".format(message['HR'],  message['RR'], message['time']))
                    req = requests.post(url=URL, headers=headers, json=data)

                    # Check request result
                    if req.status_code != 200:
                        print("Req status {}:saving HR record on backlog".format(req.status_code))
                        backlog_record.append(data)
                    else:
                        while len(backlog_record) > 0 and requests.post(url=URL, headers=headers, json=backlog_record[0]).status_code == 200:
                            del backlog_record[0]
                except requests.exceptions.ConnectionError:
                    print("Connection refused: saving HR record on backlog")
                    backlog_record.append(data)
            except KeyboardInterrupt:
                break
    
        zServer.close()
        zContext.term()

    def polarScan(self):
        """
        This method defines the BLE scanner that searches Polar devices and trigger
        the heart rate thread when a new device is found
        """
        # Create scanner object
        scanner = btle.Scanner()
        while (True):
            # Scan devices
            try:
                devices = scanner.scan(5)
            except btle.BTLEException as e:
                print(e)
                sleep(2)
                scanner = btle.Scanner()
            for dev in devices:
                # Get complete local name
                devName = dev.getValueText(0x9)
                if(devName):
                    # Check if device is already present in the list
                    if((devName[0:9] == 'Polar H10' or devName[0:9] == 'Polar OH1') & (devName not in self._polarDevices)):
                        self._polarDevices[devName] = dev.addr
                        print("Found " + devName + " " + dev.addr)
                        # Spawn an heart rate thread
                        self.triggerHRThread(devName, dev.addr)
            sleep(10.0)

    def start(self, config):
        # Set BLE BAD STUFF
        os.system("echo 3200 > /sys/kernel/debug/bluetooth/hci0/supervision_timeout")
        os.system("echo 6 > /sys/kernel/debug/bluetooth/hci0/conn_min_interval")
        os.system("echo 7 > /sys/kernel/debug/bluetooth/hci0/conn_max_interval")

        # Spawn the server thread
        servThread =  Thread(name="server", target=self.serverThread, args=(config,))
        servThread.start()

        # Spawn the scanner thread
        scanThread = Thread(name="scanner", target=self.polarScan)
        scanThread.start()

        # Spawn the control thread
        controlThread = Thread(name="controller", target=self.controllerHRThread)
        controlThread.start()
