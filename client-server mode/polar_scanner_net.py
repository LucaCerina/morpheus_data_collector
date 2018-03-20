import sys
import threading
from multiprocessing import Process
from time import sleep

import bluepy.btle as btle
import zmq
from bluepy.btle import BTLEException

from polar_reader_client import heartRateThread

# Devices and current threads dictionaries
polarDevices = {}
HRThreads = {}

# Server address
SrvAddr = '127.0.0.1'

def triggerHRThread(devName, address):
    """
    This method spawns an heart rate monitor thread triggered by the Scanner
    The thread ends when the Polar device disconnects
    """
    global SrvAddr
    HRThreads[devName] = Process(name=devName,
                                          target=heartRateThread,
                                          args=[devName, address, SrvAddr])
    HRThreads[devName].start()

def controllerHRThread():
    """
    This method controls if an heart rate thread is ended (e.g disconnection)
    and delete the device from the list to be found again by the Scanner
    """
    while(True):
        sleep(10.0)
        destroyList = []
        # Generate destruction list without altering dictionary
        for key in HRThreads:
            if not HRThreads[key].is_alive():
                destroyList.append(key)
        # Pop destroyed elements from dictionary
        for item in destroyList:
            HRThreads.pop(item)
            polarDevices.pop(item)
            print("Thread " + item + " destroyed.")

def polarScan():
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
        except BTLEException as e:
            print(e)
            sleep(2)
            scanner = btle.Scanner()
        for dev in devices:
            # Get complete local name
            devName = dev.getValueText(0x9)
            if(devName):
                # Check if device is already present in the list
                if((devName[0:9] == 'Polar H10' or devName[0:9] == 'Polar OH1') & (devName not in polarDevices)):
                    polarDevices[devName] = dev.addr
                    print("Found " + devName + " " + dev.addr)
                    # Spawn an heart rate thread
                    triggerHRThread(devName, dev.addr)
        sleep(10.0)

if __name__ == "__main__":
    # Set server address
    if(len(sys.argv) > 1):
        SrvAddr = sys.argv[1]
    print(SrvAddr)

    # Ping the Server
    try:
        zContext = zmq.Context()
        zClient = zContext.socket(zmq.REQ)
        zClient.setsockopt(zmq.LINGER, 0)
        zClient.setsockopt(zmq.RCVTIMEO, 1000)
        zClient.connect('tcp://'+SrvAddr+':5555')
        zClient.send(b'PING', zmq.NOBLOCK)
        reply = zClient.recv(copy=False)
        if(reply.bytes != b'OK'):
            print('Server refused connection')
            sys.exit(1)
        else:
            print('Server is alive!')
    except zmq.error.Again:
        print("Server is offline")
        sys.exit(1)

    # Spawn the scanner thread
    scanThread = threading.Thread(name="scanner", target=polarScan)
    scanThread.start()

    # Spawn the control thread
    controlThread = threading.Thread(name="controller", target=controllerHRThread)
    controlThread.start()
