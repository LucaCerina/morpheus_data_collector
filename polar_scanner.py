import threading
from time import sleep

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
    HRThreads[devName] = threading.Thread(name=devName,
                                          target=heartRateThread,
                                          args=[address])
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
        devices = scanner.scan(5)
        for dev in devices:
            # Get complete local name
            devName = dev.getValueText(0x9)
            if(devName):
                # Check if device is already present in the list
                if((devName[0:5] == 'Polar') & (devName not in polarDevices)):
                    polarDevices[devName] = dev.addr
                    print("Found " + devName + " " + dev.addr)
                    # Spawn an heart rate thread
                    triggerHRThread(devName, dev.addr)
        sleep(10.0)

# Spawn the scanner thread
scanThread = threading.Thread(name="scanner", target=polarScan)
scanThread.start()

# Spawn the control thread
controlThread = threading.Thread(name="controller", target=controllerHRThread)
controlThread.start()
