import sys
import zmq
import json

from influxdb import InfluxDBClient, exceptions
import requests

def transformMessage(message):
    output = dict()
    output['measurement'] = "polar_data"
    output['tags'] = {'device': message['deviceID']}
    output['time'] = message['time']
    output['fields'] = {'HR': message['HR'], 'RR': message['RR']}
    return output

# ZeroMQ server
zContext = zmq.Context()
zServer = zContext.socket(zmq.PULL)
zServer.bind('tcp://*:3000')

# InfluxDB client
fluxClient = InfluxDBClient(host='localhost', port=8086, database='HRData')

# Test InfluxDB server connection
try:
    fluxClient.request('ping', expected_response_code=204)
except requests.exceptions.ConnectionError:
    print("InfluxDB database is offline...")
    sys.exit(1)

# Check if database exists
if not any(dbName['name'] == 'HRData' for dbName in fluxClient.get_list_database()):
    fluxClient.create_database('HRData')

#data = list()
print("Listening on port 3000...")
while True:
    try:
        message = zServer.recv_json()
        hrBody = transformMessage(message)
        fluxClient.write_points([hrBody])
#        data.append(message)
    except KeyboardInterrupt:
        break

#with open('data.json', 'w') as outfile:
#    json.dump(data, outfile)
