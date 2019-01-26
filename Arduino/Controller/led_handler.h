class LedHandler {
  public:
    LedHandler();
    void init();
    void update();
    void setValue(int value);
  protected:
    unsigned long next_change_ms_ = 0;
};
