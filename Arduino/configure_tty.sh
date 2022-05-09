#!/bin/bash
tty=$(ls /dev/ttyUSB*)
stty -F $tty ispeed 9600 ospeed 9600 -ignpar cs8 -cstopb -echo
# might also use screen $(ls /dev/ttyACM*) for interactive session
