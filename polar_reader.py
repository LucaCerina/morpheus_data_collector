import os
import sys
import uuid
from time import sleep

import bluepy.btle as btle
from bluepy.btle import BTLEException
from tendo import singleton


class heartDelegate(btle.DefaultDelegate):
    """
    Bluepy delegate that handles the recognition of heartbeats
    """
    message = 0

    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        # Heart rate handle
        if(cHandle == 37):
            # HR beats-per-minute byte
            self.message = data[1]

    def getLastBeat(self):
        """
        Access the delegate message
        """
        return self.message

class HRmonitor():
    """
    This class contains the methods necessary to connect to the device.
    Specifically the Polar OH1.
    """
    # Useful GATT descriptors
    CCC_descriptor_uuid = "00002902-0000-1000-8000-00805f9b34fb"
    heartRate_service_uuid = "0000180d-0000-1000-8000-00805f9b34fb"
    heartRate_measure_uuid = "00002a37-0000-1000-8000-00805f9b34fb"
    battery_service_uuid = "0000180f-0000-1000-8000-00805f9b34fb"

    def __init__(self, address):
        self.address = address
        try:
            # Connect to the device
            self.device = btle.Peripheral(self.address)
            self.device.setDelegate(heartDelegate())
            print("Connected to: " + self.address)
        
            # Read descriptors
            self.heartrate_service = self.device.getServiceByUUID(self.heartRate_service_uuid)
            self.CCC_descriptor = self.heartrate_service.getDescriptors(forUUID = self.CCC_descriptor_uuid)[0]
        except BTLEException as e:
            # Return None if connection fails
            self.device = None

    def startMonitor(self):
        """
        This method starts the Polar monitor by writing the CCC descriptor
        """
        try:
            print("Writing CCC...")
            self.CCC_descriptor.write(b"\x01\x00", withResponse=False)
            sleep(1.0)
            print("CCC value: " + str(self.CCC_descriptor.read()))
        except Exception as e:
            print(e)

    def stopMonitor(self):
        """
        This method stops the Polar monitor by resetting the CCC descriptor
        """
        self.CCC_descriptor.write(b"\x00\x00", withResponse=False)

    def terminate(self):
        """
        This method terminates the connection with the device
        """
        try:
            self.device.disconnect()
        except Exception as e:
            print(e)

    def getHeartRate(self):
        """
        This method wait the HR notification and return its value, otherwise it
        returns 0
        """
        try:
            self.device.waitForNotifications(1.0)
            return self.device.delegate.getLastBeat()
        except Exception as e:
            return 0
            print(e)

def heartRateThread(address):
    """
    This method instantiate the heart rate monitor and read data from it.
    The method automatically manage read failures and terminate on complete
    disconnection
    """
    # Disconnections counter
    disconnCounter = 0

    # Initialize Heart Rate monitor
    monitor = HRmonitor(address)
    # Activate the monitor only on correct connection
    if(monitor.device != None):
        monitor.startMonitor()

        # Reader continuous loop
        while(True):
            try:
                beat = monitor.getHeartRate()
                sleep(1.0)
                if(beat != 0):
                    print(beat)
                    # Reset disconnection counter for read failures
                    disconnCounter = 0
                else:
                    print("read failure")
                    raise(BTLEException(BTLEException.DISCONNECTED, "conn fail"))
            except KeyboardInterrupt:
                # Terminate the thread on manual interrupt TODO: not the best way
                monitor.stopMonitor()
                monitor.terminate()
                break
            except BTLEException as e:
                print("disconnection")
                # Update counter
                disconnCounter += 1
                # Try connection only for momentary disconnections
                if(disconnCounter < 3):
                    monitor.terminate()
                    sleep(1.0)
                    monitor = HRmonitor(address)
                    if(monitor.device != None):
                        monitor.startMonitor()
                else:
                    break
