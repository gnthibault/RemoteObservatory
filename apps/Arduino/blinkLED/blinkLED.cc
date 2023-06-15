// Arduino stuff
#include <Arduino.h>

// Local stuff
#include <cxa_pure_virtual.h>

int main()
{
        init();
	Serial.begin(9600);
	pinMode(13, OUTPUT);
	for(;;)
	{
                int pin = HIGH; 
		Serial.println("Pure C");
		digitalWrite(13, pin);
		(pin == HIGH) ? (pin = LOW) : (pin = HIGH);
		delay(1000);
	}
	return 0;
}
