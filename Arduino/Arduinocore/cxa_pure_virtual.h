//http://zedcode.blogspot.com/2007/02/gcc-c-link-problems-on-small-embedded.html
//to keep from needing to link to c++ std lib, maybe? not totally sure
// solves this error:
//../../libarduino/libarduinocore.a(Print.o):(.data+0x6): undefined reference to `__cxa_pure_virtual'
extern "C" void __cxa_pure_virtual(void)
{
	// call to a pure virtual function happened ... wow, should never happen ... stop
	for(;;)
	{

	}
}

