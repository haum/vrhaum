#include <CarBoard.hpp>
#include <ImuLSM6DS3.hpp>

#include <ESP8266WiFi.h>
#include <NeoPixelBus.h>

namespace {
	constexpr const int PIN_DEBUG_RX = 3;
	constexpr const int PIN_DEBUG_TX = 1;
	constexpr const int PIN_THROTTLE = 14;
	constexpr const int PIN_STEERING = 0;
	constexpr const int PIN_HEADLIGHTS = 16;

	SoftwareSerial debugSerial(PIN_DEBUG_RX, PIN_DEBUG_TX);
	NeoPixelBus<NeoGrbFeature, NeoEsp8266Uart1800KbpsMethod> strip(/* length */ 1);
	ImuLSM6DS3 imu(Wire);
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

	strip.Begin();
	setColor(0, 0, 0);

	_batt_adc = analogRead(0);

	Wire.begin();
	imu.init();
}

void CarBoard::loop() {
	unsigned long now = millis();
	if (now - _batt_adc_time > 200) {
		_batt_adc_time = now;
		_batt_adc = analogRead(0);
	}
	if (now - _imu_sample_time >= 10) {
		_imu_sample_time = now;
		auto imu2car_coord = [](auto vec) {
			std::swap(vec[0], vec[1]);
			vec[0] *= -1;
			return vec;
		};
		if (imu.accelerometerDataReady()) _imu_xl = imu2car_coord(imu.readAccelerometer());
		if (imu.gyroscopeDataReady()) _imu_g = imu2car_coord(imu.readGyroscope());
	}
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
	const int16_t value = map(i_angle, -32768, 32767, 2000, 1000);
	_steeringServo.writeMicroseconds(value);
}

void CarBoard::setThrottle(int16_t i_speed) {
	const int16_t value = (i_speed > 0) ? map(i_speed, 0, 32767, 1423, 1000) :
	                      (i_speed < 0) ? map(i_speed, -32768, 0, 2000, 1576) :
	                      1500;
	_throttleServo.writeMicroseconds(value);
}

void CarBoard::setHeadlights(uint16_t i_pwr) {
	const uint8_t value = map(i_pwr, 0, 65535, 0, 255);
	analogWrite(PIN_HEADLIGHTS, value);
}

void CarBoard::setColor(uint8_t r, uint8_t g, uint8_t b) {
	strip.SetPixelColor(0, RgbColor(r, g, b));
	strip.Show();
}

uint16_t CarBoard::batteryLevel_ADC() const {
	return _batt_adc;
}

uint16_t CarBoard::batteryLevel_gauge() const {
	return 0;
}
