#!/bin/bash

in="./build/Controller/Controller"
out="./build/Controller/Controller.hex"
tty=$(ls /dev/ttyACM*)
avr-objcopy -O ihex -R .eeprom $in $out
avrdude -V -carduino -patmega328p -b115200 -P $tty -D -Uflash:w:$out:i \
  -C ./avrdude.conf
