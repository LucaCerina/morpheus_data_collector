from multiprocessing import Process
from threading import Thread
from time import sleep
import os

import bluepy.btle as btle
from bluepy.btle import BTLEException

from polar_reader import heartRateThread

# Devices and current threads dictionaries
polarDevices = {}
HRThreads = {}

def triggerHRThread(devName, address):
    """
    This method spawns an heart rate monitor thread triggered by the Scanner
    The thread ends when the Polar device disconnects
    """
    HRThreads[devName] = Process(name=devName,
                                          target=heartRateThread,
                                          args=[devName, address])
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
    # Set BLE BAD STUFF
    os.system("echo 3200 > /sys/kernel/debug/bluetooth/hci0/supervision_timeout")
    os.system("echo 6 > /sys/kernel/debug/bluetooth/hci0/conn_min_interval")
    os.system("echo 7 > /sys/kernel/debug/bluetooth/hci0/conn_max_interval")

    # Spawn the scanner thread
    scanThread = Thread(name="scanner", target=polarScan)
    scanThread.start()

    # Spawn the control thread
    controlThread = Thread(name="controller", target=controllerHRThread)
    controlThread.start()
