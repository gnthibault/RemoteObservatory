// Standard C stuff
#include <stdlib.h>

// Arduino lib

// Local helpers
//#include "dht_handler.h"
//#include "led_handler.h"
//#include "relay_handler.h"
//#include "servo_handler.h"

// DHT22 temperature sensor
#define DHTTYPE DHT22       // DHT 22  (AM2302)
const int DHT_SCOPE_PIN = 0;//secondary mirror temperature
const int DHT_AIR_PIN   = 0;//outside air temperature
const int DHT_BOX_PIN   = 0;//control box temperature

// Relay
const int SCOPE_DEW_HEAT_RELAY  = 0;//main telescope dew heater
const int FINDER_DEW_HEAT_RELAY = 0;//finderscope dew heater
const int CAMERA_RELAY          = 0;//EOS camera power supply

// PWMs
const int SCOPE_SERVO_DUSTCAP  = 0;//main telescope dustcap
const int FINDER_SERVO_DUSTCAP = 0;//finderscope dustcap

// Timers
unsigned long end_setup_millis;
unsigned long next_report_millis;
constexpr int interval = 1000;
int report_num = 0;

// Names, to be used in Serial communications
const char* relay_cam_name = "camera_00";
const char* relay_scope_name = "scope_dew";
const char* relay_finder_name = "finder_dew";
const char* dht_scope_name = "scope";
const char* dht_air_name = "air";
const char* dht_box_name = "box";

// Declare main "devices"
//DHTHandler dht_air_handler(DHT_AIR_PIN, DHTTYPE, dht_air_name);
//DHTHandler dht_box_handler(DHT_BOX_PIN, DHTTYPE, dht_box_name);
//DHTHandler dht_scope_handler(DHT_SCOPE_PIN, DHTTYPE, dht_scope_name);
//LedHandler led_handler;
//RelayHandler relay_scope_dew_handler(SCOPE_DEW_HEAT_RELAY, relay_scope_name);
//RelayHandler relay_finder_dew_handler(FINDER_DEW_HEAT_RELAY, relay_finder_name);
//RelayHandler relay_camera_handler(CAMERA_RELAY, relay_cam_name);
//ServoHandler servo_scope_dustcap(SCOPE_SERVO_DUSTCAP);
//ServoHandler servo_finder_dustcap(FINDER_SERVO_DUSTCAP);

void setup() {
  Serial.begin(9600);
  Serial.flush();

  // Init devices
  //dht_air_handler.Init();
  //dht_box_handler.Init();
  //dht_scope_handler.Init();
  //led_handler.Init();
  //relay_scope_dew_handler.Init();
  //relay_finder_dew_handler.Init();
  //relay_camera_handler.Init();
  //servo_scope_dustcap.Init();
  //servo_finder_dustcap.Init();

  Serial.println("EXIT setup()");
  next_report_millis = end_setup_millis = millis();
}

void loop() {
  led_handler.update();
  if (Serial) {
    main_loop();
  }
}

void main_loop() {
  unsigned long now = millis();
  if (next_report_millis <= now) {
    // Schedule the next report for `interval' milliseconds from the last
    // report unless we've fallen behind.
    next_report_millis += interval;
    if (next_report_millis <= now) {
      next_report_millis = now + interval;
    }

    // Collect the data. Since some of these operations take a while, keep
    // updating the LEDs appropriately.
    // TODO TN: Could probably be done with an interrupt handler instead.
    report_num++;
    dht_air_handler.Collect();
    dht_box_handler.Collect();
    dht_scope_handler.Collect();
    relay_scope_dew_handler.Collect();
    relay_finder_dew_handler.Collect();
    relay_camera_handler.Collect();
    bool cam_relay_stat = digitalRead(CAMERA_RELAY);

    // Format/output the results.
    Serial.print("{\"name\":\"camera_board\", \"count\":");
    Serial.print(millis() - end_setup_millis);
    Serial.print(", \"num\":");
    Serial.print(report_num);
    Serial.print(", \"inputs_received\":");
    Serial.print(inputs);

    // output reports
    //dht_air_handler.Report();
    //dht_box_handler.Report();
    //dht_scope_handler.Report();
    //relay_scope_dew_handler.Report();
    //relay_finder_dew_handler.Report();
    //relay_camera_handler.Report();

    Serial.println("}");
    Serial.flush();
  }

  // Read any serial input
  //    - Input will be two integers (with anything in between them), the
  //      first specifying the pin and the second the status
  //      to change to (1/0).
  //      Example serial input:
  //           5,1   # put pin 5 to on
  //           6,0   # put pin 6 to off
  while (Serial.available() > 0) {
    inputs++;
    int pin_num = Serial.parseInt();
    int pin_status = Serial.parseInt();

    switch (pin_num) {
      case LED_BUILTIN:
        //led_handler.setValue(pin_status);
      case SCOPE_DEW_HEAT_RELAY:
        //relay_scope_dew_handler.setValue(pin_status);
      case FINDER_DEW_HEAT_RELAY:
        //relay_finder_dew_handler.setValue(pin_status);
      case CAMERA_RELAY:
        //relay_camer_handler.setValue(pin_status);
      case SCOPE_SERVO_DUSTCAP:
        //servo_scope_dustcap.setValue(pin_status);
      case FINDER_SERVO_DUSTCAP:
        //servo_finder_dustcap.setValue(pin_status);
        break;
    }
  }
)
