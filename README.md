# RemoteObservatory
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
* spectroDB: https://github.com/tlemoult/spectroDb (Thierry Lemoult + contributors)

## Install
sudo apt-add-repository ppa:mutlaqja/ppa
sudo apt-get update
sudo apt-get install libcfitsio-dev libnova-dev swig indi-full libindi-dev libindi1 kstars-bleeding libftdi-dev libgps-dev libraw-dev libgphoto2-dev libboost-dev libboost-regex-dev librtlsdr-dev libftdi1-dev libfftw3-dev libastrometry* libnova* astrometry-* xplanet extra-cmake-modules kdelibs5-dev libkf5declarative-dev libkf5globalaccel-dev libkf5configwidgets-dev libkf5xmlgui-dev libkf5windowsystem-dev kdoctools-dev libkf5notifications-dev libkf5kdelibs4support5-bin libkf5newstuff-dev libkf5crash-dev libkf5plotting-dev libkf5notifyconfig-dev libraw-dev wcslib-dev libqt5svg5-dev libqt5websockets5-dev qttools5-dev-tools libftdi1-dev libgps-dev libjpeg9-dev -y

# Python requirements
pip install requests pyindi-client requests-cache watchdog astropy ntplib astroplan matplotlib tzwhere astroquery pymongo rawpy serial pyserial



If you want to run the astrometry server locally, use:
pip install django Pillow

## Web service

For now, RemoteObservatory uses some web service to acquire data, so ensure that you have a json file containing the key for each API in your home directory:
  * For WUG, get your key [here](https://www.wunderground.com/weather/api/) and store it in your home directory inside a .wug.json file
  * For nova (astrometry.net), get your key at [here](http://nova.astrometry.net/api_help) and store it in your home directory inside a .nova.json file

## Building 3D support for virtual telescope

pip install PyQt5 PyQt3D

## Support for DBus scripting

sudo apt-get install libgirepository1.0-dev gobject-introspection
pip install PyGObject

or

conda install -c conda-forge pygobject

## Support for the Dash dashboard:

pip install dash dash-core-components dash-html-components dash-renderer plotly





## TODO: WORK IN PROGRESS: DO NOT USE BEFORE THIS IS DONE
make sure we are correctly scoring all constraints (not only binary values) in ObservationPlanner/Scheduler
Also remove the stuf in DefaultScheduler for defining the constraints
Correct the stub inside of launch_remote_observatory that returns safe even if not safe
re-integrate the simulator mode that returns fines, even if not fines
Make a proper integration between our IndiMount and abstractMount inside of IndiAbstractMount, because right now it is a mess
Setup a calibrating_flat and calibrating_dark states
fill-in the class Calibration that mirrors the observation class and make sure
that a new calibration is issued whenever an observation has completed (This should arise in Manager ?)
CRITICAL: check what happens when no indi server is running, there are unhandled exception there
