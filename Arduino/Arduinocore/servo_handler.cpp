
// Arduino libs
#include <Servo.h>

// Local
#include "servo_handler.h"

ServoHandler::ServoHandler(uint8_t pin) : pin_(pin), servo_() {}


void ServoHandler::init() {
  servo_.attach(pin_);
}

void ServoHandler::setValue(int value) {
  servo_.write(value);
}

