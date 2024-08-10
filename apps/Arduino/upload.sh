#!/bin/bash

#APP=Controller
APP=Firmata
#APP=blinkLED
in="./build/$APP/$APP"
out="./build/$APP/$APP.hex"

# If arduino uno, think about sudo adduser $USER dialout
#tty=$(ls /dev/ttyACM*)
#tty=/dev/arduino
#device=m328p
#baud=115200

# If arduino nano
tty=$(ls /dev/ttyUSB*)
#tty=/dev/arduino
device=ATmega328P
#device=m328p
baud=115200

avr-objcopy -O ihex -R .eeprom $in $out
avrdude -V -carduino -p$device -b$baud -P $tty -D -Uflash:w:$out:i \
  -C ./avrdude.conf
#avrdude -V -carduino -pATmega328P -b57600 -P $tty -D -Uflash:w:$out:i \

