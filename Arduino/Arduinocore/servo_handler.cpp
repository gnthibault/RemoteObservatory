
// Local
#include "servo_handler.h"

ServoHandler::ServoHandler(uint8_t pin, uint32_t min_pulse,
                           uint32_t max_pulse) :
  pin_(pin), servo_(), min_pulse_(min_pulse), max_pulse_(max_pulse) {}


void ServoHandler::init() {
  if ((min_pulse_==0) || (max_pulse_==0)) {
    servo_.attach(pin_);
  } else {
    servo_.attach(pin_, min_pulse_, max_pulse_);
  }
}

void ServoHandler::setValue(int value) {
  // Value should be in between 0 and 180
  servo_.write(value);
  //servo_.writeMicroseconds(value);
}

