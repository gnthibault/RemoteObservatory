
// Arduino libs
#include <Arduino.h>

// Local
#include "relay_handler.h"

RelayHandler::RelayHandler(uint8_t pin, const char* name) :
  pin_(pin), name_(name), status_(false) {}

void RelayHandler::init() {
  pinMode(this->pin_, OUTPUT);
}

void RelayHandler::setValue(int value) {
  if (value==0) {
    digitalWrite(this->pin_, LOW);
  } else {
    digitalWrite(this->pin_, HIGH);
  }
}

void RelayHandler::collect() {
  status_ = digitalRead(this->pin_);
}

void RelayHandler::report() {
  Serial.print(", \"name_\":"); //TODO TN
  Serial.print(status_);
}
