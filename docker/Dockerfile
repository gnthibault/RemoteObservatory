ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}

# prevent keyboard related user input to be asked for
ENV DEBIAN_FRONTEND noninteractive

# Useless docker cache for pip
ENV PIP_NO_CACHE_DIR=1

# Generic install / utilities
RUN apt-get update && apt-get --assume-yes --quiet install --no-install-recommends \
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
#
## OpenPhd2 might later be replaced by a fork from @gnthibault
#RUN add-apt-repository ppa:pch/phd2 && apt-get --assume-yes --quiet install --no-install-recommends \
#    phd2
#
## Dependencies for nice reporting / latex reports
#RUN apt-get --assume-yes --quiet install --no-install-recommends \
#    texlive-latex-recommended \
#    texlive-publishers \
#    texlive-bibtex-extra \
#    texlive-science

# Using bash for lower level scripting from now-on
SHELL ["/bin/bash", "-l", "-c"]
RUN echo 'export PS1="\u@\h \w> "' | cat - /root/.profile > temp && mv temp /root/.profile

# Python environment
RUN curl https://pyenv.run | bash
RUN echo 'export PYENV_ROOT=/root/.pyenv' >> /root/.bashrc
RUN echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> /root/.bashrc
RUN echo 'eval "$(pyenv init -)"' >> /root/.bashrc
RUN pyenv install -v 3.11.7
RUN pyenv global 3.11.7

# Python virtual environment
ENV VIRTUAL_ENV=/opt/obs_venv
RUN source /root/.bashrc && python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Indi webmanager for dev
#COPY requirements.txt .
#RUN pip install indiweb
#RUN cp indiwebmanager.service /etc/systemd/system/
#RUN chmod 644 /etc/systemd/system/indiwebmanager.service
#RUN systemctl daemon-reload
#RUN systemctl enable indiwebmanager.service


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


# Build with
# ./build_images.sh latest linux/amd64
# launch with
# docker run --user $(id -u):$(id -g) -it --rm -v /main/machine/volume:/docker/mount/point --net host gnthibault/remote_observatory:latest
