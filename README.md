# NECSTCamp - Polar backend

This is a real-time heart-beat monitoring application designed around the Polar OH1 optical heart rate sensor.
The Scanner application automatically identifies Polar sensors and start recording, while the Reader app could be used to manage single OH1 sensors directly (or for debugging purposes)

The system has been currently tested on this environment:
* Raspberry Pi 3
* Polar OH1 with firmware 1.0.9
* Python 3.5.2 and 3.6.2
* Bluepy library 1.1.2

To install bluepy directly from git:

> sudo pip install git+https://github.com/IanHarvey/bluepy.git

