// Standard
#include <stdint.h> 

class LedHandler {
  public:
    LedHandler(uint32_t milli_delay=1000, uint8_t pin=LED_BUILTIN);

    // The setup routine, setting pinmode, etc...
    void init();

    // turn on if off, turn off if on
    void update();

    // Set actual value (0 or 1 basically) of led
    void setValue(int value);

    // Read the current values from the sensor.
    void collect();

    // Print the values. Requires that Collect has been called.
    void report();
  protected:
    uint8_t pin_;
    uint32_t milli_delay_;
    uint32_t next_change_ms_ = 0;
};
