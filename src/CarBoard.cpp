#include <CarBoard.hpp>

#include <ESP8266WiFi.h>

namespace {
	constexpr const int PIN_DEBUG_RX = 3;
	constexpr const int PIN_DEBUG_TX = 1;
	constexpr const int PIN_THROTTLE = 14;
	constexpr const int PIN_STEERING = 0;
	constexpr const int PIN_HEADLIGHTS = 12;

	SoftwareSerial debugSerial(PIN_DEBUG_RX, PIN_DEBUG_TX);
};

void CarBoard::init() {
	_throttleServo.attach(PIN_THROTTLE);
	setThrottle(0);

	_steeringServo.attach(PIN_STEERING);
	setSteering(0);

	pinMode(PIN_HEADLIGHTS, OUTPUT);
	setHeadlights(0);

	EEPROM.begin(256);

	Serial.begin(115200);
	Serial.swap(); // Change uart mux
	U0C0 |= BIT(UCTXI); // Invert TX signal

	debugSerial.begin(76800);
	debugSerial.println("CarInSitu");
}

void CarBoard::loop() {
}

std::array<uint8_t, 6> CarBoard::mac() const {
	std::array<uint8_t, 6> ret;
	WiFi.macAddress(ret.data());
	return ret;
}

Stream & CarBoard::debug_serial() const {
	return debugSerial;
}

void CarBoard::setSteering(int16_t i_angle) {
	const int16_t value = map(i_angle, -32768, 32767, 1000, 2000);
	_steeringServo.writeMicroseconds(value);
}

void CarBoard::setThrottle(int16_t i_speed) {
	const int16_t value = (i_speed > 0) ? map(i_speed, 0, 32767, 1576, 2000) :
	                      (i_speed < 0) ? map(i_speed, -32768, 0, 1000, 1423) :
	                      1500;
	_throttleServo.writeMicroseconds(value);
}

void CarBoard::setHeadlights(uint16_t i_pwr) {
	const uint8_t value = map(i_pwr, 0, 65535, 0, 255);
	analogWrite(PIN_HEADLIGHTS, value);
}

void CarBoard::setColor(uint8_t r, uint8_t g, uint8_t b) {
}
