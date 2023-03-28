#ifndef OTA_UPDATER_HPP
#define OTA_UPDATER_HPP

#include<Stream.h>

class OTAUpdater {
	private:
		Stream & _log;

	public:
		OTAUpdater(Stream & s) : _log(s) {}
		void init(String hostname);
		void loop();
};

#endif
