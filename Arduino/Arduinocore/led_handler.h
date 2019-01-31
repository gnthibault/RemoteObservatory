// Standard
#include <stdint.h> 

class LedHandler {
  public:
    LedHandler(uint32_t milli_delay=1000, uint8_t pin=LED_BUILTIN);
    void init();
    void update();
    void setValue(int value);
  protected:
    uint8_t pin_;
    uint32_t milli_delay_;
    uint32_t next_change_ms_ = 0;
};
