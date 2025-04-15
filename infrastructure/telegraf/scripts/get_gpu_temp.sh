#!/bin/bash
cpu=$(cat /hostfs/sys/class/thermal/cooling_device0/cur_stat)
temp=cpu
#cpu=$(</sys/class/thermal/thermal_zone2/temp)
#temp=$((cpu/1000))
#export LD_LIBRARY_PATH=/hostfs/usr/lib/aarch64-linux-gnu
#temp=$(/hostfs/bin/bc -l <<< "scale=2; $cpu/1000")
#export LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu
echo $temp

