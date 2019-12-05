from Observatory import ArduiScopeController 
import logging
from time import sleep

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s') 
a = ArduiScopeController.ArduiScopeController()       
a.initialize()
do = True
sleep(1)
while do:
    do = False
    #a.send_order(pin=13,value=0)
    a._pub.send_message('scope_controller:commands', {"command": "write_line", "line": "13 0"})
"""

import zmq
import random
import sys
import time
port = "6501"
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:{}".format(port))
do = True
while do:
    #do = False
    topic = "scope_controller:commands"
    messagedata = '{"command":"write_line","line":"13 0"}' #marche
    messagedata = '{"command": "write_line", "line": "13 0"}' #marche aussi
    print("{} {}".format(topic, messagedata))
    #socket.send_string("{} {}".format(topic, messagedata))
    socket.send_string('scope_controller:commands {"command": "write_line", "line": "13 1"}', flags=zmq.NOBLOCK)
    #socket.send_string('scope_controller {"name":"scope_controller","timestamp":"2019-02-12T07:10:09GMT","data":{"name":"scope_controller","uptime":"97s","num":"98"}}')
    #socket.send(("%d %d" % (5555, 6666)).encode())
    time.sleep(1)
"""
