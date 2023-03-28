#include <OtaUpdater.hpp>
#include <ArduinoOTA.h>

void OTAUpdater::init(String hostname) {
	ArduinoOTA.setHostname(hostname.c_str());
	ArduinoOTA.setPasswordHash("6f67154c3512b8de72af2e635be08f17");
	ArduinoOTA.setRebootOnSuccess(true);

	ArduinoOTA.onStart([this]() {
		_log.print("OTA: Start updating ");
		_log.println(ArduinoOTA.getCommand() == U_FLASH ? "sketch" : "filesystem");
	});
	ArduinoOTA.onEnd([this]() {
		_log.println("OTA: End");
	});
	ArduinoOTA.onProgress([this](unsigned int progress, unsigned int total) {
		_log.printf("OTA: Progress: %u%%\r", (progress / (total / 100)));
	});
	ArduinoOTA.onError([this](ota_error_t error) {
		_log.printf("OTA: Error[%u]: ", error);
		_log.println([](ota_error_t error){
			switch(error) {
				case OTA_AUTH_ERROR: return "Auth Failed";
				case OTA_BEGIN_ERROR: return "Begin Failed";
				case OTA_CONNECT_ERROR: return "Connect Failed";
				case OTA_RECEIVE_ERROR: return "Receive Failed";
				case OTA_END_ERROR: return "End Failed";
			}
			return "?";
		}(error));
	});

	ArduinoOTA.begin();
	_log.println("OTA: Ready");
}

void OTAUpdater::loop() {
	ArduinoOTA.handle();
}

