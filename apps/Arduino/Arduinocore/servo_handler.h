// Arduino libs
#include <Servo.h>

class ServoHandler {
  public:
    ServoHandler(uint8_t pin, uint32_t min_pulse=0, uint32_t max_pulse=0);

    // The setup routine, attaching servo with pulse config
    void init();

    // Actuation
    void setValue(uint32_t value);

    // Read the current value (do nothing)
    void collect();

    // Print the values. Requires that Collect has been called.
    void report();

  protected:
    uint8_t pin_;
    Servo servo_;
    uint32_t min_pulse_;
    uint32_t max_pulse_;
    uint32_t value_;
};
