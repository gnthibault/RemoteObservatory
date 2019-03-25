// Arduino
#include <Arduino.h>

// Local
#include "led_handler.h"
#include "PinUtils.h"

LedHandler::LedHandler(uint32_t milli_delay, uint8_t pin):
  milli_delay_(milli_delay), pin_(pin) {}

void LedHandler::init() {
  pinMode(pin_, OUTPUT);
  digitalWrite(pin_, false);

  // Provide a visible signal that setup has been entered.
  if (Serial) {
    // 2 seconds of fast blinks.
    for (int i = 0; i < 40; ++i) {
      delay(50);
      toggle_led();
    }
  } else {
    // 2 seconds of slow blinks.
    for (int i = 0; i < 10; ++i) {
      delay(200);
      toggle_led();
    }
  }
}

void LedHandler::update() {
  unsigned long now = millis();
  if (next_change_ms_ <= now) {
    toggle_led();
    next_change_ms_ += (Serial ? milli_delay_ : milli_delay_);
    if (next_change_ms_ <= now) {
      next_change_ms_ = now;
    }
  }
}

void LedHandler::setValue(int value) {
  if (value == 0) {
    turn_pin_off(pin_);
  } else {
    turn_pin_on(pin_);
  }
}

void LedHandler::collect() {
}

void LedHandler::report() {
  int value = 0; //TODO TN
  Serial.print("{\"name\":\"led_handler\", \"pin_number\": \"");
  Serial.print(pin_);
  Serial.print(" , \"pin_value\": ");
  Serial.print(value);
  Serial.println("\"}");
}
