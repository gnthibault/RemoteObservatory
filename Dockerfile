ARG BASE_IMAGE=ubuntu:24.04
ARG TARGETPLATFORM="linux/amd64"

FROM ${BASE_IMAGE}

# prevent keyboard related user input to be asked for
ENV DEBIAN_FRONTEND=noninteractive

# Useless docker cache for pip
ENV PIP_NO_CACHE_DIR=1

# Versioning
ENV INDI_VERSION=v2.1.2
ENV PYINDI_VERSION=v2.1.2
ENV INDI_3RD_PARTY_VERSION=v2.1.2
ENV PYTHON_VERSION=3.12.3
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
      export BARCH="ARM64"; \
    elif [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
      export BARCH="AMD64"; \
    else \
        export BARCH="X86"; \
    fi

# Actual application code and configs (could be used in builds)
RUN mkdir -p /opt/remote_observatory/
COPY . /opt/remote_observatory/

RUN echo '\
Acquire::Retries "8";\
Acquire::https::Timeout "240";\
Acquire::http::Timeout "240";\
APT::Get::Assume-Yes "true";\
APT::Install-Recommends "false";\
APT::Install-Suggests "false";\
Debug::Acquire::https "true";\
' > /etc/apt/apt.conf.d/99custom

# Generic install / utilities / dev
RUN apt-get update && apt-get --assume-yes --quiet install --no-install-recommends \
    apt-utils \
    build-essential \
    ca-certificates \
    cmake \
    debconf \
    gettext \
    git \
    graphviz \
    libgraphviz-dev \
    libz3-dev \
    python3 \
    python3-dev \
    python3-numpy-dev \
    python3-pip \
    python3-setuptools \
    python3-six \
    retry \
    sudo \
    tmux \
    vim && \
    apt-get clean

# create user that will be used to run the applications
ENV USERNAME=observatory
ENV USERID=1001
ENV HOME=/home/observatory
RUN groupadd -g $USERID $USERNAME \
    && useradd -ms /bin/bash -u $USERID -g $USERID -d $HOME $USERNAME \
    && echo "${USERNAME} ALL=(ALL) NOPASSWD: ALL" | tee /etc/sudoers.d/$USERNAME \
    && echo "${USERNAME}:${USERNAME}" | chpasswd
#    && usermod -aG sudo $USERNAME
RUN chown -R $USERNAME:$USERNAME /opt

##################################################

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
  python3-pil
#   libcairo2-dev \
#   libjpeg-dev \
#   libnetpbm11-dev \

USER $USERNAME
RUN mkdir -p $HOME/projects/astrometry.net \
  && cd $HOME/projects/astrometry.net \
  && curl -sSl -o astrometry.net-0.96.tar.gz --retry 8 https://astrometry.net/downloads/astrometry.net-0.96.tar.gz \
  && tar -xvf ./*.tar.gz \
  && cd astrometry.net-0.96 \
  && export NETPBM_LIB="-L/usr/lib -lnetpbm" \
  && export NETPBM_INC="-I/usr/include" \
  && ./configure --prefix=/usr \
  && make all SYSTEM_GSL=yes GSL_INC="-I/usr/include" GSL_LIB="-L/usr/lib -lgsl" -j1 \
  && sudo make install \
  && sudo ln -s /usr/local/astrometry/bin/an-fitstopnm /usr/local/bin/an-fitstopnm

#  && wget --recursive --no-parent --no-host-directories --cut-dirs=6 --accept "*.fits" --continue --directory-prefix=/usr/local/astrometry/data/ https://portal.nersc.gov/project/cosmo/temp/dstn/index-5200/LITE/

# Now Download astrometry.net index files -- This needs to be moved when gsutil is updated
# RUN pyenv install 3.11 \
#  && pyenv global 3.11 \
#  && gsutil -m cp gs://astrometry_data/* /usr/local/astrometry/data/ \
#  && pyenv global $PYTHON_VERSION
#RUN mv /opt/remote_observatory/astrometry_data/* /usr/local/astrometry/data/
USER root
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

# Generic dependency to make sure we can install system components that will start at boot if built as an image (not docker)
# RUN apt-get --assume-yes --quiet install --no-install-recommends systemd-sysv

# Dependencies to build indi from sources + pyindi-client that is linked with binaries through swig
# astrometry.net was built from source
RUN apt-get --assume-yes --quiet install --no-install-recommends \
        cdbs \
        dkms \
        fxload \
        libboost-regex-dev \
        libcfitsio-dev \
        libcurl4-gnutls-dev \
        libdbus-glib-1-dev \
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
# cache trick from https://stackoverflow.com/questions/55003297/how-to-get-git-clone-to-play-nice-with-docker-cache
USER $USERNAME
RUN --mount=type=cache,target=$HOME/.cache,uid=$USERID \
    mkdir -p $HOME/projects/indi \
    && git -C $HOME/.cache/indi/ fetch || retry -t 8 -d 10 git clone https://github.com/indilib/indi.git $HOME/.cache/indi/ \
    && cd $HOME/.cache/indi/ && git checkout $INDI_VERSION && cp -r --parents ./* $HOME/projects/indi/ \
    && mkdir -p $HOME/projects/build/indi \
    && cd $HOME/projects/build/indi \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_SYSTEM_PROCESSOR=$BARCH $HOME/projects/indi \
    && make -j1 \
    && sudo make install

# Dependencies to build indi-3rd party from sources
USER root
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
USER $USERNAME
RUN --mount=type=cache,target=$HOME/.cache,uid=$USERID \
    mkdir -p $HOME/projects/indi-3rdparty/ \
    && git -C $HOME/.cache/indi-3rdparty/ fetch || retry -t 8 -d 10 git clone https://github.com/indilib/indi-3rdparty.git $HOME/.cache/indi-3rdparty/ \
    && cd $HOME/.cache/indi-3rdparty/ && git checkout $INDI_3RD_PARTY_VERSION && cp -r --parents ./* $HOME/projects/indi-3rdparty/

RUN for i in indi-duino libasi indi-asi libplayerone indi-playerone indi-shelyak libaltaircam; \
    do cd $HOME/projects \
    && mkdir -p $HOME/projects/build/$i \
    && cd $HOME/projects/build/$i \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_SYSTEM_PROCESSOR=$BARCH $HOME/projects/indi-3rdparty/$i \
    && make -j1 \
    && sudo make install; \
    done

## OpenPhd2 might later be replaced by the original source ?
#RUN add-apt-repository ppa:pch/phd2 && apt-get --assume-yes --quiet install --no-install-recommends \
#    phd2
# Dependencies to build phd2 from sources
USER root
RUN apt-get --assume-yes --quiet install --no-install-recommends \
    libwxgtk3.2-dev

USER $USERNAME
RUN --mount=type=cache,target=$HOME/.cache,uid=$USERID \
    mkdir -p $HOME/projects/phd2 \
    && git -C $HOME/.cache/phd2/ fetch || retry -t 8 -d 10 git clone https://github.com/gnthibault/phd2.git $HOME/.cache/phd2/ \
    && cd $HOME/.cache/phd2/ && git checkout master && cp -r --parents ./* $HOME/projects/phd2/ \
    && mkdir -p $HOME/projects/build/phd2 \
    && cd $HOME/projects/build/phd2 \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_SYSTEM_PROCESSOR=$BARCH $HOME/projects/phd2 \
    && make -j1 \
    && sudo make install

## Dependencies for nice reporting / latex reports
USER root
RUN apt-get --assume-yes --quiet install --no-install-recommends \
    texlive-latex-recommended \
    texlive-publishers \
    texlive-bibtex-extra \
    texlive-science

# Downloading gcloud client
USER $USERNAME
RUN curl --retry 8 -sSL https://sdk.cloud.google.com > /tmp/gcl && bash /tmp/gcl --install-dir=/opt/gcloud --disable-prompts
ENV PATH=$PATH:/opt/gcloud/google-cloud-sdk/bin

# Using bash for lower level scripting from now-on
USER $USERNAME
SHELL ["/bin/bash", "-l", "-c"]
RUN echo 'export PS1="\u@\h \w> "' | cat - $HOME/.profile > /tmp/temp && mv /tmp/temp $HOME/.profile

# Python environment
RUN mkdir -p /opt/remote_observatory_venv
RUN curl --retry 8 https://pyenv.run | bash
# Reminder about environment management in unix:
#~/.bash_profile	Only for login shells	Good for setting environment variables (export VAR=value), path configurations, etc.
#~/.profile	Only for login shells, but used by other shells too (e.g., sh, dash)	Alternative to .bash_profile. Used when .bash_profile is missing.
#~/.bashrc	Only for interactive non-login shells	Used for aliases, shell functions, and interactive behavior. Not sourced in non-interactive shells.
# Please not in ubuntu, only .profile and .bashrc exists, and .bashrc is sourced from .profile if it exist
# Unfortunately, the fcking pyenv script is also internally running bash (with -norc option, but that's not enough)
# hence creating an infinitely recursing loop. That's why we unset BASH_ENV
RUN echo "unset BASH_ENV" >> $HOME/.nibashrc
RUN echo 'export PYENV_ROOT=$HOME/.pyenv' | tee -a $HOME/.bashrc $HOME/.nibashrc
RUN echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' | tee -a $HOME/.bashrc $HOME/.nibashrc
RUN echo 'eval "$(pyenv init -)"' | tee -a  $HOME/.bashrc $HOME/.nibashrc
ENV PYENV_ROOT="$HOME/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"
RUN pyenv install -v $PYTHON_VERSION
RUN pyenv global $PYTHON_VERSION
ENV PATH="$PYENV_ROOT/shims:$PATH"

# Python virtual environment
ENV VIRTUAL_ENV=/opt/remote_observatory_venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN echo 'source /opt/remote_observatory_venv/bin/activate' | tee -a $HOME/.bashrc $HOME/.nibashrc

# Python packages
#COPY requirements.txt .
RUN pip install -r /opt/remote_observatory/requirements.txt

# Build and install pyindi-client
RUN --mount=type=cache,target=$HOME/.cache,uid=$USERID \
    mkdir -p $HOME/projects/pyindi-client/ \
    && git -C $HOME/.cache/pyindi-client/ fetch || retry -t 8 -d 10 git clone https://github.com/indilib/pyindi-client.git $HOME/.cache/pyindi-client/ \
    && cd $HOME/.cache/pyindi-client/ && git checkout $PYINDI_VERSION && cp -r --parents ./* $HOME/projects/pyindi-client/ \
    && cd $HOME/projects/pyindi-client/ \
    && pip install -e .

# Setup "working directory" for logs
RUN mkdir -p /opt/RemoteObservatory \
  && chown -R $USERNAME:$USERNAME /opt/RemoteObservatory



# CMD /sbin/init

# Note about running multiple services on the same docker (not recommended)
# Your dockerfile might look like this:
# RUN apt-get update && apt-get install -y openssh-server apache2 supervisor
# RUN mkdir -p /var/lock/apache2 /var/run/apache2 /var/run/sshd /var/log/supervisor
# COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
# EXPOSE 22 80
# CMD ["/usr/bin/supervisord"]
# Your supervisord.conf might look something like this:
# [supervisord]
# nodaemon=true
# [program:sshd]
# command=/usr/sbin/sshd -D
# [program:apache2]
# command=/bin/bash -c "source /etc/apache2/envvars && exec /usr/sbin/apache2 -DFOREGROUND"


# Add Docker's official GPG key:
# sudo apt-get update
# sudo apt-get install ca-certificates curl
# sudo install -m 0755 -d /etc/apt/keyrings
# sudo curl --retry 8 -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
# sudo chmod a+r /etc/apt/keyrings/docker.asc

# # Add the repository to Apt sources:
# echo \
#   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
#   $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
#   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
# sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin


# Before building, to save data and avoid issue with apt-get install not signed repo, start with cleaning
# docker image prune -f && docker buildx prune -f && docker container prune -f
# docker buildx build --platform linux/arm64/v8 -t test_to_delete .
# docker buildx build --platform linux/amd64 -t test_to_delete .
# docker buildx build --platform linux/amd64 -t europe-west1-docker.pkg.dev/remote-observatory-dev-XXX/remote-observatory-main-repo/remote_observatory .

# If you want to debug a layer:
# DOCKER_BUILDKIT=0 docker build --platform linux/arm64/v8 -t test_to_delete .
# docker run -it --rm 1941be9e1d8c /bin/bash
# docker buildx prune # To clean cache
# EDIT NEW WAY
# export BUILDX_EXPERIMENTAL=1
# docker buildx prune # To clean cache
# docker buildx debug --on=error --progress=plain build --platform linux/amd64 -t test_to_delete .

# start the container in daemon mode with -d, and then look around in a shell using docker exec -it <container id> sh.
# docker run -d --rm  --name remote_observatory -v $HOME/projects/RemoteObservatory:/opt/remote_observatory_dev -p 5901:5901 test_to_delete
# docker exec -it remote_observatory /bin/bash
# docker kill remote_observatory

# docker run --user $(id -u):$(id -g) -it --rm -v /main/machine/volume:/docker/mount/point --net host gnthibault/remote_observatory:latest



# tmux new -s t1
# ctrl b + d
# tmux new -s t2
# export PYTHONPATH=/opt/remote_observatory_dev
# python ./apps/launch_remote_observatory.py