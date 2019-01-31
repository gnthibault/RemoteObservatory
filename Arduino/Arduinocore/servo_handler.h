class ServoHandler {
  public:
    ServoHandler(uint8_t pin);
    void Init();
    void setValue(int value);

  protected:
    uint8_t pin_;
    Servo servo_; 
};
