# RemoteObservatory
[![astropy](http://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat)](http://www.astropy.org/)


Another astronomical observatory manager.
This project either uses, or is directly inspired by:

* KStars: https://github.com/KDE/kstars
* Indi: https://github.com/indilib/indi (Jasem Mutlaq + contributors)
* Starquew: https://github.com/GuLinux/StarQuew/tree/master/backend/indi (Marco Gulino)
* npindi: https://github.com/geehalel/npindi (Geehalel)
* Panoptes: https://github.com/panoptes/POCS
* Astropy: https://github.com/astropy/astropy
* Astroplan: https://github.com/astropy/astroplan (Brett Morris + contributors)
* Astrometry.net: https://github.com/dstndstn/astrometry.net (Dustin Lang + contributors)
* PHD2: https://github.com/OpenPHDGuiding/phd2/wiki/EventMonitoring
* notebooks from ivandga for amateur spectroscopy: https://github.com/ivandga/ArasSpectraNotebooks
* SpectroStars from Serge Golovanow: https://github.com/serge-golovanow/SpectroStars
* Astroalign: https://github.com/toros-astro/astroalign

# Install

## System requirements when using ubuntu
sudo apt-add-repository ppa:mutlaqja/ppa
sudo add-apt-repository ppa:pch/phd2
sudo apt-get update
sudo apt-get install libcfitsio-dev libnova-dev swig indi-full libindi-dev libindi1 kstars-bleeding libftdi-dev libgps-dev libraw-dev libgphoto2-dev libboost-dev libboost-regex-dev librtlsdr-dev libftdi1-dev libfftw3-dev libastrometry* libnova* astrometry-data-2mass-05 astrometry-data-2mass-06 astrometry-data-2mass-07 astrometry-data-4208-4219 xplanet extra-cmake-modules kdelibs5-dev libkf5declarative-dev libkf5globalaccel-dev libkf5configwidgets-dev libkf5xmlgui-dev libkf5windowsystem-dev kdoctools-dev libkf5notifications-dev libkf5kdelibs4support5-bin libkf5newstuff-dev libkf5crash-dev libkf5plotting-dev libkf5notifyconfig-dev libraw-dev wcslib-dev libqt5svg5-dev libqt5websockets5-dev qttools5-dev-tools libftdi1-dev libgps-dev libjpeg9-dev gpsd  libtheora-dev phd2 libcurl4-openssl-dev wx-common libusb-1.0-0-dev libgsl-dev libogg-dev libtheora-dev -y

## Python requirements
pip install requests pyindi-client requests-cache watchdog astropy ntplib astroplan matplotlib tzwhere astroquery pymongo rawpy serial pyserial socket astroalign
If you want to run the astrometry server locally, use:
pip install django Pillow

## Arduino stuff
If you are interested in compiling/using the arduino stuff here, please download the official Arduino IDE, and define the following environment variable: $ARDUINO_SDK_PATH

## Building 3D support for virtual telescope
pip install PyQt5 PyQt3D pyqtgraph


# How to launch the full stuff

## If you want to try the software with simulators:
./apps/launch_indi_simu.sh
PYTHONPATH=. python ./apps/launch_remote_observatory.py

## If, in addition you want the nice dashboard (might require additional dependencies, scripts are untested)
./apps/launch_PAWS.sh
PYTHONPATH=. python ./apps/launch_qt_dashboard.py
PYTHONPATH=. python3 ./apps/launch_weather_capture.py (only a stub for now)


## Legacy or optional features
### Support for DBus scripting ()
sudo apt-get install libgirepository1.0-dev gobject-introspection
pip install PyGObject
or
conda install -c conda-forge pygobject
### Support for the Dash dashboard (legacy, not used anymore):
pip install dash dash-core-components dash-html-components dash-renderer plotly
### Web service (legacy, not used anymore)
For now, RemoteObservatory uses some web service to acquire data, so ensure that you have a json file containing the key for each API in your home directory:
  * For WUG, get your key [here](https://www.wunderground.com/weather/api/) and store it in your home directory inside a .wug.json file
  * For nova (astrometry.net), get your key at [here](http://nova.astrometry.net/api_help) and store it in your home directory inside a .nova.json file
### Arduino capture
PYTHONPATH=. python3 ./apps/launch_arduino_capture.py


## TODO: WORK IN PROGRESS: DO NOT USE BEFORE THIS IS DONE (or just do)
* make sure we are correctly scoring all constraints (not only binary values) in ObservationPlanner/Scheduler
* Correct the stub inside of launch_remote_observatory that returns safe even if not safe
* re-integrate the simulator mode that returns fine, even if not fine
* Make a proper integration between our IndiMount and abstractMount inside of IndiAbstractMount, because right now it is a mess
* Setup a calibrating_flat and calibrating_dark states
* fill-in the class Calibration that mirrors the observation class and make sure  that a new calibration is issued whenever an observation has completed (This should arise in Manager ?)
* Check why the SITELONG entry in outputed file is wrong
* ObservationPlanner/Scheduler l232 you NEED to setup proper FixedTarget.from_name
* ShedObservatory l76: uncomment the raise ScopeControllerError(msg)
* Gast is important: Service/NTPTimeService.py l 137
* Urgent: fix the hardcoded values in solve-field scripting
* Urgent fix the max_pointing_error in pointing. Current one might be too low
* L292 in StateMachine, find a better way to signal the issue when transitionning
* Remove temporary fix in Scheduler:             target = FixedTarget(SkyCoord(ra=1*u.deg, dec=89*u.deg)
* Need to try to kill PHD2 while guiding and check that we return to parking state
* Need to simulate a PHD2 star lost and check that we return to parking state
* The loop_mode in GuiderPHD2 is ambiguous (let it like this for now)
* Check all states from the state machine, and make sure they often call model.check_messages()
* If an observation is split into multiple observing block, shouldn't they have the same id ? that would allow to skip pointing when going from one block to another
* check if we actually refocus in case the observation id is the same
* the publisher_port parameter in weather config should be refactored with messaging parameter
* PHD2 is not closed properly / two instance might be launched which cause error
* use find . -path ./venv -prune -o -name '*.py' to search stuf not in venv
* use find . -path ./venv -prune -o -name '*.py' -exec grep -H string_to_find {} \;
* use find . -path ./venv -prune -o -name '*.py' -exec sed -i -e 's/get_local_time_from_ntp/get_local_time/g' {} \; to replace stuff
