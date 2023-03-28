#include <GateCtrl.hpp>
#include <OtaUpdater.hpp>
#include <WifiLink.hpp>

GateCtrl gate;
WifiLink wifilink(gate.log());
OTAUpdater ota(gate.log());

const char wifi_ssid[] = "CarInSitu";
const char wifi_passwd[] = "Roulez jeunesse !";

void setup() {
	gate.init();
	wifilink.init(wifi_ssid, wifi_passwd, gate.hostname());
	ota.init(gate.hostname());
}

void loop() {
	gate.loop();
	wifilink.loop();
	ota.loop();
}

