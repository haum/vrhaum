#!/usr/bin/env python3

from cardetector import CarDetector
from carmessagestx import CarMessageUdpTx, CarMessageForge

if __name__ == '__main__':
    detector = CarDetector()
    detector.start()

    print('\nChoose the car.')
    car_info = detector.choose_car()
    car = (car_info['ip'], car_info['port'])

    cartx = CarMessageUdpTx()
    forge = CarMessageForge()
    cartx.setDestination(car)
    cartx.useAdminLevel()
    print('Reset pass level 1 and 2')
    cartx.send(
        forge.cmd_change_pass_lvl1(b'\0\0\0\0\0\0') +
        forge.cmd_change_pass_lvl2(b'\0\0\0\0\0\0')
    )
