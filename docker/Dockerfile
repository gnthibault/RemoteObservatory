ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}

# prevent keyboard related user input to be asked for
ENV DEBIAN_FRONTEND noninteractive

# Useless docker cache for pip
ENV PIP_NO_CACHE_DIR=1

# Versioning
ENV INDI_VERSION=v2.0.6
ENV PYINDI_VERSION=v1.9.1
ENV INDI_3RD_PARTY_VERSION=v2.0.6


# Generic install / utilities / dev
RUN apt-get update && apt-get --assume-yes --quiet install --no-install-recommends \
    cmake \
    git \
    libz3-dev \
    python3 \
    python3-dev \
    python3-numpy-dev \
    python3-pip \
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
RUN apt-get --assume-yes --quiet install --no-install-recommends \
        astrometry.net \
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
    && mkdir -p build/libindi \
    && cd build/libindi \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr  $HOME/projects/indi \
    && make -j8 \
    && sudo make install

## Additional dependencies with indi-3rd party \
RUN mkdir -p $HOME/projects \
    && cd $HOME/projects \
    && git clone https://github.com/indilib/indi-3rdparty.git \
    && git checkout $INDI_3RD_PARTY_VERSION

# indi-duino
RUN cd $HOME/projects \
    mkdir -p build/indi-duino \
    cd build/indi-duino \
    cmake -DCMAKE_INSTALL_PREFIX=/usr  $HOME/projects/indi-3rdparty/indi-duino \
    make -j8 \
    sudo make install

# indi-asi
RUN cd $HOME/projects \
    mkdir -p build/indi-asi \
    cd build/indi-asi \
    cmake -DCMAKE_INSTALL_PREFIX=/usr  $HOME/projects/indi-3rdparty/indi-asi \
    make -j8 \
    sudo make install

#indi-playerone
RUN cd $HOME/projects \
    mkdir -p build/indi-playerone \
    cd build/indi-playerone \
    cmake -DCMAKE_INSTALL_PREFIX=/usr  $HOME/projects/indi-3rdparty/indi-playerone \
    make -j8 \
    sudo make install

#indi-shelyak
RUN cd $HOME/projects \
    mkdir -p build/indi-shelyak \
    cd build/indi-shelyak \
    cmake -DCMAKE_INSTALL_PREFIX=/usr  $HOME/projects/indi-3rdparty/indi-shelyak \
    make -j8 \
    sudo make install

#libaltaircam
RUN cd $HOME/projects \
    mkdir -p build/libaltaircam \
    cd build/libaltaircam \
    cmake -DCMAKE_INSTALL_PREFIX=/usr  $HOME/projects/indi-3rdparty/libaltaircam \
    make -j8 \
    sudo make install


## OpenPhd2 might later be replaced by the original source ?
#RUN add-apt-repository ppa:pch/phd2 && apt-get --assume-yes --quiet install --no-install-recommends \
#    phd2
#
RUN mkdir -p $HOME/projects \
    && cd $HOME/projects \
    && git clone https://github.com/gnthibault/phd2.git \
    && mkdir -p build/phd2 \
    cd build/phd2 \
    cmake -DCMAKE_INSTALL_PREFIX=/usr  $HOME/projects/phd2 \
    make -j8 \
    sudo make install


## Dependencies for nice reporting / latex reports
#RUN apt-get --assume-yes --quiet install --no-install-recommends \
#    texlive-latex-recommended \
#    texlive-publishers \
#    texlive-bibtex-extra \
#    texlive-science

# Using bash for lower level scripting from now-on
SHELL ["/bin/bash", "-l", "-c"]
RUN echo 'export PS1="\u@\h \w> "' | cat - /root/.profile > temp && mv temp /root/.profile

# Actual application code and configs
ADD code.tar.gz /opt/remote_observatory

# Python environment
RUN curl https://pyenv.run | bash
RUN echo 'export PYENV_ROOT=/root/.pyenv' >> /root/.bashrc
RUN echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> /root/.bashrc
RUN echo 'eval "$(pyenv init -)"' >> /root/.bashrc
RUN pyenv install -v 3.11.7
RUN pyenv global 3.11.7

# Python virtual environment
ENV VIRTUAL_ENV=/opt/remote_observatory_venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN echo 'source /opt/remote_observatory_venv/bin/activate' >> /root/.bashrc

# Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Build and install pyindi-client
RUN mkdir -p $HOME/projects \
    && cd $HOME/projects \
    && git clone https://github.com/indilib/pyindi-client.git \
    && cd $HOME/projects/pyindi-client \
    && git checkout PYINDI_VERSION \
    && pip install -e .


# Indi webmanager for dev
#RUN pip install indiweb
#RUN cp indiwebmanager.service /etc/systemd/system/
#RUN chmod 644 /etc/systemd/system/indiwebmanager.service
#RUN systemctl daemon-reload
#RUN systemctl enable indiwebmanager.service



# Build with
# ./build_images.sh latest linux/amd64
# launch with
# docker run --user $(id -u):$(id -g) -it --rm -v /main/machine/volume:/docker/mount/point --net host gnthibault/remote_observatory:latest
