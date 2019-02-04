SET(CMAKE_SYSTEM_NAME Generic)

SET(CMAKE_C_COMPILER avr-gcc)
SET(CMAKE_CXX_COMPILER avr-g++)

SET(CSTANDARD "-std=gnu99")
SET(CDEBUG "-gstabs")
SET(CWARN "-Wall -Wstrict-prototypes")
SET(CARCH  "-DARDUINO_ARCH_AVR")
SET(CTUNING "-funsigned-char -funsigned-bitfields -fpack-struct -fshort-enums")
SET(COPT "-Os")
SET(CINCS "-I${ARDUINO_BASE_DIR}/Arduinocore\
           -I${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino\
           -I${ARDUINO_SDK_PATH}/hardware/arduino/avr/libraries/Wire/src\
           -I${ARDUINO_SDK_PATH}/hardware/arduino/avr/variants/standard\
           -I${ARDUINO_SDK_PATH}/libraries/Firmata\
           -I${ARDUINO_SDK_PATH}/libraries/Servo/src")
SET(CMCU "-mmcu=atmega168")
SET(CDEFS "-DF_CPU=16000000 -DARDUINO=106")


SET(CFLAGS "${CMCU} ${CARCH} ${CDEBUG} ${CDEFS} ${CINCS} ${COPT} ${CWARN} ${CSTANDARD} ${CEXTRA}")
SET(CXXFLAGS "${CMCU} ${CARCH} ${CDEFS} ${CINCS} ${COPT}")

SET(CMAKE_C_FLAGS  ${CFLAGS})
SET(CMAKE_CXX_FLAGS ${CXXFLAGS})
