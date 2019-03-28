// Arduino
#include <Arduino.h>

// Local
#include "relay_handler.h"

RelayHandler::RelayHandler(uint8_t pin, const char* name) :
  pin_(pin), name_(name), value_(false) {}

void RelayHandler::init() {
  pinMode(pin_, OUTPUT);
}

void RelayHandler::setValue(int value) {
  if (value==0) {
    digitalWrite(pin_, LOW);
  } else {
    digitalWrite(pin_, HIGH);
  }
}

void RelayHandler::collect() {
  value_ = digitalRead(pin_)==HIGH ? true : false;
}

void RelayHandler::report() {
  Serial.print(", \"name\": \"");
  Serial.print(name_);
  Serial.print("\" , \"pin_number\": \"");
  Serial.print(pin_);
  Serial.print("\" , \"pin_value\": \"");
  Serial.print(value_);
  Serial.print("\"}");
}
