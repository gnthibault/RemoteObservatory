// Arduino libs
#include <Servo.h>

class ServoHandler {
  public:
    ServoHandler(uint8_t pin);
    void init();
    void setValue(int value);

  protected:
    uint8_t pin_;
    Servo servo_; 
};
