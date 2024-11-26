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

# Actual application code and configs (could be used in builds)
RUN mkdir -p /opt/remote_observatory/astrometry_data
COPY . /opt/remote_observatory/

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
RUN apt-get --assume-yes --quiet install --no-install-recommends \
  build-essential \
  curl \
  git \
  file \
  pkg-config \
  swig \
  libcairo2-dev \
  libnetpbm10-dev \
  netpbm \
  libpng-dev \
  libgsl-dev \
  libjpeg-dev \
  zlib1g-dev \
  libbz2-dev \
  libcfitsio-dev \
  wcslib-dev \
  python3 \
  python3-pip \
  python3-dev \
  python3-numpy \
  python3-scipy \
  python3-pil \
  && mkdir -p $HOME/projects/astrometry.net \
  && cd $HOME/projects/astrometry.net \
  && wget https://astrometry.net/downloads/astrometry.net-0.96.tar.gz \
  && tar -xvf ./*.tar.gz \
  && cd astrometry.net-0.96 \
  && export NETPBM_LIB="-L/usr/lib -lnetpbm" \
  && export NETPBM_INC="-I/usr/include" \
  && ./configure --prefix=/usr \
  && make all SYSTEM_GSL=yes GSL_INC="-I/usr/include" GSL_LIB="-L/usr/lib -lgsl" -j8 \
  && make install \
  && ln -s /usr/local/astrometry/bin/an-fitstopnm /usr/local/bin/an-fitstopnm
#   libcairo2-dev \
#   libjpeg-dev \
#   libnetpbm11-dev \

#  && wget --recursive --no-parent --no-host-directories --cut-dirs=6 --accept "*.fits" --continue --directory-prefix=/usr/local/astrometry/data/ https://portal.nersc.gov/project/cosmo/temp/dstn/index-5200/LITE/

# Now Download astrometry.net index files -- This needs to be moved when gsutil is updated
# RUN pyenv install 3.11 \
#  && pyenv global 3.11 \
#  && gsutil -m cp gs://astrometry_data/* /usr/local/astrometry/data/ \
#  && pyenv global $PYTHON_VERSION
#RUN mv /opt/remote_observatory/astrometry_data/* /usr/local/astrometry/data/
RUN find /opt/remote_observatory/astrometry_data/ -maxdepth 1 -type f -exec mv '{}' /usr/local/astrometry/data/  \;

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
        libgsl-dev \
        libjpeg-dev \
        libkrb5-dev \
        libnova-dev \
        libraw-dev \
        libtiff5-dev \
        libusb-1.0-0-dev \
        libusb-dev \
        swig

# Build indi from sources
RUN --mount=type=cache,target=/tmp/git_cache/ \
    mkdir -p $HOME/projects/indi \
    && git clone https://github.com/indilib/indi.git /tmp/git_cache/indi/ \
    && cd /tmp/git_cache/indi/ && git checkout $INDI_VERSION && cp -r . $HOME/projects/indi/ \
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
RUN --mount=type=cache,target=/tmp/git_cache/ \
    mkdir -p $HOME/projects/indi-3rdparty/ \
    && git clone https://github.com/indilib/indi-3rdparty.git /tmp/git_cache/indi-3rdparty/ \
    && cd /tmp/git_cache/indi-3rdparty/ && git checkout $INDI_3RD_PARTY_VERSION && cp -r . $HOME/projects/indi-3rdparty/

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

RUN --mount=type=cache,target=/tmp/git_cache/ \
    git clone https://github.com/gnthibault/phd2.git /tmp/git_cache/phd2/ \
    && mkdir -p build/phd2 \
    && cd build/phd2 \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr /tmp/git_cache/phd2/ \
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

# Downloading gcloud client
RUN curl -sSL https://sdk.cloud.google.com > /tmp/gcl && bash /tmp/gcl --install-dir=/opt/gcloud --disable-prompts
ENV PATH $PATH:/opt/gcloud/google-cloud-sdk/bin

# Using bash for lower level scripting from now-on
SHELL ["/bin/bash", "-l", "-c"]
RUN echo 'export PS1="\u@\h \w> "' | cat - /root/.profile > temp && mv temp /root/.profile

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
RUN --mount=type=cache,target=/tmp/git_cache/ \
    mkdir -p $HOME/projects/pyindi-client/ \
    && git clone https://github.com/indilib/pyindi-client.git /tmp/git_cache/pyindi-client/ \
    && cd /tmp/git_cache/pyindi-client/ && git checkout $PYINDI_VERSION && cp -r . $HOME/projects/pyindi-client/ \
    && cd $HOME/projects/pyindi-client/ \
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

# docker buildx build --platform linux/arm64/v8 -t test_to_delete .
# docker buildx build --platform linux/amd64 -t test_to_delete .
# docker buildx build -t europe-west1-docker.pkg.dev/tom-toolkit-dev-hxm/remote-observatory-tom-repo/tom_app .

# If you want to debug a layer:
# DOCKER_BUILDKIT=0 docker build --platform linux/arm64/v8 -t test_to_delete .
# docker run -it --rm 1941be9e1d8c /bin/bash
# docker buildx prune # To clean cache