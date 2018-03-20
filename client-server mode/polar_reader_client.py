import os
import sys
import uuid
from time import sleep, time

import bluepy.btle as btle
import udatetime  # RFC3339 required by influxDB
import zmq
from bluepy.btle import BTLEException
from tendo import singleton

from heartDelegate import heartDelegate

sys.path.append('../')

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
    zSocket.connect('tcp://'+SrvAddr+':3000') # TODO do not hardcode IP and port
    deviceID = devName.split(' ')[2]

    # Initialize Heart Rate monitor
    monitor = HRmonitor(devName, address)
    # Activate the monitor only on correct connection
    if(monitor.device != None):
        # Start the monitor
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
                        timeString = udatetime.to_string(udatetime.fromtimestamp(sampleTimeNew))
                        # output = str(time()) + '\t' + str(beat) + '\t' + str(readIdx) + '\n'
                        # output = str(time()) + '\t' + str(beat) + '\t' + deviceID + '\n'
                        if(reading['RR']):
                            output = {'time': timeString, 'HR':reading["HR"], 'RR':reading["RR"], 'deviceID':deviceID}
                        else:
                            output = {'time': timeString, 'HR':reading["HR"], 'RR':-1, 'deviceID':deviceID}
                        # filePointer.write(output)
                        #zSocket.send_string(output)
                        zSocket.send_json(output, zmq.NOBLOCK)
                        print(output)
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
                    # monitor.terminate()
                    sleep(0.1)
                    monitor = HRmonitor(devName, address)
                    if(monitor.device != None):
                        monitor.startMonitor()
                else:
                    # monitor.terminate()
                    break

        # Close file
        zSocket.close()
