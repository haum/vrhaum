#!/bin/bash

if [ "$1" == "all" ]
then
	echo "Upload to all detected"
	GATES=$(avahi-browse -t _arduino._tcp | grep GateNode | awk -F' ' '{ print $4 }')
	[ "$GATES" == "" ] && (echo "No gate found."; exit 1) || echo "Gates: $GATES"
	for gate in $GATES
	do
		PLATFORMIO_UPLOAD_FLAGS=--auth=CarInSituOTA pio run --target upload --upload-port ${gate}.local
	done

else
	if [ "${OTA_TARGET}" == "" ]
	then
		echo "No OTA_TARGET environment variable."
		exit 1
	else
		echo Upload to ${OTA_TARGET}
	fi
	PLATFORMIO_UPLOAD_FLAGS=--auth=CarInSituOTA pio run -t upload --upload-port ${OTA_TARGET}.local
fi
