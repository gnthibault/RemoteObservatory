#!/bin/bash

#APP=Controller
APP=Firmata
in="./build/$APP/$APP"
out="./build/$APP/$APP.hex"
#tty=$(ls /dev/ttyACM*)
tty=/dev/arduino
avr-objcopy -O ihex -R .eeprom $in $out
avrdude -V -carduino -pm328p -b115200 -P $tty -D -Uflash:w:$out:i \
#avrdude -V -carduino -pATmega328P -b57600 -P $tty -D -Uflash:w:$out:i \
#  -C ./avrdude.conf
