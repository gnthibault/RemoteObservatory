from gi.repository import GObject
from gi.repository import GLib
import os
import time

# Create a session bus.
from pydbus import SessionBus
bus = SessionBus()

# First create proxy object for connecting devices to ekos
ekos_indi = bus.get("org.kde.kstars", "/KStars/INDI")

myDevices = [ "indi_simulator_telescope", "indi_simulator_ccd",
              "indi_simulator_wheel", "indi_simulator_focus" ]

## Start INDI devices
#ekos_indi.start("7624", myDevices)

#print("Waiting for INDI devices...")

## Create array for received devices
#devices = []

#while True:
#    devices = ekos_indi.getDevices()
#    if (len(devices) < len(myDevices)):
#        time.sleep(1)
#    else:
#        break;

#print("We received the following devices:")
#for device in devices:
#    print(device)

#print("Establishing connection to Telescope and CCD...")

## Set connect switch to ON to connect the devices
#ekos_indi.set_switch("Telescope Simulator", "CONNECTION", "CONNECT", "On")
## Send the switch to INDI server so that it gets processed by the driver
#ekos_indi.sendProperty("Telescope Simulator", "CONNECTION")
## Same thing for CCD Simulator
#ekos_indi.set_switch("CCD Simulator", "CONNECTION", "CONNECT", "On")
#ekos_indi.sendProperty("CCD Simulator", "CONNECTION")
## Same thing for FW
#ekos_indi.set_switch("Filter Simulator", "CONNECTION", "CONNECT", "On")
#ekos_indi.sendProperty("Filter Simulator", "CONNECTION")
## Same thing for Focuser
#ekos_indi.set_switch("Focuser Simulator", "CONNECTION", "CONNECT", "On")
#ekos_indi.sendProperty("Focuser Simulator", "CONNECTION")
#telescopeState = "Busy"
#ccdState       = "Busy"
## Wait until devices are connected
#while True:
#    telescopeState = ekos_indi.getPropertyState("Telescope Simulator", "CONNECTION")
#    ccdState       = ekos_indi.getPropertyState("CCD Simulator", "CONNECTION")
#    if (telescopeState != "Ok" or ccdState != "Ok"):
#        time.sleep(1)
#    else:
##        break
#print("Connected to Telescope and CCD is established.")


# Start ekos
ekos = bus.get("org.kde.kstars","/KStars/Ekos")
ekos.connectDevices()
#ekos.setProfile('RemoteTesting')
ekos.start()
time.sleep(5)
print("Now ekos is supposed to be started")
#ekos_manager = bus.get("org.kde.kstars","/KStars/EkosManager")
#Q_SCRIPTABLE bool   EkosManager::start ()
#ekos_manager.start()
#print("Now ekos manager is supposed to be started")

# Create an object that will proxy for a particular remote object.
autofocuser = bus.get("org.kde.kstars","/KStars/Ekos/Focus")
#Ekos::Focus::setAutoFocusParameters (int boxSize, int stepSize, int maxTravel, double tolerance in %)
autofocuser.setAutoFocusParameters(256, 100, 50000, 2)
print("Autofocuser setting autoFocus parameters, boxSize: {}, stepSize: {}, "
      "maxTravel: {}, tolerance: {}%".format(256,100,50000,1))
#Q_SCRIPTABLE Q_NOREPLY void Ekos::Focus::setAutoStarEnabled (bool enable)
autofocuser.setAutoStarEnabled(True)
print("Autofocuser enabling auto star")
#Q_SCRIPTABLE Q_NOREPLY void Ekos::Focus::setAutoSubFrameEnabled (bool enable)
autofocuser.setAutoSubFrameEnabled(True)
print("Autofocuser enabling autosubframe")
#Q_SCRIPTABLE bool Ekos::Focus::setCCD (const QString &device)
status = autofocuser.setCCD("CCD Simulator")
print("Autofocuser setting CCD: {}, status: {}".format("CCD Simulator", status))
#Q_SCRIPTABLE bool Ekos::Focus::setFocuser (const QString &device)
status = autofocuser.setFocuser("Focuser Simulator")
print("Autofocuser setting Focuser: {}, status: {}".format("Focuser Simulator", status))
#Q_SCRIPTABLE Q_NOREPLY void Ekos::Focus::setExposure (double value in seconds)
autofocuser.setExposure(1)
print("Autofocuser setting exposure: {}".format("1"))
#Q_SCRIPTABLE Q_NOREPLY void   Ekos::Focus::start ()
autofocuser.start()

for i in range(20):
    print('Autofocuser status is {} and current HFR: {}'.format(
        autofocuser.getStatus(), autofocuser.getHFR()))
    time.sleep(1)



#Q_SCRIPTABLE bool  EkosManager::stop ()
#ekos_manager.stop()
#ekos.stop()
