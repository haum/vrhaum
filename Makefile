build:
	pio run

upload: upload_ota

upload_serial:
	pio run -t upload

upload_ota:
	@if [ "${OTA_TARGET}" == "" ]; then echo "No OTA_TARGET environmnt variable"; /bin/false; else echo Upload to ${OTA_TARGET}; fi
	PLATFORMIO_UPLOAD_FLAGS=--auth=CarInSituOTA pio run -t upload --upload-port ${OTA_TARGET}.local

upload_ota_all:
	for car in $(avahi-browse -t _arduino._tcp | grep CarNode | awk -F' ' '{ print $4 }')
	do
		PLATFORMIO_UPLOAD_FLAGS=--auth=CarInSituOTA pio run --target upload --upload-port ${car}.local
	done

clean:
	pio run -t clean

monitor:
	pio device monitor
