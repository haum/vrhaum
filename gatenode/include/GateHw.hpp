#ifndef GATHW_HPP
#define GATHW_HPP

#include <array>
#include <cinttypes>

#include <EEPROM.h>
#include <IRsend.h>
#include <Stream.h>

class GateHw {
	private:
		IRsend _ir_send{4};
		uint8_t _ir_code = 0;

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
			EEPROM.commit();
		}

		Stream & serial() const;

		void setIrCode(uint8_t code);
		uint8_t getIrCode() const;
};

#endif
