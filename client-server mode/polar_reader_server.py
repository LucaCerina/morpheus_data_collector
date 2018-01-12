import zmq

zContext = zmq.Context()
zServer = zContext.socket(zmq.REP)
zServer.bind('tcp://*:3000')

while True:
    message = zServer.recv_string()
    print(message)
    zServer.send_string("OK")

