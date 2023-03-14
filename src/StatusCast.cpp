#include <StatusCast.hpp>

#include <ESP8266WiFi.h>

void StatusCast::init() {
}

void StatusCast::loop() {
	unsigned long now = millis();
	if (now - _last_msg < 50) return;
	_last_msg = now;

	if (!WiFi.isConnected()) return;

	std::array<uint8_t, 256> msg;
	int len = 0;

	msg[len++] = 'C';
	msg[len++] = 'I';
	msg[len++] = 'S';

	for (auto s : _exports) switch (s) {
		case STATUS_NO_REPORT:
			break; // Do nothing
		case STATUS_RSSI: {
			msg[len++] = STATUS_RSSI;
			const int32_t rssi = WiFi.RSSI();
			msg[len++] = (rssi >>  0) & 0xFF;
			msg[len++] = (rssi >>  8) & 0xFF;
			msg[len++] = (rssi >> 16) & 0xFF;
			msg[len++] = (rssi >> 24) & 0xFF;
			break;
		}
		case STATUS_IR: {
			break;
		}
		case STATUS_SIMULATION: {
			msg[len++] = STATUS_SIMULATION;
			auto & sim = _car.simulation();
			int16_t x = sim.x();
			msg[len++] = (x >>  0) & 0xFF;
			msg[len++] = (x >>  8) & 0xFF;
			int16_t y = sim.y();
			msg[len++] = (y >>  0) & 0xFF;
			msg[len++] = (y >>  8) & 0xFF;
			int16_t theta = sim.theta();
			msg[len++] = (theta >>  0) & 0xFF;
			msg[len++] = (theta >>  8) & 0xFF;
			break;
		}
		case STATUS_HEADLIGHTS: {
			msg[len++] = STATUS_HEADLIGHTS;
			uint16_t hl = _car.headlightsPower();
			msg[len++] = (hl >>  0) & 0xFF;
			msg[len++] = (hl >>  8) & 0xFF;
			break;
		}
		case STATUS_COLOR: {
			msg[len++] = STATUS_COLOR;
			auto color = _car.color();
			msg[len++] = color[0];
			msg[len++] = color[1];
			msg[len++] = color[2];
			auto displayed_color = _car.displayed_color();
			msg[len++] = displayed_color[0];
			msg[len++] = displayed_color[1];
			msg[len++] = displayed_color[2];
			break;
		}
	}

	IPAddress multicast{239, 255, 0, 1};
	_udp.beginPacketMulticast(multicast, 4211, WiFi.localIP());
	_udp.write(msg.data(), len);
	_udp.endPacket();
}
