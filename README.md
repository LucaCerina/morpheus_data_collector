# Morpheus project: smart ambient data collector
This repository contains the code used for the _Morpheus_ project inside the broader [NecstCamp](https://necstcamp.necst.it/) project at Politecnico di Milano in 2019.
Specifically, the project aimed to analyze people's sleep collecting information about their heart rate, with a Polar OH1 device, and the quality of the sleeping room, collecting temperature, humidity, CO2, noise and light of the bedroom.
The data from the sensor is sent to a remote InfluxDB instance via REST API and locally stored using CSV format.
The whole system runs as a Linux service to start automatically on a Raspberry-based system.
Every sensor runs on separate thread to handle errors in sampling, delayed response from collection server or else.
Each node employs a simple json file as a configuration to know the id of the room in which it was installed, and the id of the participants sleeping there. No personal data is stored on the physical devices

## Structure of the repo
* arduino_node: An initial iteration using Arduino MKR1000 to measure temperature and humidity
* raspberry_node: A linux service running on Raspberry Pi zero-W to communicate with sensors and backend
* polar_backend: BLE delegate to collect data from Polar OH1 heart rate sensors and extract some heart rate variability stats


### Sensors employed
* ADC MCP3008: analog-to-digital readout of sound noise from a mems microphone (Adafruit MEMS SPW2430) and ambient light (GA1A12S202 log-scale analog)
* Adafruit si7021 temperature&humidity sensor (I2C protocol)
* Adafruit SGP30 CO2 sensor (I2C protocol)
* Polar OH1 a heart rate sensor worn by users with data collected through BLE4.0 scanning

### Dependencies
See `requirements.txt` files in the folders.

## Acknowledgments to project contributors
Davide Bertolotti, Daniele de Vincenti, Andrea Damiani, and Rolando Brondolin during their time at NECSTLab, Politecnico di Milano
