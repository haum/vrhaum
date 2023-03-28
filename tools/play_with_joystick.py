#!/usr/bin/env python3

import time

from cardetector import CarDetector
from joystick import choose_joystick, JoystickPilot
from carmessagestx import CarMessageUdpTx, CarMessageForge

if __name__ == '__main__':
    from evdev.ecodes import BTN_TL, BTN_TR, BTN_MODE

    detector = CarDetector()
    detector.start()

    print('This script allows to play with a joystick.')

    print('\nFirst, choose your joystick.')
    joy = choose_joystick()
    if joy is None:
        print('No joystick.')
        exit()
    pilot = JoystickPilot()

    print('\nNow, choose your car.')
    car_info = detector.choose_car()
    car = (car_info['ip'], car_info['port'])

    cartx = CarMessageUdpTx()
    cartx.usePrivilegeLevel(1, b'\0\0\0\0\0\0')
    cartx.setDestination(car)

    forge = CarMessageForge()
    cartx.send(forge.cmd_engine_on())
    engine_on = True
    engine_on_debounce = False
    while True:
        msg = b''
        time.sleep(0.05)

        throttle, steering = pilot.decode(joy)
        throttle = int(throttle*32767)
        steering = int(steering*32767)
        msg += forge.cmd_pilot(throttle, steering)

        if engine_on_debounce == False and joy.button(BTN_MODE):
            engine_on = not engine_on
            msg += forge.cmd_engine_on(engine_on)
            engine_on_debounce = True
        elif not joy.button(BTN_MODE):
            engine_on_debounce = False

        if engine_on:
            msg += forge.cmd_headlights(65535 if joy.button(BTN_TL) or joy.button(BTN_TR) else 40000)

        cartx.send(msg)

