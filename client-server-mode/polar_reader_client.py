import os
import sys
sys.path.append(os.getcwd()+'/../')
import uuid
from time import sleep, time

import bluepy.btle as btle
import udatetime  # RFC3339 required by influxDB
import zmq
from bluepy.btle import BTLEException
from tendo import singleton

from heartDelegate import heartDelegate, HRmonitor

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
        monitor.startMonitor()

        # Initialize sampleTime
        sampleTimeOld = time() 
        # Reader continuous loop
        while(True):
            try:
                reading = monitor.getHeartRate()
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
                    monitor = HRmonitor(devName, address)
                    if(monitor.device != None):
                        monitor.startMonitor()
                    else:
                        sleep(0.1)
                else:
                    # monitor.terminate()
                    break

        # Close file
        zSocket.close()
