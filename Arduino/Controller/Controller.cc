// Standard C stuff
#include <stdlib.h>

// Arduino lib
#include <Arduino.h>

// Local helpers
#include <cxa_pure_virtual.h>
//#include "dht_handler.h"
#include "led_handler.h"
//#include "relay_handler.h"
//#include "servo_handler.h"

// DHT22 temperature sensor
#define DHTTYPE DHT22       // DHT 22  (AM2302)
const int DHT_SCOPE_PIN = 0;//secondary mirror temperature
const int DHT_AIR_PIN   = 1;//outside air temperature
const int DHT_BOX_PIN   = 2;//control box temperature

// Relay
const int SCOPE_DEW_HEAT_RELAY  = 3;//main telescope dew heater
const int FINDER_DEW_HEAT_RELAY = 4;//finderscope dew heater
const int CAMERA_RELAY          = 5;//EOS camera power supply
const int SCOPE_FAN_RELAY       = 6;//main telescope prim. mirror fans

// PWMs
const int SCOPE_SERVO_DUSTCAP  = 7;//main telescope dustcap
const int FINDER_SERVO_DUSTCAP = 8;//finderscope dustcap

// Timers
unsigned long end_setup_millis;
uint64_t next_report_millis;
const uint64_t interval = 1000;
unsigned int report_num = 0;

// Names, to be used in Serial communications
const char* relay_cam_name = "camera_0";
const char* relay_scope_name = "scope_dew";
const char* relay_finder_name = "finder_dew";
const char* relay_fan_name = "scope_fan";
const char* dht_scope_name = "scope";
const char* dht_air_name = "air";
const char* dht_box_name = "box";

// Declare main "devices"
//DHTHandler dht_air_handler(DHT_AIR_PIN, DHTTYPE, dht_air_name);
//DHTHandler dht_box_handler(DHT_BOX_PIN, DHTTYPE, dht_box_name);
//DHTHandler dht_scope_handler(DHT_SCOPE_PIN, DHTTYPE, dht_scope_name);
LedHandler led_handler;
//RelayHandler relay_scope_dew_handler(SCOPE_DEW_HEAT_RELAY, relay_scope_name);
//RelayHandler relay_finder_dew_handler(FINDER_DEW_HEAT_RELAY, relay_finder_name);
//RelayHandler relay_camera_handler(CAMERA_RELAY, relay_cam_name);
//RelayHandler relay_camera_handler(CAMERA_RELAY, relay_cam_name);
//ServoHandler servo_scope_dustcap(SCOPE_SERVO_DUSTCAP);
//ServoHandler servo_finder_dustcap(FINDER_SERVO_DUSTCAP);

void setup() {
  Serial.begin(9600);
  Serial.flush();

  // Init devices
  //dht_air_handler.init();
  //dht_box_handler.init();
  //dht_scope_handler.init();
  led_handler.init();
  //relay_scope_dew_handler.init();
  //relay_finder_dew_handler.init();
  //relay_camera_handler.init();
  //servo_scope_dustcap.init();
  //servo_finder_dustcap.init();

  Serial.println("EXIT setup()");
  next_report_millis = end_setup_millis = millis();
}


void main_loop() {
  uint64_t now = millis();
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
    //dht_air_handler.collect();
    //dht_box_handler.collect();
    //dht_scope_handler.collect();
    //relay_scope_dew_handler.collect();
    //relay_finder_dew_handler.collect();
    //relay_camera_handler.collect();
    //bool cam_relay_stat = digitalRead(CAMERA_RELAY);

    // Format/output the results: main entry: 
    Serial.print("{\"name\":\"scope_controller\", \"uptime\":");
    Serial.print((millis() - end_setup_millis)/1000);
    Serial.print("s , \"num\":");
    Serial.print(report_num);

    // Then each device report its own status
    //dht_air_handler.report();
    //dht_box_handler.report();
    //dht_scope_handler.report();
    //relay_scope_dew_handler.report();
    //relay_finder_dew_handler.report();
    //relay_camera_handler.report();

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
        Serial.print("pin_num was ");
        Serial.print(pin_num);
        Serial.print(" and status was ");
        Serial.print(pin_status);
        break;
    }
  }
}

int main() {
  init();
  setup();
  if (Serial) {
    for(;;) {
      main_loop();
    }
  }
}

