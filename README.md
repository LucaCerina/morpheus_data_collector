# NECSTCamp - Polar backend

This is a real-time heart-beat monitoring application designed around the Polar OH1 optical heart rate sensor.
The Scanner application automatically identifies Polar sensors and start recording, while the Reader app could be used to manage single OH1 sensors directly (or for debugging purposes)

The system has been currently tested on this environment:

* Raspberry Pi 3
* Polar OH1 with firmware 1.0.9
* Python 3.5.2 and 3.6.2
* Bluepy library 1.1.2

The system is designed to work with Python > 3, Python 2 will not be supported.

The Reader Client and Server employ the ZeroMQ library, tested on:

* ZeroMQ 4.2.0
* PyZMQ 16.0.3

The Reader Client and Server requires RFC3339 library.

Other dependencies:

* InfluxDB for time-series backup

To install bluepy directly from git:

> sudo pip install git+https://github.com/IanHarvey/bluepy.git

To execute the code without sudo, some permissions must be set to bluepy:

> sudo apt-get install libcap2-bin

> sudo setcap 'cap_net_raw,cap_net_admin+eip' $PATH_TO_HCITOOL

> sudo setcap 'cap_net_raw,cap_net_admin+eip' $PATH_TO_PYTHON

> sudo setcap 'cap_net_raw,cap_net_admin+eip' $PATH_TO_BLUEPY_HELPER

