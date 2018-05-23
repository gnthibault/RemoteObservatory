# RemoteObservatory
Another astronomical observatory manager

## Install
sudo apt-add-repository ppa:mutlaqja/ppa
sudo apt-get update
sudo apt-get install libcfitsio-dev libnova-dev swig indi-full kstars-bleeding libftdi-dev libgps-dev libraw-dev libgphoto2-dev libboost-dev libboost-regex-dev librtlsdr-dev libftdi1-dev libfftw3-dev libastrometry* libnova* astrometry-* -y
pip install requests pyindi-client requests-cache watchdog astropy ntplib astroplan matplotlib tzwhere astroquery

If you want to run the astrometry server locally, use:
pip install django
pip install Pillow

## Web service

For now, RemoteObservatory uses some web service to acquire data, so ensure that you have a json file containing the key for each API in your home directory:
  * For WUG, get your key [here](https://www.wunderground.com/weather/api/) and store it in your home directory inside a .wug.json file
  * For nova (astrometry.net), get your key at [here](http://nova.astrometry.net/api_help) and store it in your home directory inside a .nova.json file

## Building 3D support for virtual telescope

We use anaconda 3 distribution, and the following conda environment:
https://github.com/FreeCAD/FreeCAD_Conda

~/.condarc:
channels:
  - freecad
  - cad
  - conda-forge
  - defaults


conda create -n freecad freecad pivy=0.6.4b2
