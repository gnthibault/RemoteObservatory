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
	sudo add-apt-repository -y ppa:mutlaqja/ppa
	sudo add-apt-repository -y ppa:pch/phd2
	sudo apt-get update
	sudo apt-get install -y\
            astrometry.net\
            astrometry-data-4208-4219\
            extra-cmake-modules\
            indi-full\
            gpsd\
            kdelibs5-dev\
            kdoctools-dev\
            kstars-bleeding\
            libastrometry*\
            libboost-dev\
            libboost-regex-dev\
            libcfitsio-dev\
            libfftw3-dev\
            libftdi-dev\
            libftdi1-dev\
            libgps-dev\
            libgphoto2-dev\
            libindi-dev\
            libindi1\
            libkf5declarative-dev\
            libkf5globalaccel-dev\
            libkf5configwidgets-dev\
            libkf5xmlgui-dev\
            libkf5windowsystem-dev\
            libkf5notifications-dev\
            libkf5kdelibs4support5-bin\
            libkf5newstuff-dev\
            libkf5crash-dev\
            libkf5plotting-dev\
            libkf5notifyconfig-dev\
            libnova*\
            libqt5svg5-dev\
            libqt5websockets5-dev\
            libraw-dev\
            librtlsdr-dev\
            libtheora-dev\
            phd2\
            qttools5-dev-tools\
            swig\
            wcslib-dev\
            xplanet
#            libjpeg9-dev\

venv: requirements.txt packages
	echo "Installing python requirements ..."
	test -d venv || virtualenv venv
	. venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt

remote_observatory: venv
	echo "Installing remote_observatory in venv ..."
	#python setup.py install

docs: venv
	cd docs
	make html
	cd -


clean:
	rm -rf venv


