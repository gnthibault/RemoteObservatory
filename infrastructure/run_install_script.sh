#!/bin/bash

parent_path="/opt/remote_observatory/infrastructure"
service_file_path="${parent_path}/observatory.service"
destination_service_file_path="/lib/systemd/system/observatory.service"
requirements_file_path="${parent_path}/requirements_docker_compose.txt"
env_file_path="${parent_path}/.env"

## create user that will be used in subsequent steps
#useradd -ms /bin/bash observatory
username=observatory
userhome=$( getent passwd "$username" | cut -d: -f6 )
chown -R $username:$username $userhome
chown -R $username:$username /opt
## Add user to sudoers for reboot/shutdown commands
#usermod -aG sudo $username
##username=$(getent passwd 1000 | cut -d: -f1)

# Now update and install packages
#apt-get update && apt-get upgrade --yes # This generates plenty of errors related to uboot/kernel stuff
apt-get update
apt-get install --reinstall --yes\
  net-tools\
  software-properties-common\
  sudo

# You want to disable the auto-upgrade that can potentially break something ?
# https://help.ubuntu.com/community/AutomaticSecurityUpdates
# sed -i 's/APT::Periodic::Unattended-Upgrade "1";/APT::Periodic::Unattended-Upgrade "0";/g' /etc/apt/apt.conf.d/50unattended-upgrades

#DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
#    ubuntu-desktop \
#    && apt-get clean
# Install XFCE, VNC server, dbus-x11, and xfonts-base for vnc
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    accountsservice \
    dbus-x11 \
    tightvncserver \
    x11vnc \
    xfce4 \
    xfce4-goodies \
    xfonts-base \
    xinit \
    xorg \
    xvfb \
    && apt-get clean

# Setup lightdm after debugging with lightdm --test-mode --debug
#lightdm\
#lightdm-gtk-greeter\
#cp $parent_path/lightdm.conf /etc/lightdm/lightdm.conf
#sed -i "s~LOCAL_USER_NAME~${username}~g" /etc/lightdm/lightdm.conf
#### systemctl enable lightdm # The unit files have no installation config

# vnc server
# https://askubuntu.com/questions/120973/how-do-i-start-vnc-server-on-boot
# Setup VNC server
mkdir $userhome/.vnc \
    && echo "$username" | vncpasswd -f > $userhome/.vnc/passwd \
    && chmod 600 $userhome/.vnc/passwd \
    && cp $parent_path/xstartup $userhome/.vnc/xstartup \
    && chmod +x $userhome/.vnc/xstartup \
    && chown -R $username:$username $userhome/.vnc

# Create an .Xauthority file
touch $userhome/.Xauthority \
    && chown -R $username:$username $userhome

# Copy a script to start the xsession and VNC server
cp $parent_path/observatory-xvfb.service /etc/systemd/system/observatory-xvfb.service
service_file_path=/etc/systemd/system/observatory-xvfb.service
chmod 0755 ${service_file_path}
# changed default sed separator from / to ~
sed -i "s~LOCAL_USER_NAME~${username}~g" ${service_file_path}
sed -i "s~LOCAL_INSTALL_PATH~${parent_path}~g" ${parent_path}/.env
systemctl daemon-reload
systemctl enable observatory-xvfb


## Copy a script to start the VNC server
#cp $parent_path/vncserver.service /etc/systemd/system/vncserver.service
#service_file_path=/etc/systemd/system/vncserver.service
#chmod 0755 ${service_file_path}
## changed default sed separator from / to ~
#sed -i "s~LOCAL_USER_NAME~${username}~g" ${service_file_path}
#sed -i "s~LOCAL_INSTALL_PATH~${parent_path}~g" ${service_file_path}
#systemctl daemon-reload
#systemctl enable ${service_file_path}
# Expose VNC port
#EXPOSE 5901


chown -R $username:$username $userhome


# Install docker
curl -fsSL https://get.docker.com -o get-docker.sh
/bin/bash ./get-docker.sh
rm ./get-docker.sh
usermod -a -G docker ${username}

# Installing docker compose and other tools that needs proper system like networking
# Make sure network-manager it is needed, already in template
apt-get install --reinstall --yes\
  libffi-dev\
  libssl-dev\
  network-manager\
  wpasupplicant
# Clean /var/cache/apt/archives/
apt autoremove && apt autoclean

# Install python3 dependencies
#su - ${username} -ci "pip3 install -r ${requirements_file_path}"
#su - ${username} -c 'BASH_ENV=$userhome/.nibashrc bash -c "echo \$PYENV_ROOT"'
#sudo -u ${username} BASH_ENV=$userhome/.nibashrc bash -c "pip3 install -r ${requirements_file_path}"
su - ${username} -c "BASH_ENV=$userhome/.nibashrc bash -c 'pip3 install -r ${requirements_file_path}'"

#### Custom scripts to support scripts/binary utilities 
# Enable temperature monitoring to access /dev/vchiq for GPU temp
#usermod -a -G video $username #This one cannot really work for now
#echo 'SUBSYSTEM=="vchiq",GROUP="video",MODE="0660"' > /etc/udev/rules.d/10-vchiq-permissions.rules
#chmod a+x ${parent_path}/telegraf/scripts/*.sh
#chmod o+x /bin/vcgencmd

# Enable serial access
usermod -a -G dialout $username

## Enable GPIO
#groupadd gpio
#usermod -a -G gpio $username
#echo 'KERNEL=="gpiomem",GROUP="gpio",MODE="0660"' > /etc/udev/rules.d/10-gpiomem-permissions.rules
#echo "SUBSYSTEM==\"gpio*\", PROGRAM=\"/bin/sh -c 'find -L /sys/class/gpio/ -maxdepth 2 -exec chown root:gpio {} \; -exec chmod 770 {} \; || true\"" > /etc/udev/rules.d/10-gpio-permissions.rule


####                           Indi - webmanager                            ####
#sudo -u ${username} bash --rcfile $userhome/.bashrc -ci "pip3 install indiweb==0.1.8"
su - ${username} -c "BASH_ENV=$userhome/.nibashrc bash -c 'pip3 install indiweb==0.2.0'"
su - ${username} -c "BASH_ENV=$userhome/.nibashrc bash -c 'pip3 install indiweb==0.2.0'"
cp ${parent_path}/indiwebmanager*.service /etc/systemd/system/
for sfile in $(ls /etc/systemd/system/indiwebmanager*.service);
do
  service_file_path=${sfile}
  chmod 0755 ${service_file_path}
  # changed default sed separator from / to ~
  sed -i "s~LOCAL_USER_NAME~${username}~g" ${service_file_path}
  sed -i "s~LOCAL_INSTALL_PATH~${parent_path}~g" ${service_file_path}
  systemctl daemon-reload
  systemctl enable ${service_file_path}
done
#All systemctl enable does is create symlinks from /usr/lib/systemd/system/ or /etc/systemd/system/ to the appropriate target directories in /etc/systemd/system/, with services in the latter directory overriding ones in the former.


####                               OpenPHD2                                 ####
cp ${parent_path}/phd2.service /etc/systemd/system/
service_file_path=/etc/systemd/system/phd2.service
chmod 0755 ${service_file_path}
# changed default sed separator from / to ~
sed -i "s~LOCAL_USER_NAME~${username}~g" ${service_file_path}
sed -i "s~LOCAL_INSTALL_PATH~${parent_path}~g" ${service_file_path}
systemctl daemon-reload
systemctl enable ${service_file_path}

####    MQTT - TIG stack - Docker compose service definition and startup    ####
# Make sure all path are correct for local config
#echo "LOCAL_INSTALL_PATH=${parent_path}" >> ${env_file_path}
sed -i "s~LOCAL_INSTALL_PATH~${parent_path}~g" ${env_file_path}
cp ${parent_path}/observatory.service /etc/systemd/system/
service_file_path=/etc/systemd/system/observatory.service
# changed default sed separator from / to ~
sed -i "s~LOCAL_USER_NAME~${username}~g" ${service_file_path}
sed -i "s~LOCAL_INSTALL_PATH~${parent_path}~g" ${service_file_path}
sed -i "s~NIBASHRC_PATH~${userhome}/.nibashrc~g" ${service_file_path}
chmod 0755 ${service_file_path}
chmod a+x ${parent_path}/influxdb/scripts/init.sh #influxdb specific
systemctl daemon-reload
systemctl enable ${service_file_path}

# config files for influxdb: enable REST API
# sample taken from https://github.com/influxdata/influxdb/blob/1.8/etc/config.sample.toml
# with some modifications in the [http] section
# Also check the doc for more info: https://docs.influxdata.com/influxdb/v1.8/query_language/manage-database/
#cp $parent_path/influxdb.conf /etc/influxdb/influxdb.conf
#systemctl restart influxdb.service
#curl -XPOST 'http://localhost:8086/query' --data-urlencode 'q=CREATE DATABASE "telegraf"'
#curl -XPOST 'http://localhost:8086/query' --data-urlencode 'q=CREATE USER "telegrafuser" WITH PASSWORD "Telegr@f"'
#curl -XPOST 'http://localhost:8086/query' --data-urlencode 'q=GRANT ALL ON "telegraf" TO "telegrafuser"'
#curl -XPOST 'http://localhost:8086/query' --data-urlencode 'q=CREATE RETENTION POLICY "52Weeks" ON "telegraf" DURATION 52w REPLICATION 1'

# config files for telegraf: influxdb
#cp $parent_path/telegraf.conf /etc/telegraf/telegraf.conf
chmod a+x ${parent_path}/telegraf/scripts/*.sh
#systemctl reload telegraf.service

# config files for telegraf: local computer info capture
#usermod -a -G video telegraf
#cp $parent_path/telegraf_capture.conf /etc/telegraf/telegraf.d/telegraf_capture.conf
#systemctl reload telegraf.service

# Grafana
# Open the following URL in your webbrowser: http://IP_OBSERVATORY:3000 to reach the login screen.
# The default credentials admin / admin must be changed at first login.
# From the Grafana frontend. To add the first dashboard, mouse over the + just below the Grafana Search at the main page and choose Import. Enter the ID 10578 and Load.

# Download all dockers dependencies
su - ${username} -c "BASH_ENV=$userhome/.nibashrc bash -c 'docker compose pull influxdb  -f ${parent_path}/docker-compose.yml'"
su - ${username} -c "BASH_ENV=$userhome/.nibashrc bash -c 'docker compose pull mosquitto -f ${parent_path}/docker-compose.yml'"
su - ${username} -c "BASH_ENV=$userhome/.nibashrc bash -c 'docker compose pull telegraf  -f ${parent_path}/docker-compose.yml'"
su - ${username} -c "BASH_ENV=$userhome/.nibashrc bash -c 'docker compose pull grafana   -f ${parent_path}/docker-compose.yml'"

# Final operations, cleanup/anything done after download and file changes are over
# provide access to all those file to user
chown -R ${username}:${username} ${parent_path}
# Sorry but I didn't found any easy and robust way to remap internal docker users ids onto local ${username} id
chmod -R o+rwX ${parent_path}
## Now repair network conf
#dpkg-reconfigure resolvconf --frontend=noninteractive
