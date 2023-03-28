#ifndef WIFILINK_HPP
#define WIFILINK_HPP

#include <Stream.h>

class WifiLink {
	private:
		Stream & _log;
		uint8_t _last_status;

		void print_status();

	public:
		WifiLink(Stream & s) : _log(s) {}
		void init(const char* ssid, const char* pass, String hostname);
		void loop();
};

#endif
