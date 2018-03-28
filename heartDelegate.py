import bluepy.btle as btle
from bluepy.btle import BTLEException

from time import sleep

class heartDelegate(btle.DefaultDelegate):
    """
    Bluepy delegate that handles the recognition of heartbeats
    """

    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.data = None

    def handleNotification(self, cHandle, data):
        # Heart rate handle
        #print("cHandle: {}".format(cHandle))
        self.data = data
        #if(cHandle == 37):
            # HR beats-per-minute byte
        #    self.message = self.data[1]
        #elif(cHandle == 16):
        #    self.message = parse_message(data)

    def parseBeat(self):
        """
        Extract informations from HR message
        """
        reading = {"HR":0, "RR":list()}
        hrFormat = self.data[0] & 0x01

        sensorContact = True
        contactSupported = not ((self.data[0] & 0x06) == 0)
        if contactSupported:
            sensorContact = ((self.data[0] & 0x06) >> 1) == 3

        energyExpended = (self.data[0] & 0x10) >> 3

        rrPresent = (self.data[0] & 0x10) >> 4
        hrValue = self.data[1] + (self.data[2] << 8) if hrFormat == 1 else self.data[1]
        if ( not contactSupported & hrValue == 0):
            sensorContact = False

        offset = hrFormat + 2
        energy = 0
        if energyExpended == 1:
            energy = (self.data[offset] & 0xFF) + ((self.data[offset + 1] & 0xFF) << 8)
            offset += 2
        
        rrVals = list()
        #print("rrPresent: {}".format(rrPresent))
        if rrPresent == 1:
            dataLen = len(self.data)
            #print("offset: {} dataLen {}".format(offset, dataLen))
            while offset < dataLen:
                rrValue = int((self.data[offset] & 0xFF) + ((self.data[offset +1] & 0xFF) << 8))
                offset +=2
                rrVals.append(rrValue)

        reading["HR"] = hrValue
        reading["RR"] = rrVals
        #print("{} {} {}".format(hrValue, rrVals, reading)) TODO check why it returns a int sometimes
        return reading

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
            #self.CCC_descriptor.write(b"\x00\x00", withResponse=False)
            #sleep(0.05)
            self.CCC_descriptor.write(b"\x01\x00", withResponse=True)
            sleep(0.05)
            #print("CCC value: " + str(self.CCC_descriptor.read()))
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
            print(e)
            return {'HR':0, 'RR':[]}

        return self.device.delegate.parseBeat()
