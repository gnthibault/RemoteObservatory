# include our arduino tools
include_directories(${ArduinoCode_SOURCE_DIR}/Arduinocore)
LINK_DIRECTORIES(${ArduinoCode_SOURCE_DIR}/Arduinocore)
link_libraries(Arduinocore)
add_executable(Controller Controller.cc)
