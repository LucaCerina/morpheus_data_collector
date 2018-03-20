import os
import sys
import uuid
from time import sleep, time

import bluepy.btle as btle
import udatetime
from bluepy.btle import BTLEException
from tendo import singleton

from heartDelegate import heartDelegate


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

    def __init__(self, devName, address):
        self.devName = devName
        self.address = address
        try:
            # Connect to the device
            #print("test connection")
            #print("isinstance: {}".format(isinstance(self.address, ScanEntry))
            if devName[6:9] == "OH1":
                self.device = btle.Peripheral(self.address)
            else: #H10
                self.device = btle.Peripheral(self.address, addrType="random")
            self.device.setDelegate(heartDelegate())
            print("Connected to: " + self.devName)
        
            # Read descriptors
            self.heartrate_service = self.device.getServiceByUUID(self.heartRate_service_uuid)
            #print(self.heartrate_service.uuid)
            self.CCC_descriptor = self.heartrate_service.getDescriptors(forUUID = self.CCC_descriptor_uuid)[0]
            #print(self.CCC_descriptor.uuid)        
        except BTLEException as e:
            # Return None if connection fails
            print("Failed to connect to: " + self.devName)
            self.device = None

    def startMonitor(self):
        """
        This method starts the Polar monitor by writing the CCC descriptor
        """
        try:
            print("Writing CCC...")
            self.CCC_descriptor.write(b"\x00\x00", withResponse=False)
            sleep(0.05)
            self.CCC_descriptor.write(b"\x01\x00", withResponse=False)
            sleep(0.05)
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
            self.device.waitForNotifications(2.0)
        except Exception as e:
            return {'HR':0, 'RR':[]}
            print(e)
        return self.device.delegate.getLastBeat()

def heartRateThread(devName, address):
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

    # Initialize Heart Rate monitor
    monitor = HRmonitor(devName, address)
    # Activate the monitor only on correct connection
    if(monitor.device != None):
        # Open a reading file
        deviceName = devName.split(' ')[2]
        filename = deviceName +'.csv'
        if(os.path.isfile('./'+filename)):
            filePointer = open(filename, 'a+')
            filePointer.seek(filePointer.tell() - 20) #TODO: improve the hardcoded value
            lastLine = filePointer.read()
            try:
                readIdx = int(lastLine.split("\t")[-1].split("\n")[0]) + 1
            except ValueError:
                # Catch exception when only headers are available on the file
                readIdx = 0
        else:
            filePointer = open(filename, 'w')
            filePointer.write('TIME\tHR\tRR\tWID\n')

        monitor.startMonitor()

        # Initialize sampleTime
        sampleTimeOld = time() 
        # Reader continuous loop
        while(True):
            try:
                reading = monitor.getHeartRate()
                sampleTimeNew = time()
                sleep(0.1)
                if(reading["HR"] != 0):
                    # Limit HR to 222bpm and/or avoid false readings
                    if(sampleTimeNew - sampleTimeOld > 0.27):
                        sampleTimeOld = sampleTimeNew
                        #timeString = rfc3339.format(sampleTimeNew) #TODO find RFC3339 library with 
                        timeString = udatetime.to_string(udatetime.fromtimestamp(sampleTimeNew))
                        if reading["RR"]:
                            for i in range(len(reading["RR"])):
                                print(reading["RR"][i])   
                                output = "{}\t{}\t{}\t{}\n".format(timeString, reading["HR"], reading["RR"][i], readIdx)
                                filePointer.write(output)
                                print("{}\t{}".format(deviceName, output, end='', flush=True))
                        else:
                                output = "{}\t{}\t{}\t{}\n".format(timeString, reading["HR"], 0, readIdx)
                                filePointer.write(output)
                                print("{}\t{}".format(deviceName, output, end='', flush=True))                          
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
                print("disconnection of: " + deviceName)
                # Update counter
                disconnCounter += 1
                # Try connection only for momentary disconnections
                if(disconnCounter < 3):
                    # monitor.terminate()
                    sleep(0.1)
                    monitor = HRmonitor(devName, address)
                    if(monitor.device != None):
                        monitor.startMonitor()
                else:
                    print("Max Disconnection")
                    #monitor.terminate()
                    break

        # Close file
        filePointer.close()
