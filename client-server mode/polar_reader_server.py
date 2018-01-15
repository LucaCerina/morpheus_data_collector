import zmq
import json

zContext = zmq.Context()
zServer = zContext.socket(zmq.PULL)
zServer.bind('tcp://*:3000')

data = list()

while True:
    try:
        message = zServer.recv_json()
        print(message)
    except KeyboardInterrupt:
        break

with open('data.json', 'w') as outfile:
    json.dump(data, outfile)
