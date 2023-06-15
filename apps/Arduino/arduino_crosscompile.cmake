SET(CMAKE_SYSTEM_NAME Generic)

SET(CMAKE_C_COMPILER avr-gcc)
SET(CMAKE_CXX_COMPILER avr-g++)

SET(CSTANDARD "-std=gnu99")
SET(CDEBUG "-gstabs")
SET(CWARN "-Wall -Wstrict-prototypes")
SET(CARCH  "-DARDUINO_ARCH_AVR")
SET(CTUNING "-w -Wl,--gc-sections")
#SET(CTUNING "-w -flto -fno-use-linker-plugin -Wl,--gc-sections")
#SET(CTUNING "-w -flto -fuse-linker-plugin -Wl,--gc-sections")
SET(CPPTUNING "-std=gnu++11 -fpermissive -fno-exceptions -ffunction-sections -fdata-sections -fno-threadsafe-statics -Wno-error=narrowing -w -CC")
#SET(CPPTUNING "-std=gnu++11 -fpermissive -fno-exceptions -ffunction-sections -fdata-sections -fno-threadsafe-statics -Wno-error=narrowing -flto -fno-use-linker-plugin -w -CC")
#SET(CPPTUNING "-std=gnu++11 -fpermissive -fno-exceptions -ffunction-sections -fdata-sections -fno-threadsafe-statics -Wno-error=narrowing -flto -w -CC")
SET(COPT "-Os")

SET(CINCS "-I${ARDUINO_BASE_DIR}/Arduinocore\
           -I${ARDUINO_SDK_PATH}/hardware/arduino/avr/cores/arduino\
           -I${ARDUINO_SDK_PATH}/hardware/arduino/avr/libraries/Wire/src\
           -I${ARDUINO_SDK_PATH}/hardware/arduino/avr/variants/standard\
           -I${ARDUINO_SDK_PATH}/libraries/Firmata\
           -I${ARDUINO_SDK_PATH}/libraries/Servo/src")
SET(CMCU "-mmcu=atmega328p")
SET(CDEFS "-DF_CPU=16000000L -DARDUINO=10808 -DARDUINO_AVR_UNO")

#SET(LINKERFLAGS "-flto")
SET(LINKERFLAGS)
SET(CFLAGS "${CMCU} ${CARCH} ${CDEBUG} ${CDEFS} ${CINCS} ${COPT} ${CTUNING} ${CWARN} ${CSTANDARD} ${CEXTRA}")
SET(CXXFLAGS "${CMCU} ${CARCH} ${CDEFS} ${CINCS} ${COPT} ${CPPTUNING}")

SET(CMAKE_C_FLAGS  ${CFLAGS})
SET(CMAKE_CXX_FLAGS ${CXXFLAGS})
SET(CMAKE_EXE_LINKER_FLAGS ${LINKERFLAGS})
