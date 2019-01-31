
in="./build/blinkLED/blinkLED"
out="./build/blinkLED/blinkLED.hex"
tty=$(ls /dev/ttyACM*)
hex='/tmp/arduino_build_338045/blinkLED.ino.hex'
avrdude -V -q -q -carduino -patmega328p -b115200 -P $tty -D -Uflash:w:$out:i \
  -C ./avrdude.conf
