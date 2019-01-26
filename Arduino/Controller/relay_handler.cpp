
// Arduino libs

// Local
#include "relay_handler.h"

RelayHandler::RelayHandler(uint8_t pin, const char* name) :
  pin_(pin), status_(false), name_(name) {}

void RelayHandler::Init() {
  pinMode(this->pin_, OUTPUT);
}

void RelayHandler::setValue(int value) {
  if (value==0) {
    digitalWrite(this->pin_, LOW);
  } else {
    digitalWrite(this->pin_, HIGH);
  }
}

void RelayHandler::Collect() {
  status_ = digitalRead(this->pin_);
}

void RelayHandler::Report() {
  Serial.print(", \"name_\":"); //TODO TN
  Serial.print(status_);
}
