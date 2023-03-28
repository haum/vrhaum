build:
	pio run

upload: upload_ota

upload_serial:
	pio run -t upload

upload_ota:
	@./upload_ota.sh

upload_ota_all:
	@./upload_ota.sh all

clean:
	pio run -t clean

monitor:
	pio device monitor
