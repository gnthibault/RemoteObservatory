# Basic stuff
import logging
import random
import threading
import time

#PyIndi
import PyIndi
# local includes
from helper.IndiClient import IndiClient
from Service.NTPTimeService import HostTimeService

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s;%(levelname)s:%(message)s')

def test_indiClient():
    config = dict(
        indi_host="localhost",
        indi_port="7624"
    )

    cli = IndiClient(config=config)
    cli.connect_to_server()
    device_name = "CCD Simulator"
    camera = None
    while not camera:
        camera = cli.getDevice(deviceName=device_name)
        time.sleep(0.1)
    cli.connectDevice(deviceName=device_name)
    cpv = camera.getSwitch("CONNECTION")
    choices = [s.getName() for s in cpv]

    def worker():
        on_switch = random.choice(choices)
        for index, switch in enumerate(cpv):
            if switch.getName() == on_switch:
                cpv[index].setState(PyIndi.ISS_ON)
        cli.sendNewSwitch(cpv)

    tlen = 8000
    tlist = []
    for i in range(tlen):
        # Create a Thread object
        t = threading.Thread(target=worker)
        tlist.append(t)

    for t in tlist:
        # Start the thread (this begins running the function in the background)
        t.start()

    for t in tlist:
        # Wait (block) until the thread is done
        t.join()