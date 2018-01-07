# RemoteObservatory
Another astronomical observatory manager

## Install
sudo apt-add-repository ppa:mutlaqja/ppa
sudo apt-get update
sudo apt-get install libcfitsio-dev libnova-dev swig indi-full kstars-bleeding libftdi-dev libgps-dev libraw-dev libgphoto2-dev libboost-dev libboost-regex-dev librtlsdr-dev libftdi1-dev libfftw3-dev libastrometry* libnova* astrometry-* -y
pip install requests pyindi-client requests-cache watchdog astropy ntplib

If you want to run the astrometry server locally, use:
sudo apt-get install python-django-auth-openid python-django-south python-simplejson
pip install Pillow

## Web service

For now, RemoteObservatory only uses WUG, so, ensure that you have a json file containing your wug key in your home directory inside a .wug.json file


