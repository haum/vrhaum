#ifndef CARBOARD_HPP
#define CARBOARD_HPP

#include <array>
#include <cinttypes>

#include <EEPROM.h>
#include <SoftwareSerial.h>
#include <Servo.h>

class CarBoard {
	private:
		Servo _throttleServo;
		Servo _steeringServo;

		uint16_t _batt_adc = 0;
		unsigned long _batt_adc_time = 0;

		std::array<int16_t, 3> _imu_xl;
		std::array<int16_t, 3> _imu_g;
		unsigned long _imu_sample_time = 0;

	public:
		void init();
		void loop();

		std::array<uint8_t, 6> mac() const;

		template<typename T>
		T eeprom_load() const {
			T ret;
			EEPROM.get(0, ret);
			return ret;
		}
		template<typename T>
		void eeprom_save(const T & data) {
			EEPROM.put(0, data);
		}

		Stream & debug_serial() const;

		void setThrottle(int16_t i_speed);
		void setSteering(int16_t i_angle);
		void setHeadlights(uint16_t i_pwr);
		void setColor(uint8_t r, uint8_t g, uint8_t b);

		uint16_t batteryLevel_ADC() const;
		uint16_t batteryLevel_gauge() const;

		std::array<int16_t, 3> imuAccelerometerData() const { return _imu_xl; }
		std::array<int16_t, 3> imuGyroscopeData() const { return _imu_g; }
};

#endif
