# If you just want to update from the repo packages and not reinstall everything:
apt-get install -y linux-rockpro64

# temporary fix for debian stuff
Replace line 22 in /usr/bin/partbootscript.sh with this:
HOMEPART=$(lsblk --output NAME | grep ${HOMEPART}p | tail -1 | sed 's/.*-//')
The only change is the "p" at the end of homepart.


# Installation guide
sudo apt-get update

# change locale
echo "set mouse-=a" > ~/.vimrc
Also in ~/.bashrc
#Locales
export LANGUAGE=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
et dans locale.gen
sudo vim /etc/locale.gen
et decommenter en_US.UTF-8 UTF-8
sudo locale-gen

## Networking
sudo apt-get install network-manager
/etc/hosts should contain:
127.0.0.1  localhost.localdomain  localhost
/etc/NetworkManager/NetworkManager.conf should contain
[device]
wifi.scan-rand-mac-address=no
sudo systemctl restart NetworkManager.service
sudo ifconfig wlan0 up
sudo nmcli d wifi list
sudo nmcli d wifi connect network_name password ****-****-****-****

## Debuging pcie
sudo nano /etc/pulse/client.conf
Scroll through the configuration file, then uncomment (remove the ; character) and edit the following line:
From:
; autospawn = yes
to 
autospawn = no
sudo systemctl mask pulseaudio
Open the /etc/pulse/daemon.conf and set
daemonize = no

## Automount the data directory
sudo mkdir /var/RemoteObservatory/
sudo chown 1000:1000 /var/RemoteObservatory
echo "/dev/nvme0n1 /var/RemoteObservatory ext4 defaults 0 0" | sudo tee -a /etc/fstab

# astrometry

# benchmark disk
sysbench --test=fileio --file-total-size=128G prepare
sysbench --test=fileio --file-total-size=128G --file-test-mode=rndrw --max-time=300 --max-requests=0 run
sysbench --test=fileio --file-total-size=128G cleanup
sudo hdparm -tT --direct /dev/nvme0n1
./iozone -e -I -a -s 1000M -r 16k -r 512k -r 1024k -r 16384k -i 0 -i 1 -i 2 -f test
http://www.iozone.org/src/current/iozone3_487.tar

# benchmark memory
sysbench --test=memory --memory-block-size=1M --memory-total-size=100G --num-threads=1 run

# benchmark thread
sysbench --test=cpu --cpu-max-prime=20000 --num-threads=8 run

## Debugging wifi
### check dmesg for firmware
dmesg | grep irmware
### check all loaded modules
lsmod
### get info for a specific module (ex: firmware)
modinfo bcmdhd
### check driver parameter values at load
/etc/modprobe.d/iwlwifi.conf
### currently available parameters:
ls /sys/module/iwlwifi/parameters
### and their values:
cat /sys/module/bcmdhd/parameters/info_string
### firmwares are there:
ls /lib/firmware/
### eventually load it with a specific value yourself
sudo modprobe iwlwifi 11n_disable=8

### If wifi is only enabled after login:
Simply go into Network Manager > Edit Connections. Select your connection, click Edit and check Available to all users.
You may also need to add a line for each interface that you want to automatically come up at boot time in /etc/network/interfaces:
auto eth0
auto wifi0

## Installing new kernel
https://github.com/ayufan-rock64/linux-mainline-kernel/releases/download/5.0.0-1105-ayufan/linux-image-5.0.0-1105-ayufan-g2d7c76c290dc_5.0.0-1105-ayufan_arm64.deb
https://github.com/ayufan-rock64/linux-mainline-kernel/releases/download/5.0.0-1105-ayufan/linux-headers-5.0.0-1105-ayufan-g2d7c76c290dc_5.0.0-1105-ayufan_arm64.deb
dpkg -i *.deb

# ssh
sudo apt-get install openssh-server

# graphical stuff
sudo apt-get install --no-install-recommends xserver-xorg xinit
sudo apt-get install lxde-core lxappearance lightdm
sudo apt-get install chromium
sudo apt-get install xterm


#Build indi from sources:

## start to build libgphoto2 of jaseem (better than libgphoto2-dev for all functionality)
git clone https://github.com/knro/libgphoto2.git
sudo apt-get -y install libltdl7 libltdl-dev
cd libgphoto2
autoreconf --install --symlink
./configure --prefix=/usr/local
make -j8 && sudo make install

## build indi
To build libindi, first install the following packages:
sudo apt-get install cdbs libftdi1-dev libcfitsio-dev libnova-dev libusb-1.0-0-dev libjpeg-dev libusb-dev libtiff5-dev libftdi-dev fxload libkrb5-dev libcurl4-gnutls-dev libraw-dev libgsl0-dev dkms libboost-regex-dev libgps-dev libdc1394-22-dev libfftw3-dev
mkdir ~/Projects
cd ~/Projects
git clone https://github.com/indilib/indi.git
mkdir -p build/libindi
cd build/libindi
cmake -DCMAKE_INSTALL_PREFIX=/usr  ~/Projects/indi/libindi
make -j8
sudo make install
cd -
mkdir -p build/3rdparty/indi-duino
cd build/3rdparty/indi-duino
cmake -DCMAKE_INSTALL_PREFIX=/usr  ~/Projects/indi/3rdparty/indi-duino
make -j8
sudo make install
cd-

mkdir -p build/3rdparty/indi-gphoto
cd build/3rdparty/indi-gphoto
cmake -DCMAKE_INSTALL_PREFIX=/usr  ~/Projects/indi/3rdparty/indi-gphoto
make -j8
sudo make install
cd-


###Install Astrometry.net for ekos
sudo apt install astrometry.net

### build kstars
sudo apt-get -y install build-essential cmake git libeigen3-dev libcfitsio-dev zlib1g-dev extra-cmake-modules libkf5plotting-dev libqt5svg5-dev libkf5xmlgui-dev kio-dev kinit-dev libkf5newstuff-dev kdoctools-dev libkf5notifications-dev qtdeclarative5-dev libkf5crash-dev gettext libnova-dev libgsl-dev libraw-dev libkf5notifyconfig-dev wcslib-dev libqt5websockets5-dev qt5keychain-dev xplanet xplanet-images
mkdir ~/Projects/build/kstars
cd ~/Projects
git clone git://anongit.kde.org/kstars.git
cd build/kstars
cmake -DCMAKE_INSTALL_PREFIX=/usr ~/Projects/kstars
make -j8
sudo make install

### build kstars
mkdir ~/Projects/build/phd2
git clone https://github.com/OpenPHDGuiding/phd2.git
cd build/phd2
cmake -DCMAKE_INSTALL_PREFIX=/usr ~/Projects/phd2
make -j8
sudo make install

# Kernel driver for serial arduino connexion
sudo apt-get install gcc-aarch64-linux-gnu
git clone https://github.com/mrfixit2001/rockchip-kernel.git
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- rockchip_linux_defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- prepare
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- scripts
git clone https://github.com/skyrocknroll/CH341SER_LINUX.git
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
Then copy to destination machine and
sudo make load

# Build arduino sdk OPTIONAL (dont do it)
git clone https://github.com/arduino/Arduino.git
cd Arduino/build
sudo apt-get install openjdk-8-jdk ant
./build_all_dist.bash
cd .. ; tar -xvf linux/arduino-1.8.10-linux64.tar.xz


# install mobindi
# First install nodejs
curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install

# Now mobindi
sudo apt-get install git cmake zlib1g-dev libcurl4-openssl-dev libgsl-dev libraw-dev libcfitsio-dev libjpeg-dev libpng-dev libcgicc-dev daemontools nginx
git clone https://github.com/pludov/mobindi.git
cd mobindi
./install.sh

#start it with
./startup.sh
Connect to http://localhost:8080, or if you want to test the new support for https, use: https://localhost:8443

# Afterwards, update to latest version with
git pull --ff-only
./install.sh
./startup.sh
npm install




### More on wifi stuff

diagnose with:
wget -N -t 5 -T 10 https://github.com/UbuntuForums/wireless-info/raw/master/wireless-info && \
chmod +x wireless-info && \
./wireless-info

download firmware from https://github.com/kszaq/brcmfmac_sdio-firmware-aml/tree/master/firmware/brcm

From https://www.raspberrypi.org/forums/viewtopic.php?t=130195
I managed to find rt2870.bin from the original kernel, and I have put it in lib/firmware, and it still won't work.
airquixorz wrote:
The only firmware that's running is the raspberry firmware. I've also tried ifconfig -a, and it returns eth0 and l0 but no wlan0.
The ralink wifi devices use a different name - ra0.
There are two solutions. I use option 2.
1. Edit file /etc/network/interfaces. Copy the section for wlan0 so you have two wlan0 sections and then change the name wlan0 in one of the sections to ra0.
2. Create a file /etc/udev/rules.d/95-ralink.rules using command
Code: Select all
sudo nano /etc/udev/rules.d/95-ralink.rules
and add the line
Code: Select all
ACTION=="add", SUBSYSTEM=="net", ATTR{type}=="1", KERNEL=="ra*", NAME="wlan0"
This will change the ralink wifi driver name from ra0 which it usually uses to wlan0 so you don't need to edit /etc/network/interfaces.




# old stuff
### solve locale problem on computer
export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
sudo dpkg-reconfigure locales

### Setup automatic time update toward UTC
sudo apt-get install ntp
To modify the systems to use UTC time, edit /etc/default/rcS setting UTC=yes.




###Third part soft for driving eqmod mounts
cd ~/Projects
mkdir -p build/indi-eqmod
cd build/indi-eqmod
cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Debug ~/Projects/indi/3rdparty/indi-eqmod

###Other 3rd party apps/driver
mkdir -p build/3rdparty
cd build/3rdparty
cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Debug ../../3rdparty/


##Install PHD2 for autoguiding
sudo apt-add-repository ppa:pch/phd2 
sudo apt-get update 
sudo apt-get install phd2

## Webserver for indi
sudo apt-get -y install python-requests python-psutil python-bottle
git clone https://github.com/knro/indiwebmanager
cd indiwebmanager/servermanager/
python drivermanager.py

## Usage
The INDI Web Manager can run as a standalone server. It can be started manually by invoking python:
$ cd servermanager
$ python drivermanager.py
Then using your favorite web browser, go to http://localhost:8624 if the INDI Web Manager is running locally. If the INDI Web Manager is installed on a remote system, simply replace localhost with the hostname or IP address of the remote system.
## Auto Start
To enable the INDI Web Manager to automatically start after a system reboot, a systemd service file is provided for your convenience:
[Unit]
Description=INDI Web Manager
After=multi-user.target
[Service]
Type=idle
User=pi
ExecStart=/usr/bin/python /home/pi/servermanager/drivermanager.py
ExecStartPost=/usr/bin/python /home/pi/servermanager/autostart.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
The above service files assumes you copied the servermanager directory to /home/pi, so change it to whereever you installed the directory on your target system. The user is also specified as pi and must be changed to your username.
If you selected any profile as Auto Start then the INDI server shall be automatically started when the service is executed on start up.
Copy the indiwebmanager.service file to /lib/systemd/system:
sudo cp indiwebmanager.service /lib/systemd/system/
sudo chmod 644 /lib/systemd/system/indiwebmanager.service
Now configure systemd to load the service file during boot:
sudo systemctl daemon-reload
sudo systemctl enable indiwebmanager.service


## Setuping remote access

### Start
sudo apt-get install xvfb x11-xkb-utils
sudo apt-get install xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic  xserver-xorg-core

Lancer la commande :
vncpasswd /etc/vnc/vncpasswd

Ensuite, ajouter le contenu suivant dans /etc/lightdm/lightdm.conf
[VNCServer]
enabled=true
command=/usr/bin/Xvnc -rfbauth /etc/vnc/vncpasswd
port=5900
width=1280
height=1024
depth=24

Tester avec sudo /etc/init.d/lightdm restart

#VNC from webserver:
git clone git://github.com/kanaka/noVNC   
cd noVNC
./utils/launch.sh --vnc 192.168.0.73:5900

## Connect wifi in command line
add wifi_dummy line in /etc/modules
ifconfig wlan0 up
nmcli d wifi list
sudo nmcli d wifi connect UPCC1492B7 password fudefx85kQpu


## Create wifi hotspot directly fron Indi

HOT SPOT:  It is possible to create a WiFi hotspot from your Pi3's wireless and connect to it via WiFi and do away with the Ethernet cable completely.  Again, I have to thank rlancaste (from the INDI forums) for the information that got me to a successful conclusion here.  The key for me was using RealVNC instead of Vino.  I tried everything I'm about to tell you with Vino and it wouldn't work.  I'm still not sure why RealVNC worked for me and Vino didn't but I suspect it's an encryption issue of some sort.  I found this to be pretty straight forward at the time I did it.  First thing you need to do is actually create a WiFi Hotspot on your Pi. To do that:

Navigate your way to the Network Connections window (System/Preferences/Internet and Network/Network Connections) to create a new WiFi Hospot.
Click Add to create a new connection
Select WiFi as the type of connection from the drop-down
Now: ◦
Give your connection a name at the top (mine is AstroPi)
Use that exact same name as the SSID
Change Mode to Hotspot
Go to the Wi-Fi Security tab and change it to WPA Personal (if you want a secure connection; recommended) and establish the password you want.
Hit Save, your done here.
Now, you need to be able to start that hotspot when you want it.  On the desktop, right-click and select Create a Launcher.  Name it something like “Start Hotspot” (your choice here) and insert the command nmcli connection up in the command field.  So for me, that command is: nmcli connection up AstroPi.  Hit OK and that's done. Just double click on that launcher to make the WiFi hotspot happen.  On my system, I can tell the hotspot started because the little up/down arrow for my netork connection in the toolbar goes away.  I'll get that back later when I shut the hotspot down.  Now, when you start the hotspot, you can look for that WiFi connection from your remote computer and see the SSID you created (AstroPi in my case) and connect to it with the password you specified just like any other WiFi connection.  Click properties on that connection and check out the IP address your remote computer was given by the hotspot.  That will give you a clue to the IP address you need to use as the address in VNC viewer in order to connect to the Pi.  In my case, the IP address assigned to my laptop by the Pi3 is 10.42.0.43. So that means the Pi3's address is 10.42.0.1 (just replace the last number with 1) and that's what I put in the VNC viewer to connect.  Works great.
Now, rlancaste also suggested a couple other launchers for the desktop that you can do here, if you want.  Some systems are having problems with the nm-applet and it needs to be restarted.  So a launcher with nm-applet as the command line can be created to do that.  My up/down arrow on the desktop that indicates a network connection sometime just disappears.  This launcher will bring it back.  This isn't a critical thing.  I generally don't care if the network arrows are there or not under normal circumstances.  The second launcher will turn off the hotspot and go back to normal network operations.  That launcher needs the command line: gksu systemctl restart NetworkManager.service and I used the name that was suggested to me of “Restart Network Manager Service” as the name of the launcher.  So, if you do all that you will have a launcher to turn the hotspot on, another to turn it off and go back to normal and a third to restart the nm-applet when it decides to stop working.  I suppose you could create a startup command in your startup programs to automatically start the hotspot when the Pi is turned on if you are going to run it headless and via a hotspot.  I'm connecting with an Ethernet cable directly to start with and I can activate the hotspot if I like from there.


# How to use Indi (basics ?)

indiserver ../indi/build/libindi/examples/tutorial_one/tutorial_one

Je lance le serveur indi avec la commande suivante:
indiserver indi_lx200basic indi_gphoto

indi_lx200basic pour le Pic-Astro
indi_gphoto pour mon Canon EOS1100D


## How to use PHD2
Start PHD2 in Terminal by simply typing PHD2 and pressing Enter.  Do not connect anything at this point, simply get it open so you know it’s working.  
Start KStars, then INDI/Ekos and get the INDI server running and everything connected.  At this point I would open the Guider Module in Ekos and check to make sure you have a working connection to your guide camera.
Now go back to PHD2 to connect/configure a camera and mount.  Click on the USB icon on the bottom left of the PHD screen.  Select INDI Mount and INDI Camera as your equipment.  Name the profile what you want, I named it “INDI”.
Now, confirm the camera and mount are set up properly within PHD2.  Click on the setup icons next to the connect buttons. With INDI server already running and everything connected in Ekos, you should be able select your CCD guide camera in the dropdown for the camera driver and your mount type in the dropdown for your mount driver.  In my case with an SSAG camera and EQMod mount, I select QHY CCD for my camera and EQMod Mount for my mount driver.  Don’t touch anything here.  Of course, you should see your equipment in place of mine in the screens.  Close these screens and hit “Connect All” on the PHD2 connect equipment screen.  
Now go into the Ekos Guider Module and click on the Options button there near the middle.  In the Options window select PHD2 for the guiding option and don't change anything else.  Notice that the port in the Options window is 4400.  You may have noticed the port listed iN PHD2 was 7642 – that’s OK!  They are the right numbers, do not be tempted to change them.  At this point hit “OK”, close the options window you should be good.  Notice, if you’ve used PHD before, you might be tempted to go back to the PHD control panel and start looping the image like you normally do when it’s stand-alone.  Don’t do that.  Ekos will start PHD2 when you click “Guide” in the guider module.  Of course, you DO need to go into PHD2 and configure the guiding options the way you want.  Good luck.

Notes: 1) Start Ekos first so PHD2 sees the drivers.  2) Leave everything at the defaults.  3) Let Ekos start PHD2 imaging, calibration, etc.  Don't do it in the PHD2 panel.


# How to use AstroEQ (under linux)

Pre-requis:
sudo apt-get install libjssc-java

Installation from source:
git clone https://github.com/TCWORLD/AstroEQ.git
cd Downloads
unzip ./AstroEQ-ConfigUtility-LINUX.zip
sudo dpkg -i ./astroequploader-3.6.deb 

Ensuite utiliser l'utilitaire graphique astroEQ, avec les parametres suivants (voir la doc Concernant la configuration d'astroEQ: https://www.astroeq.co.uk/tutorials.php?link=/doku/doku.php?id=config):

Les moteurs sont des 400 pas 1.2A 3.3ohms 4V avec un  couple de 21.6 N/cm..
Leur référence: SH4009L1206 (la dernière de la série).

En R.A:
Le rapport de démultiplication est de 1440 par la vis sans fin secteur lisse et de 4 par le jeux de poulie sois une réduciton totale de 1440*4= 5760
il faut aussi multiplier par le nombre de pas du moteur, et de micropas par pas le cas echeant.

En DEC:
Je n'arrive plus a retrouver les references des poulies crantees que j'avais achete sur HPC, donc il faudra compter le rapport de reduction de l'ensemble, mais il doit etre assez proche de celui de l'axe de RA.

Cela donne, dans AstroEQ:
ST4 Rate (x Sidereal): 0.25 (default)
Advanced HC Detect: Disabled (default)
Motor Driver IC TYpe DRV882x (default)
uStep Gear Changing: Disabled (Pas besoin, vu qu'on va fonctionner tout le temps en pas complets.
Motor Microstep Level: 1 (Pas besoin de microstepping vu le rapport de reduction enorme)

Right Ascension Axis: Forward (a verifier)
Motor Step Angle (deg): 0.9
Motor Gear Ratio: 4
Worm Gear Ratio: 1440
Goto Rate (x Sidereal): 2

Declination Axis: Pour l'instant, donner les memes references.

Quelques infos supplementaires:
ST4 Rate (x Sidereal): In this field you should enter a value between 0.05 and 0.95. This value represents the speed at which the mount will move when an ST4 signal is received. The speed is a factor of the sidereal rate - e.g. 0.5 means half the sidereal rate.
Advanced HC Detect: This setting should only be âEnabledâ if you have a V4.6 or newer mount, or if you have performed the advanced hand-controller resistor modification. If you have an older version AstroEQ controller, leave this as âDisabledâ
Motor Driver IC Type: This allows you to select which motor driver IC is used in the AstroEQ. All purchased controllers are shipped with a DRV882x type driver board. For custom controllers you may have other versions. If you are unsure, assume DRV882x.
uStep Gear Changing: When a microstepping mode of 8 uStep or higher is used, the AstroEQ will change stepping modes (âgear changeâ) when performing a high speed movement such as a Go-To. This allows the mount to have a higher top speed at the expense of noise. This setting can be used to enable or disable this feature.
Motor Microstep Level: This determines the number of microsteps to be used. For lower gear ratios, a higher microstep level should be used. Typical values are 4 uSteps, 16 uSteps and 32 uSteps.

