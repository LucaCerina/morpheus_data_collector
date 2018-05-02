import os
import sys
import uuid
from time import sleep, time

import bluepy.btle as btle
import udatetime
from bluepy.btle import BTLEException
from tendo import singleton

from heartDelegate import heartDelegate, HRmonitor

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
            filePointer = open(filename, 'a+', 0)
            filePosition = filePointer.tell() - 20
            if filePosition > 0:
                filePointer.seek(filePosition #TODO: improve the hardcoded value
                lastLine = filePointer.read()
                try:
                    readIdx = int(lastLine.split("\t")[-1].split("\n")[0]) + 1
                except ValueError:
                    # Catch exception when only headers are available on the file
                    readIdx = 0
            else:
                filePointer.write('TIME\tHR\tRR\tWID\n')
                readIdx = 0
        else:
            filePointer = open(filename, 'w', 0)
            filePointer.write('TIME\tHR\tRR\tWID\n')

        monitorStarted = monitor.startMonitor()

        # Initialize sampleTime
        sampleTimeOld = time() 
        # Reader continuous loop
        while(True and monitorStarted):
            try:
                reading = monitor.getHeartRate()
                sampleTimeNew = time()
                #sleep(0.1)
                if(reading["HR"] != 0):
                    # Limit HR to 222bpm and/or avoid false readings
                    if(sampleTimeNew - sampleTimeOld > 0.27):
                        sampleTimeOld = sampleTimeNew
                        #timeString = rfc3339.format(sampleTimeNew) #TODO find RFC3339 library with 
                        timeString = udatetime.to_string(udatetime.fromtimestamp(sampleTimeNew))
                        if reading["RR"]:
                            for i in range(len(reading["RR"])):  
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
                    #monitor = HRmonitor(devName, address)
                    if(monitor.device != None):
                        monitorStarted = monitor.startMonitor()
                    else:
                        sleep(0.1)
                else:
                    print("Max Disconnection")
                    #monitor.terminate()
                    break

        # Close file
        filePointer.close()
