ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}

# prevent keyboard related user input to be asked for
ENV DEBIAN_FRONTEND noninteractive
# Useless docker cache for pip
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get --assume-yes --quiet install --no-install-recommends \
      libcfitsio-dev \
      libnova-dev \
      libz3-dev \
      python3-pip \
      python3 \
      python3-dev \
      python3-numpy-dev \
      python3-six \
      software-properties-common \
      swig && \
      apt-get clean

RUN apt-add-repository ppa:mutlaqja/ppa && apt-get --assume-yes --quiet install --no-install-recommends \
      gsc \
      libindi1 \
      indi-bin \
      kstars-bleeding

RUN add-apt-repository ppa:pch/phd2 && apt-get --assume-yes --quiet install --no-install-recommends \
      phd2

#        apt-transport-https \
#        bash-completion \
#        build-essential \
#        ca-certificates \
#        curl \
#        git \
#        gnupg \
#        libfreetype6-dev \
#        openssh-client \
#        software-properties-common \
#        astrometry-data-4208-4219\
#        extra-cmake-modules\
#        gpsd\
#        indi-full\
#        kdelibs5-dev\
#        kdoctools-dev\
#        kstars-bleeding\
#        libastrometry*\
#        libboost-dev\
#        libboost-regex-dev\
#        libcfitsio-dev\
#        libcurl4-openssl-dev\
#        libfftw3-dev\
#        libftdi-dev\
#        libftdi1-dev\
#        libgphoto2-dev\
#        libgps-dev\
#        libgraphviz-dev \
#        libgsl-dev\
#        libindi-dev\
#        libindi1\
#        libjpeg-dev\
#        libnova*\
#        libogg-dev\
#        libpython3-dev\
#        libqt5svg5-dev\
#        libqt5websockets5-dev\
#        libraw-dev\
#        librtlsdr-dev\
#        libtheora-dev\
#        libtiff-dev\
#        libusb-1.0-0-dev\
#        libwxgtk3.0-dev\
#        qttools5-dev-tools\
#        swig3.0\
#        wcslib-dev\
#        xplanet\
#        zlib1g-dev\
#        wget && \


# Python stuff
COPY requirements.txt .
RUN pip install -r requirements.txt

# Build with
# ./build_images.sh latest linux/amd64
# launch with
# docker run --user $(id -u):$(id -g) -it --rm -v /main/machine/volume:/docker/mount/point --net host gnthibault/remote_observatory:latest
