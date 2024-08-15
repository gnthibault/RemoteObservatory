ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}

# prevent keyboard related user input to be asked for
ENV DEBIAN_FRONTEND noninteractive

# Useless docker cache for pip
ENV PIP_NO_CACHE_DIR 1

# Versioning
ENV INDI_VERSION v2.0.8
ENV PYINDI_VERSION v1.9.1
ENV INDI_3RD_PARTY_VERSION v2.0.8
ENV PYTHON_VERSION 3.12.3

# Generic install / utilities / dev
RUN apt-get update && apt-get --assume-yes --quiet install --no-install-recommends \
    build-essential \
    cmake \
    gettext \
    git \
    libgraphviz-dev \
    libz3-dev \
    python3 \
    python3-dev \
    python3-numpy-dev \
    python3-pip \
    python3-setuptools \
    python3-six \
    software-properties-common \
    vim && \
    apt-get clean

# pyenv dependencies
RUN apt-get --assume-yes --quiet install --no-install-recommends \
    build-essential \
    curl \
    libbz2-dev \
    libffi-dev \
    liblzma-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    llvm \
    make \
    python3-openssl \
    tk-dev \
    wget \
    xz-utils \
    zlib1g-dev

## Install astrometry.net packages
# Check cat /usr/local/astrometry/etc/astrometry.cfg to make sure destination path is correct
# 4100-series built from the Tycho-2 catalog; scales 7-19 available, good for images wider than 1 degree. Recommended.
# Mean satellite observation epoch      ~J1991.5
# Epoch of the Tycho-2 catalog           J2000.0
# Reference system                       ICRS
# see https://heasarc.gsfc.nasa.gov/W3Browse/all/tycho2.html

# 5200-series, LIGHT version built from Tycho-2 + Gaia-DR2; scales 0-6 available, good for images narrower than 1 degree. Combine with 4100-series for broader scale coverage.
# The LIGHT version contains smaller files with no additional Gaia-DR2 information tagged along. Recommended.
# Gaia DR2 astrometry consistently uses the ICRS reference system and provides stellar coordinates valid for epoch J2015.5
# see https://www.cosmos.esa.int/web/cheops-guest-observers-programme/coordinates
RUN apt-get --assume-yes --quiet install --no-install-recommends libcairo2-dev libnetpbm11-dev \
  && mkdir -p $HOME/projects/astrometry.net \
  && cd $HOME/projects/astrometry.net \
  && wget https://astrometry.net/downloads/astrometry.net-0.95.tar.gz \
  && tar -xvf ./*.tar.gz \
  && cd astrometry.net-0.95 \
  && export NETPBM_LIB="-L/usr/lib -lnetpbm" \
  && export NETPBM_INC="-I/usr/include" \
  && ./configure --prefix=/usr \
  && make reconfig \
  && make all -j8 \
  && make install \
  && ln -s /usr/local/astrometry/bin/an-fitstopnm /usr/local/bin/an-fitstopnm \
  && wget --recursive --no-parent --continue --directory-prefix=/usr/local/astrometry/data/ https://portal.nersc.gov/project/cosmo/temp/dstn/index-5200/LITE/

## Indi dependencies for pre-packages binaries
#RUN apt-add-repository ppa:mutlaqja/ppa && apt-get --assume-yes --quiet install --no-install-recommends \
#    gsc \
#    libcfitsio-dev \
#    libnova-dev \
#    libindi1 \
#    indi-bin \
#    kstars-bleeding \
#    swig

# Dependencies to build indi from sources + pyindi-client that is linked with binaries through swig
# astrometry.net was built from source
RUN apt-get --assume-yes --quiet install --no-install-recommends \
        cdbs \
        dkms \
        fxload \
        libboost-regex-dev \
        libcfitsio-dev \
        libcurl4-gnutls-dev \
        libdc1394-dev \
        libev-dev \
        libfftw3-dev \
        libftdi-dev \
        libftdi1-dev \
        libgps-dev \
        libgsl0-dev \
        libjpeg-dev \
        libkrb5-dev \
        libnova-dev \
        libraw-dev \
        libtiff5-dev \
        libusb-1.0-0-dev \
        libusb-dev \
        swig

# Build indi from sources
RUN mkdir -p $HOME/projects \
    && cd $HOME/projects \
    && git clone https://github.com/indilib/indi.git \
    && cd $HOME/projects/indi \
    && git checkout $INDI_VERSION \
    && cd $HOME/projects \
    && mkdir -p build/indi \
    && cd build/indi \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr  $HOME/projects/indi \
    && make -j8 \
    && make install

# Dependencies to build indi-3rd party from sources
RUN apt-get --assume-yes --quiet install --no-install-recommends \
    libnova-dev \
    libcfitsio-dev \
    libusb-1.0-0-dev \
    zlib1g-dev \
    libgsl-dev \
    libjpeg-dev \
    libcurl4-gnutls-dev \
    libtiff-dev \
    libftdi-dev \
    libraw-dev \
    libdc1394-dev \
    libgphoto2-dev \
    libboost-dev \
    libboost-regex-dev \
    librtlsdr-dev \
    liblimesuite-dev \
    libftdi1-dev \
    libgps-dev \
    libavcodec-dev \
    libavdevice-dev \
    libzmq3-dev

# Additional dependencies with indi-3rd party - clone the whole thing
RUN mkdir -p $HOME/projects \
    && cd $HOME/projects \
    && git clone https://github.com/indilib/indi-3rdparty.git \
    && cd $HOME/projects/indi-3rdparty \
    && git checkout $INDI_3RD_PARTY_VERSION

RUN for i in indi-duino libasi indi-asi libplayerone indi-playerone indi-shelyak libaltaircam; \
    do cd $HOME/projects \
    && mkdir -p $HOME/projects/build/$i \
    && cd $HOME/projects/build/$i \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr  $HOME/projects/indi-3rdparty/$i \
    && make -j8 \
    && make install; \
    done

## OpenPhd2 might later be replaced by the original source ?
#RUN add-apt-repository ppa:pch/phd2 && apt-get --assume-yes --quiet install --no-install-recommends \
#    phd2
# Dependencies to build phd2 from sources
RUN apt-get --assume-yes --quiet install --no-install-recommends \
    libwxgtk3.2-dev

RUN mkdir -p $HOME/projects \
    && cd $HOME/projects \
    && git clone https://github.com/gnthibault/phd2.git \
    && mkdir -p build/phd2 \
    && cd build/phd2 \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr  $HOME/projects/phd2 \
    && make -j8 \
    && make install

RUN cp /opt/remote_observatory/infrastructure/phd2.service /etc/systemd/system/
RUN chmod 644 /etc/systemd/system/phd2.service

## Dependencies for nice reporting / latex reports
RUN apt-get --assume-yes --quiet install --no-install-recommends \
    texlive-latex-recommended \
    texlive-publishers \
    texlive-bibtex-extra \
    texlive-science

# Using bash for lower level scripting from now-on
SHELL ["/bin/bash", "-l", "-c"]
RUN echo 'export PS1="\u@\h \w> "' | cat - /root/.profile > temp && mv temp /root/.profile

# Actual application code and configs
RUN mkdir -p /opt/remote_observatory
ADD code.tar.gz /opt/remote_observatory

# Python environment
RUN curl https://pyenv.run | bash
RUN echo 'export PYENV_ROOT=/root/.pyenv' >> /root/.bashrc
RUN echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> /root/.bashrc
RUN echo 'eval "$(pyenv init -)"' >> /root/.bashrc
RUN pyenv install -v $PYTHON_VERSION
RUN pyenv global $PYTHON_VERSION

# Python virtual environment
ENV VIRTUAL_ENV=/opt/remote_observatory_venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN echo 'source /opt/remote_observatory_venv/bin/activate' >> /root/.bashrc

# Python packages
#COPY requirements.txt .
RUN pip install -r /opt/remote_observatory/requirements.txt

# Build and install pyindi-client
RUN mkdir -p $HOME/projects \
    && cd $HOME/projects \
    && git clone https://github.com/indilib/pyindi-client.git \
    && cd $HOME/projects/pyindi-client \
    && git checkout $PYINDI_VERSION \
    && pip install -e .


# Indi webmanager for dev
RUN pip install indiweb==0.1.8
RUN cp /opt/remote_observatory/infrastructure/indiwebmanager*.service /etc/systemd/system/
RUN chmod 644 /etc/systemd/system/indiwebmanager.service
RUN chmod 644 /etc/systemd/system/indiwebmanager_guiding_camera.service
RUN chmod 644 /etc/systemd/system/indiwebmanager_pointing_camera.service
RUN chmod 644 /etc/systemd/system/indiwebmanager_science_camera.service

#RUN systemctl daemon-reload
#RUN systemctl enable indiwebmanager.service


# # Add Docker's official GPG key:
# sudo apt-get update
# sudo apt-get install ca-certificates curl
# sudo install -m 0755 -d /etc/apt/keyrings
# sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
# sudo chmod a+r /etc/apt/keyrings/docker.asc

# # Add the repository to Apt sources:
# echo \
#   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
#   $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
#   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
# sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Build with
# ./build_images.sh latest linux/amd64
# launch with
# docker run --user $(id -u):$(id -g) -it --rm -v /main/machine/volume:/docker/mount/point --net host gnthibault/remote_observatory:latest
