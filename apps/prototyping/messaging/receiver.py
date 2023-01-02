# from Observatory import ArduiScopeController
# import logging
# logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')
# a = ArduiScopeController.ArduiScopeController()
# a.initialize()
# mtype, mmsg = a._sub.receive_message(blocking=True)
# print("{} : {}".format(mtype, mmsg))

import sys
import zmq

port = "6511"
    
# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)

socket.connect("tcp://localhost:{}".format(port))

socket.setsockopt_string(zmq.SUBSCRIBE, "STATUS") #"scope_controller"
#socket.setsockopt(zmq.SUBSCRIBE, "5555".encode())

# Process 5000 updates
for update_nbr in range (50000):
    string = socket.recv()
    print(string)
    #topic, messagedata = string.split()
    #print(f"received {topic} - {messagedata}")
