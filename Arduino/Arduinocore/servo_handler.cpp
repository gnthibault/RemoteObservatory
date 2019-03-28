// Arduino
#include <Arduino.h>

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

void ServoHandler::setValue(uint32_t value) {
  // Value should be in between 0 and 180
  servo_.write(value);
  // Instead of collecting the value of the pin, we save it in the object
  value_ = value;
  //servo_.writeMicroseconds(value);
}

void ServoHandler::collect() {
}

void ServoHandler::report() {
  Serial.print("{\"name\":\"servo_handler\", \"pin_number\": \"");
  Serial.print(pin_);
  Serial.print("\" , \"pin_value\": \"");
  Serial.print(value_);
  Serial.print("\"}");
}
