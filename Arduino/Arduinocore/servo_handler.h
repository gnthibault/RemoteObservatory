// Arduino libs
#include <Servo.h>

class ServoHandler {
  public:
    ServoHandler(uint8_t pin, uint32_t min_pulse=0, uint32_t max_pulse=0);
    void init();
    void setValue(int value);

  protected:
    uint8_t pin_;
    Servo servo_; 
    uint32_t min_pulse_;
    uint32_t max_pulse_;
};
