#include <GateCtrl.hpp>

Stream & GateCtrl::log() {
	return _gate.serial();
}

void GateCtrl::init() {
	_gate.init();
	_server.begin();

	Config readconfig = _gate.eeprom_load<Config>();
	if (!strcmp("GateNode", readconfig.header) && readconfig.version == 1)
		setConfig(readconfig);
	else
		useDefaultConfig();

	_gate.setIrCode(configCode());
}

void GateCtrl::loop() {
	WiFiClient accepted_client = _server.accept();
	if (accepted_client) {
		if (_client.connected()) {
			accepted_client.println("Sorry, only one client allowed.");
			accepted_client.stop();
		} else {
			_client = accepted_client;
			_client.setTimeout(5);
			_client.println("GateNode");
			_client.println("========");
		}
	}

	if (_client.available() > 0) {
		String line = _client.readStringUntil('\n');
		line.trim();
		if (line == "") {
			_client.flush();

		} else if (line == "DumpConfig") {
			_client.println("RAM config");
			for (size_t i=0; i < sizeof(Config); i++) { _client.print(*(reinterpret_cast<uint8_t*>(&_config)+i), HEX); _client.print(' '); }
			_client.print('\n');

			_client.println("EEPROM config");
			Config readconfig = _gate.eeprom_load<Config>();
			for (size_t i=0; i < sizeof(Config); i++) { _client.print(*(reinterpret_cast<uint8_t*>(&readconfig)+i), HEX); _client.print(' '); }
			_client.print('\n');

			_client.println("Default config");
			Config defconfig;
			for (size_t i=0; i < sizeof(Config); i++) { _client.print(*(reinterpret_cast<uint8_t*>(&defconfig)+i), HEX); _client.print(' '); }
			_client.print('\n');

		} else if (line == "Code?") {
			printCode(_client);

		} else if (line == "Save") {
			printCode(_client);
			_client.println("Saving code");
			saveConfig();

		} else if (line.length() == 2 && line[0] == '!') {
			uint8_t code = line[1];
			setConfigCode(code);
			_gate.setIrCode(code);
			printCode(_client);

		} else {
			_client.println("Not understood.");
			_client.print(line);
		}
	}

	_gate.loop();
}

void GateCtrl::printCode(Stream & s) {
	uint8_t code = _gate.getIrCode();
	s.print("Code: 0x");
	s.print(code, HEX);
	s.print(" (");
	s.print(static_cast<char>(code));
	s.println(")");
}

void GateCtrl::setConfig(const Config & conf) {
	_config = conf;
	if (_config.name[0] == 0) setConfigNameMAC();
}

void GateCtrl::useDefaultConfig() {
	if (_config.name[0] == 0) setConfigNameMAC();
}

void GateCtrl::setConfigNameMAC() {
	String name;
	std::array<uint8_t, 6> mac = _gate.mac();
	for (auto it = mac.rbegin(); it != mac.rend(); it++) name += String(*it, HEX);
	strncpy(_config.name, name.c_str(), 12);
	_config.name[12] = 0;
}

void GateCtrl::setConfigName(String name) {
	if (name.length() == 0) setConfigNameMAC();
	else strncpy(_config.name, name.c_str(), sizeof(_config.name));
}

const char * GateCtrl::configName() { return _config.name; }

void GateCtrl::setConfigCode(uint8_t code) { _config.code = code; }

const uint8_t GateCtrl::configCode() const { return _config.code; }

String GateCtrl::hostname() { return String("GateNode-") + _config.name; }

void GateCtrl::saveConfig() {
	_gate.eeprom_save(_config);
}
