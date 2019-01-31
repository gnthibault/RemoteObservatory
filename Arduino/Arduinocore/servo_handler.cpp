
// Local
#include "servo_handler.h"

ServoHandler::ServoHandler(uint8_t pin) : pin_(pin), servo_() {}


void ServoHandler::init() {
  servo_.attach(pin_);
}

void ServoHandler::setValue(int value) {
  // Value should be in between 0 and 180
  servo_.write(value);
}

