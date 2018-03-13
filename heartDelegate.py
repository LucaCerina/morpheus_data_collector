import bluepy.btle as btle

class heartDelegate(btle.DefaultDelegate):
    """
    Bluepy delegate that handles the recognition of heartbeats
    """

    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        # Heart rate handle
        #print("cHandle: {}".format(cHandle))
        self.data = data
        #if(cHandle == 37):
            # HR beats-per-minute byte
        #    self.message = data[1]
        #elif(cHandle == 16):
        #    self.message = parse_message(data)

    def getLastBeat(self):
        """
        Access the delegate message
        """
        return self.parse_message(self.data)

    def parse_message(self, data):
        """
        Extract informations from HR message
        """
        reading = {"HR":None, "RR":list()}
        hrFormat = data[0] & 0x01

        sensorContact = True
        contactSupported = not ((data[0] & 0x06) == 0)
        if contactSupported:
            sensorContact = ((data[0] & 0x06) >> 1) == 3

        energyExpended = (data[0] & 0x10) >> 3

        rrPresent = (data[0] & 0x10) >> 4
        hrValue = data[1] + (data[2] << 8) if hrFormat == 1 else data[1]
        if ( not contactSupported & hrValue == 0):
            sensorContact = False

        offset = hrFormat + 2
        energy = 0
        if energyExpended == 1:
            energy = (data[offset] & 0xFF) + ((data[offset + 1] & 0xFF) << 8)
            offset += 2
        
        rrVals = list()
        #print("rrPresent: {}".format(rrPresent))
        if rrPresent == 1:
            dataLen = len(data)
            #print("offset: {} dataLen {}".format(offset, dataLen))
            while offset < dataLen:
                rrValue = int((data[offset] & 0xFF) + ((data[offset +1] & 0xFF) << 8))
                offset +=2
                rrVals.append(rrValue)

        reading["HR"] = hrValue
        reading["RR"] = rrVals
        #print("{} {} {}".format(hrValue, rrVals, reading)) TODO check why it returns a int sometimes
        return reading