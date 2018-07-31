#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import GObject
from gi.repository import GLib
import os
import time

# Create a session bus.
from pydbus import SessionBus
bus = SessionBus()

# Create an object that will proxy for a particular remote object.
remote_object = bus.get("org.kde.kstars", # Connection name
                        "/KStars/INDI" # Object's path
                       )

# Introspection returns an XML document containing information
# about the methods supported by an interface.
print("Introspection data:")
print(remote_object.Introspect())

# Get INDI interface
myDevices = [ "indi_simulator_telescope", "indi_simulator_ccd" ]

# Start INDI devices
remote_object.start("7624", myDevices)

print("Waiting for INDI devices...")

# Create array for received devices
devices = []

while True:
    devices = remote_object.getDevices()
    if (len(devices) < len(myDevices)):
        time.sleep(1)
    else:
        break;

print("We received the following devices:")
for device in devices:
    print(device)

print("Establishing connection to Telescope and CCD...")

# Set connect switch to ON to connect the devices
remote_object.setSwitch("Telescope Simulator", "CONNECTION", "CONNECT", "On")
# Send the switch to INDI server so that it gets processed by the driver
remote_object.sendProperty("Telescope Simulator", "CONNECTION")
# Same thing for CCD Simulator
remote_object.setSwitch("CCD Simulator", "CONNECTION", "CONNECT", "On")
remote_object.sendProperty("CCD Simulator", "CONNECTION")

telescopeState = "Busy"
ccdState       = "Busy"

# Wait until devices are connected
while True:
    telescopeState = remote_object.getPropertyState("Telescope Simulator", "CONNECTION")
    ccdState       = remote_object.getPropertyState("CCD Simulator", "CONNECTION")
    if (telescopeState != "Ok" or ccdState != "Ok"):
        time.sleep(1)
    else:
        break

print("Connected to Telescope and CCD is established.")
print("Commanding telescope to slew to coordinates of star Caph...")

# Set Telescope RA,DEC coords in JNOW
remote_object.setNumber("Telescope Simulator", "EQUATORIAL_EOD_COORD", "RA", 0.166)
remote_object.setNumber("Telescope Simulator", "EQUATORIAL_EOD_COORD", "DEC", 59.239)
remote_object.sendProperty("Telescope Simulator", "EQUATORIAL_EOD_COORD")

# Wait until slew is done
telescopeState = "Busy"
while True:
    telescopeState = remote_object.getPropertyState("Telescope Simulator", "EQUATORIAL_EOD_COORD")
    if (telescopeState != "Ok"):
        time.sleep(1)
    else:
        break

print("Telescope slew is complete, tracking...")
print("Taking a 5 second CCD exposure...")

# Take 5 second exposure
remote_object.setNumber("CCD Simulator", "CCD_EXPOSURE", "CCD_EXPOSURE_VALUE", 5.0)
remote_object.sendProperty("CCD Simulator", "CCD_EXPOSURE")

# Wait until exposure is done
ccdState       = "Busy"
while True:
    ccdState = remote_object.getPropertyState("CCD Simulator", "CCD_EXPOSURE")
    if (ccdState != "Ok"):
        time.sleep(1)
    else:
        break

print("Exposure complete")

# Get image file name and open it in external fv tool
fileinfo = remote_object.getBLOBFile("CCD Simulator", "CCD1", "CCD1")
print("We received file: ", fileinfo[0], " with format ", fileinfo[1], " and size ", fileinfo[2])

print("Invoking fv tool to view the received FITS file...")
# run external fits viewer
command = "fv " + fileinfo[0]
os.system(command)

print("Shutting down INDI server...")
# Stop INDI server
remote_object.stop("7624")
