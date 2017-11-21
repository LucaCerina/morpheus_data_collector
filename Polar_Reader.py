import bluepy.btle as btle
from bluepy.btle import BTLEException
import sys
import uuid
from time import sleep
from tendo import singleton
import os

class heartDelegate(btle.DefaultDelegate):
	message = 0

	def __init__(self):
		btle.DefaultDelegate.__init__(self)

	def handleNotification(self, cHandle, data):
		#print(str(data) + " " + str(cHandle))
		if(cHandle == 37): # Heart Rate handle
			self.message = data[1]

	def getLastBeat(self):
		return self.message

class HRmonitor():
	CCC_descriptor_uuid = "00002902-0000-1000-8000-00805f9b34fb"
	heartRate_service_uuid = "0000180d-0000-1000-8000-00805f9b34fb"
	heartRate_measure_uuid = "00002a37-0000-1000-8000-00805f9b34fb"
	battery_service_uuid = "0000180f-0000-1000-8000-00805f9b34fb"

	def __init__(self, address):
		self.address = address
		try:
			self.device = btle.Peripheral(self.address)
			self.device.setDelegate(heartDelegate())
			print("Connected to: " + self.address)
		
			# Read descriptors
			self.heartrate_service = self.device.getServiceByUUID(self.heartRate_service_uuid)
			self.CCC_descriptor = self.heartrate_service.getDescriptors(forUUID = self.CCC_descriptor_uuid)[0]
		except BTLEException as e:
			self.device = None

	def startMonitor(self):
		try:
			print("Writing CCC...")
			self.CCC_descriptor.write(b"\x01\x00", withResponse=False)
			sleep(1.0)
			print("CCC value: " + str(self.CCC_descriptor.read()))
		except Exception as e:
			print(e)
			#self.device.disconnect()

	def stopMonitor(self):
		self.CCC_descriptor.write(b"\x00\x00", withResponse=False)

	def terminate(self):
		try:
			self.device.disconnect()
		except Exception as e:
			print(e)

	def getHeartRate(self):
		try:
			self.device.waitForNotifications(1.0)
			return self.device.delegate.getLastBeat()
		except Exception as e:
			return 0
			print(e)

def heartRateThread(address):
	# Disconnections counter
	disconnCounter = 0
	# Initialize Heart Rate monitor
	monitor = HRmonitor(address)
	if(monitor.device != None):
		monitor.startMonitor()

		# Reading continuous loop
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
				monitor.stopMonitor()
				monitor.terminate()
				break
			except BTLEException as e:
				print("disconn")
				disconnCounter += 1
				if(disconnCounter < 3):
					monitor.terminate()
					sleep(1.0)
					monitor = HRmonitor(address)
					if(monitor.device != None):
						monitor.startMonitor()
				else:
					break

#heartRateThread("A0:9E:1A:17:74:55")