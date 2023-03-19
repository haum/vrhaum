#include <CarCtrl.hpp>

void CarCtrl::init() {
	_car.init();
	_sim.init();

	Config readconfig = _car.eeprom_load<Config>();
	if (!strcmp("CarNode", readconfig.header) && readconfig.version == 1)
		setConfig(readconfig);
	else
		useDefaultConfig();

	setHeadlights(0);
}

void CarCtrl::loop() {
	unsigned long now = millis();
	if (blinks()) {
		setHeadlightsPower(((now & 0x3FF) > 512) * 40000);
	} else {
		setHeadlightsPower(headlightsPower());
	}

	if ((now & 0xFF) < 128) {
		if (speed() < 0) setDisplayedColor({64, 64, 64});
		else if (speed_down()) setDisplayedColor({64, 0, 0});
		else if (speed() == 0) setDisplayedColor(color());
		else setDisplayedColor({0, 0, 0});
	} else {
		setDisplayedColor(color());
	}

	_sim.update();
	_car.loop();
}

void CarCtrlBase::shutdown() {
	_shutdown = true;
	_car.setThrottle(0);
	_car.setSteering(0);
	_car.setHeadlights(0);
	_car.setColor(0, 0, 0);
}

void CarCtrl::start_engine(bool on) {
	if (_shutdown) return;
	start_pilot(on);
	setHeadlights(on ? 40000 : 0);
}

void CarCtrlConfig::setConfig(const Config & conf) {
	_config = conf;
	if (_config.name[0] == 0) setConfigNameMAC();
}

void CarCtrlConfig::useDefaultConfig() {
	if (_config.name[0] == 0) setConfigNameMAC();
}

void CarCtrlConfig::setConfigNameMAC() {
	String name;
	std::array<uint8_t, 6> mac = _car.mac();
	for (auto it = mac.rbegin(); it != mac.rend(); it++) name += String(*it, HEX);
	strncpy(_config.name, name.c_str(), 12); 
	_config.name[12] = 0;
}

void CarCtrlConfig::setConfigName(String name) {
	if (name.length() == 0) setConfigNameMAC();
	else strncpy(_config.name, name.c_str(), sizeof(_config.name));
}

const char * CarCtrlConfig::configName() { return _config.name; }

String CarCtrlConfig::hostname() { return String("CarNode-") + _config.name; }

void CarCtrlConfig::setConfigAdminPass(std::array<uint8_t, 6> pass) { _config.adminpass = pass; }

const std::array<uint8_t, 6> CarCtrlConfig::configAdminPass() const { return _config.adminpass; }

void CarCtrlConfig::setConfigSteeringTrim(uint16_t value) { _config.steeringTrim = value; }

const uint16_t CarCtrlConfig::configSteeringTrim() const { return std::min(_config.steeringTrim, static_cast<uint16_t>(450)); }

void CarCtrlConfig::saveConfig() {
	_car.eeprom_save(_config);
}

void CarCtrlPilot::start_pilot(bool on) {
	if (_shutdown) return;
	_pilot_started = on;
}

void CarCtrlPilot::pilot(int16_t i_speed, int16_t i_angle) {
	if (_shutdown) return;
	if (_invert_throttle) i_speed *= -1;
	if (_invert_steering) i_angle *= -1;
	if (i_speed < 0) i_speed = std::max(_speed_max_neg, i_speed);
	if (i_speed > 0) i_speed = std::min(_speed_max_pos, i_speed);
	if (!_pilot_started) {
		i_speed = 0;
		i_angle = 0;
	}

	bool update_speed = (i_speed != _speed);
	bool update_angle = (i_angle != _angle);
	_speed_down = (abs(i_speed) < abs(_speed));
	_speed = i_speed;

	if (update_speed) _car.setThrottle(i_speed);
	if (update_angle) _car.setSteering(i_angle);

	_sim.pilot(i_speed, i_angle);
}

void CarCtrlPilot::limitSpeed(int16_t pos, int16_t neg) {
	_speed_max_pos = std::max(int16_t(0), pos);
	_speed_max_neg = std::min(int16_t(0), neg);
}

void CarCtrlHeadlights::setHeadlights(uint16_t i_pwr) {
	if (_shutdown) return;
	_headlights_pwr = i_pwr;
	if (!_blink) setHeadlightsPower(i_pwr);
}

void CarCtrlHeadlights::setHeadlightsPower(uint16_t i_pwr) {
	if (_shutdown) return;
	if (i_pwr == _headlights_pwr_set) return;
	_headlights_pwr_set = i_pwr;

	log().print("HL: ");
	log().println(i_pwr);

	_car.setHeadlights(i_pwr);
}

uint16_t CarCtrlHeadlights::headlightsPower() const {
	return _headlights_pwr;
}

void CarCtrlRearlight::setDisplayedColor(const color_t c) {
	if (_shutdown) return;
	_color_set = c;
	_car.setColor(c[0], c[1], c[2]);
}

void CarCtrlRearlight::setColor(const color_t c) {
	_color = c;
}

CarCtrlRearlight::color_t CarCtrlRearlight::color() const {
	return _color;
}

CarCtrlRearlight::color_t CarCtrlRearlight::displayed_color() const {
	return _color_set;
}
