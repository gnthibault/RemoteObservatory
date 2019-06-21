#!/bin/bash

#APP=Controller
APP=Firmata
#APP=blinkLED
in="./build/$APP/$APP"
out="./build/$APP/$APP.hex"

# If arduino uno, think about sudo adduser $USER dialout
tty=$(ls /dev/ttyACM*)
#tty=/dev/arduino
device=m328p
baud=115200

# If arduino nano
#tty=/dev/arduino
#device=m328
#baud=57600

avr-objcopy -O ihex -R .eeprom $in $out
avrdude -V -carduino -p$device -b$baud -P $tty -D -Uflash:w:$out:i \
  -C ./avrdude.conf
#avrdude -V -carduino -pATmega328P -b57600 -P $tty -D -Uflash:w:$out:i \

