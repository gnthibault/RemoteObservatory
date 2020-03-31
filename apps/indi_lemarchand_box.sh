#!/bin/bash

# First: setup a fifo to launch drivers on demand
rm -rf /tmp/INDI_FIFO
mkfifo /tmp/INDI_FIFO

# Launch indiserver
LD_LIBRARY_PATH=/usr/local/lib/:$LD_LIBRARY_PATH indiserver -f /tmp/INDI_FIFO &

# Start Scope controller which is the most useful driver (other are launched on demand)
echo "start /usr/local/bin/indi_duino -s \"/home/rock/projects/RemoteObservatory/conf_files/indi_driver_conf/scope_controller_sk.xml\"" > /tmp/INDI_FIFO
#echo "stop /usr/local/bin/indi_duino" > /tmp/INDI_FIFO

# Start ASI camera driver for autoguiding
echo "start /usr/local/bin/indi_asi_ccd" > /tmp/INDI_FIFO
#echo "stop /usr/local/bin/indi_asi_ccd" > /tmp/INDI_FIFO

# Start mount on demand ?
sudo ifconfig eth0 192.168.1.1
echo "start /usr/local/bin/indi_lx200generic -n \"Losmandy Gemini\"" > /tmp/INDI_FIFO
#echo "stop /usr/local/bin/indi_lx200generic" > /tmp/INDI_FIFO

# Start aag cloudwatcher
#echo "start /usr/local/bin/indi_aagcloudwatcher_ng -c \"/home/rock/projects/RemoteObservatory/conf_files/indi_driver_conf/indi_aagcloudwatcher_ng.xml\" -s \"/home/rock/projects/RemoteObservatory/conf_files/indi_driver_conf/indi_aagcloudwatcher_ng_sk.xml\"" > /tmp/INDI_FIFO# Start indi gphoto_ccd on demand
#echo "stop /usr/local/bin/indi_aagcloudwatcher_ng" > /tmp/INDI_FIFO

# Same but not the buggy ng version
echo "start /usr/local/bin/indi_aagcloudwatcher" > /tmp/INDI_FIFO
#echo "stop /usr/local/bin/indi_aagcloudwatcher" > /tmp/INDI_FIFO

#echo "start /usr/local/bin/indi_gphoto_ccd" > /tmp/INDI_FIFO
#echo "stop /usr/local/bin/indi_gphoto_ccd" > /tmp/INDI_FIFO 
