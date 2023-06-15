#ifndef RESOURCES_ARDUINO_FILES_SHARED_DHT_HANDLER_H
#define RESOURCES_ARDUINO_FILES_SHARED_DHT_HANDLER_H

// Standard C library
#include <stdlib.h>

// Local helpers
#include "DHT.h"

// Reads and reports Humidity & Temperature values.
class DHTHandler {
  public:
    DHTHandler(uint8_t pin, uint8_t type, const char* name);

    // Initialize communication to the sensor.
    void init();

    // Read the current values from the sensor.
    void collect();

    // Print the values. Requires that Collect has been called.
    void report();

    float getHumidity() const { return humidity_; }
    float getTemperature() const { return temperature_; }

  protected:
    DHT dht_;
    float humidity_;
    float temperature_;  // Celcius
    const char* name_;
};

#endif  // RESOURCES_ARDUINO_FILES_SHARED_DHT_HANDLER_H
