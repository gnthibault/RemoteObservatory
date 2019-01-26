class RelayHandler {
  public:
    RelayHandler(uint8_t pin, const char* name);
    void Init();
    void setValue(int value);
    void Collect();
    void Report();
  protected:
    uint8_t pin_;
    bool status_;
    const char* name_;
};
