// Standard
#include <stdint.h> 

class RelayHandler {
  public:
    RelayHandler(uint8_t pin, const char* name);
    void init();
    void setValue(int value);
    void collect();
    void report();
  protected:
    uint8_t pin_;
    bool status_;
    const char* name_;
};
