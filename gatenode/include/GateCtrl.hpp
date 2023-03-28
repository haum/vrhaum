#ifndef GATECTRL_HPP
#define GATECTRL_HPP

#include <GateHw.hpp>
#include <ESP8266WiFi.h>

class GateCtrl {
	private:
		GateHw _gate;
		WiFiServer _server{23};
		WiFiClient _client;

		struct Config {
			char header[9] = "GateNode";
			uint8_t version = 1;
			char name[17] = "";
			uint8_t code = 0x42;

			Config & operator=(const Config &) = default;
		} _config;

		void setConfig(const Config & c);
		void useDefaultConfig();
		void setConfigNameMAC();

		void printCode(Stream &);

	public:
		void init();
		void loop();
		Stream & log();

		void setConfigName(String name);
		const char * configName();
		String hostname();
		void setConfigCode(uint8_t code);
		const uint8_t configCode() const;
		void saveConfig();
};

#endif
