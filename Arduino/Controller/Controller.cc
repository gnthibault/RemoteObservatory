// Standard C stuff
#include <stdlib.h>

// Arduino lib
#include <Arduino.h>

// Local helpers
#include <cxa_pure_virtual.h>
//#include "dht_handler.h"
#include "led_handler.h"
#include "relay_handler.h"
#include "servo_handler.h"

// DHT22 temperature sensor
#define DHTTYPE DHT22       // DHT 22  (AM2302)
const int DHT_SCOPE_PIN = 0;//secondary mirror temperature
const int DHT_AIR_PIN   = 1;//outside air temperature
const int DHT_BOX_PIN   = 2;//control box temperature

// Relay
const int SCOPE_DEW_HEAT_RELAY  = 11;//main telescope dew heater
const int FINDER_DEW_HEAT_RELAY = 4;//finderscope dew heater
const int CAMERA_RELAY          = 5;//EOS camera power supply
const int SCOPE_FAN_RELAY       = 6;//main telescope prim. mirror fans

// PWM/SERVO
const int SCOPE_SERVO_DUSTCAP  = 9;    //main telescope dustcap
const int SCOPE_SERVO_MIN_PULSE = 780; //For futaba S3050
const int SCOPE_SERVO_MAX_PULSE = 2180;//For futaba S3050
const int FINDER_SERVO_DUSTCAP = 10;   //finderscope dustcap
const int FINDER_SERVO_MIN_PULSE = 550; //For futaba S3003
const int FINDER_SERVO_MAX_PULSE = 2350;//For futaba S3003

// Timers, interval between reports
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
//RelayHandler relay_gpu_dew_handler(GPU_DEW_HEAT_RELAY, relay_gpu_name);
//RelayHandler relay_camera_handler(CAMERA_RELAY, relay_cam_name);
//RelayHandler relay_scope_fan_handler(SCOPE_FAN_RELAY, relay_cam_name);
ServoHandler servo_scope_dustcap(SCOPE_SERVO_DUSTCAP, SCOPE_SERVO_MIN_PULSE,
                                 SCOPE_SERVO_MAX_PULSE);
//ServoHandler servo_finder_dustcap(FINDER_SERVO_DUSTCAP, FINDER_SERVO_MIN_PULSE,
//                                  FINDER_SERVO_MAX_PULSE);

// We have a simple state machine for order processing protocol, TBD better
String protocolString;
int pin_num;
int pin_status;
//0 is nothing received, 1 in pin_num received, and 2 is ready to process
int state;

void process_order(int pin_num, int pin_status) {
  switch (pin_num) {
    case LED_BUILTIN:
      led_handler.setValue(pin_status);
      break;
    case SCOPE_DEW_HEAT_RELAY:
      //relay_scope_dew_handler.setValue(pin_status);
      break;
    case FINDER_DEW_HEAT_RELAY:
      //relay_finder_dew_handler.setValue(pin_status);
      break;
    case CAMERA_RELAY:
      //relay_camer_handler.setValue(pin_status);
      break;
    case SCOPE_SERVO_DUSTCAP:
      // Value between 0 and 180
      servo_scope_dustcap.setValue(pin_status);
      break;
    case FINDER_SERVO_DUSTCAP:
      // Value between 0 and 180
      //servo_finder_dustcap.setValue(pin_status);
      break;
    default:
      Serial.print("Invalid pin id: ");
      Serial.println(pin_num);
      break;
  }
}

void setup() {
  Serial.begin(9600);//115200 TODO TN
  Serial.flush();

  // Init devices
  //dht_air_handler.init();
  //dht_box_handler.init();
  //dht_scope_handler.init();
  led_handler.init();
  //relay_scope_dew_handler.init();
  //relay_finder_dew_handler.init();
  //relay_gpu_dew_handler.init();
  //relay_camera_handler.init();
  //relay_scope_fan_handler.init();
  servo_scope_dustcap.init();
  //servo_finder_dustcap.init();

  // Initialize simple state machine for command processing
  pin_num = 0;
  pin_status = 0;
  state = 0;

  // Initialize timing stuff
  next_report_millis = end_setup_millis = millis();

  // Outro
  Serial.println("EXIT setup()");
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
    //relay_gpu_dew_handler.collect();
    //relay_camera_handler.collect();
    //bool cam_relay_stat = digitalRead(CAMERA_RELAY);

    // Format/output the results: main entry: 
    Serial.print("{\"name\":\"scope_controller\", \"uptime\": \"");
    Serial.print((millis() - end_setup_millis)/1000);
    Serial.print("s\" , \"num\":\"");
    Serial.print(report_num);
    Serial.print("\", \"devices\": [");

    // Then each device report its own status
    //dht_air_handler.report();
    //dht_box_handler.report();
    //dht_scope_handler.report();
    led_handler.report();
    //relay_scope_dew_handler.report();
    //relay_finder_dew_handler.report();
    //relay_gpu_dew_handler.report();
    //relay_camera_handler.report();

    Serial.println("]}");
  }

  // Read any serial input
  //    - Input will be two integers (with, in between them), the
  //      first specifying the pin and the second the status
  //      to change to (1/0).
  //      Example serial input:
  //           5,1   # put pin 5 to on
  //           6,0   # put pin 6 to off
  while (Serial.available()) {
    char c = Serial.read();  //gets one byte from serial buffer
    switch(c) {
      case '\n' :
        if (protocolString.length() > 0) {
          //Serial.println(protocolString);
          pin_status = protocolString.toInt();
          if (state == 1) {
            state = 2;
          }
        }
        if (state == 2) {
          //Serial.print("pin_num was ");
          //Serial.print(pin_num);
          //Serial.print(" and status was ");
          //Serial.println(pin_status);
          process_order(pin_num, pin_status);
        }
        protocolString = ""; //clears variable for new input
        state = 0;           //reset statemachine state
        break;
      case ',' :
        if (protocolString.length() > 0) {
          //Serial.println(protocolString);
          pin_num = protocolString.toInt();
          if (state == 0) {
            state = 1;
          } else {
            state = 0;
          }
        } else {
          state = 0;
        }
        protocolString = ""; //clears variable for new input
        break;
      default:
        protocolString += c;
        //Serial.println(protocolString);
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
  return EXIT_SUCCESS;
}

