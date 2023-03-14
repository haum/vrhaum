#ifndef STATUSCAST_HPP
#define STATUSCAST_HPP

#include <WiFiUdp.h>
#include <CarCtrl.hpp>

class StatusCast {
	private:
		typedef enum : uint8_t {
			STATUS_NO_REPORT,
			STATUS_RSSI,
			STATUS_IR,
			STATUS_SIMULATION,
			STATUS_HEADLIGHTS,
			STATUS_COLOR,
		} status_t;

		std::array<status_t, 20> _exports = {
			STATUS_RSSI,
			STATUS_IR,
			STATUS_SIMULATION,
			STATUS_HEADLIGHTS,
			STATUS_COLOR,
		};

		CarCtrl & _car;
		WiFiUDP _udp;
		unsigned long _last_msg = 0;

	public:
		StatusCast(CarCtrl & car) : _car(car) {}
		void init();
		void loop();
};

#endif
