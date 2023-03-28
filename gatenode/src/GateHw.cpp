#include <GateHw.hpp>

#include <Arduino.h>
#include <ESP8266WiFi.h>

void GateHw::init() {
	Serial.begin(76800);
	Serial.println("GateNode");
	EEPROM.begin(256);
	_ir_send.begin();
}

void GateHw::loop() {
	_ir_send.sendRC6(0xa00 | _ir_code, 12, 2);
}

std::array<uint8_t, 6> GateHw::mac() const {
	std::array<uint8_t, 6> ret;
	WiFi.macAddress(ret.data());
	return ret;
}

Stream & GateHw::serial() const {
	return Serial;
}

void GateHw::setIrCode(uint8_t code) {
	_ir_code = code;
}

uint8_t GateHw::getIrCode() const {
	return _ir_code;
}
