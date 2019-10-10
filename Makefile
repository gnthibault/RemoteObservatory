#########################################################
#
#  setup environment for remote obervatory
#
#########################################################

# Produce verbose output by default.
VERBOSE = 1

# Default target executed when no arguments are given to make.
default_target: all

.PHONY: default_target

all: remote_observatory

packages:
	echo "Installing system packages requirements ..."
	sudo apt-add-repository ppa:mutlaqja/ppa
	sudo add-apt-repository ppa:pch/phd2
	sudo apt-get update
	sudo apt-get install -y libcfitsio-dev libnova-dev swig indi-full libindi-dev libindi1 kstars-bleeding libftdi-dev libgps-dev libraw-dev libgphoto2-dev libboost-dev libboost-regex-dev librtlsdr-dev libftdi1-dev libfftw3-dev libastrometry* libnova* astrometry-* xplanet extra-cmake-modules kdelibs5-dev libkf5declarative-dev libkf5globalaccel-dev libkf5configwidgets-dev libkf5xmlgui-dev libkf5windowsystem-dev kdoctools-dev libkf5notifications-dev libkf5kdelibs4support5-bin libkf5newstuff-dev libkf5crash-dev libkf5plotting-dev libkf5notifyconfig-dev libraw-dev wcslib-dev libqt5svg5-dev libqt5websockets5-dev qttools5-dev-tools libftdi1-dev libgps-dev libjpeg9-dev gpsd  libtheora-dev phd2

venv: requirements.txt packages
	echo "Installing python requirements ..."
	test -d venv || virtualenv venv
	. venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt

remote_observatory: venv
	echo "Installing remote_observatory in venv ..."
	#python setup.py install

clean:
	rm -rf venv


