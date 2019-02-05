# Make sure local directory is used as a search path for .h
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# Custom stuff
set(headers_arduino
  cxa_pure_virtual.h
  DHT.h
  dht_handler.h
  led_handler.h
  LM335.h
  Moonlite.h
  PinUtils.h
  relay_handler.h
  servo_handler.h
  StepperControl_A4988.h
)

set(sources_arduino
  DHT.cpp
  dht_handler.cpp
  led_handler.cpp
  LM335.cpp
  Moonlite.cpp
  PinUtils.cpp
  relay_handler.cpp
  servo_handler.cpp
  StepperControl_A4988.cpp
)

# Reference stuff
set(sources_official
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/HardwareSerial0.cpp
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/HardwareSerial.cpp
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/hooks.c
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/Print.cpp
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/Stream.cpp
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/wiring.c
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/wiring_analog.c
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/wiring_digital.c
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/wiring_pulse.c
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/wiring_shift.c
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/WMath.cpp
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino/WString.cpp
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/libraries/Wire/src/Wire.cpp
  ${ARDUINO_SDK_PATH}/hardware/arduino/avr/libraries/Wire/src/utility/twi.c
  ${ARDUINO_SDK_PATH}/libraries/Servo/src/avr/Servo.cpp
)

add_library(Arduinocore ${sources_arduino} ${sources_official})
