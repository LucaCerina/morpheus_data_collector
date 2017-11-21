import bluepy.btle as btle
from bluepy.btle import BTLEException
import threading
from Polar_Reader import heartDelegate, HRmonitor, heartRateThread
from time import sleep

scanner = btle.Scanner()
polarDevices = {}
HRThreads = {}

def triggerHRThread(deviceName, address):
    HRThreads[deviceName] = threading.Thread(name = deviceName, target = heartRateThread, args = [address])
    HRThreads[deviceName].start()

def controllerHRThread():
    while(True):
        sleep(10.0)
        destroyList = []
        for key in HRThreads:
            if not HRThreads[key].is_alive():
                destroyList.append(key)
        for item in destroyList:
            HRThreads.pop(item)
            polarDevices.pop(item)
            print("Thread " + key + " destroyed.")

def polarScan():
    while(True):
        devices = scanner.scan(5)
        for d in devices:
            # Get complete local name
            deviceName = d.getValueText(9) 
            if(deviceName):
                if((deviceName[0:5] == 'Polar') & (deviceName not in polarDevices)):
                    polarDevices[deviceName] = d.addr
                    print(deviceName + " " + d.addr)
                    triggerHRThread(deviceName, d.addr)
        sleep(10.0)

scanThread = threading.Thread(name = "scanner", target = polarScan)
scanThread.start()

controllerThread = threading.Thread(name = "controller", target=controllerHRThread)
controllerThread.start()


