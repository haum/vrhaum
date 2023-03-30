#!/usr/bin/env python3

import time

from cardetector import CarDetector
from joystick import choose_joystick, JoystickPilot, BTN_X, BTN_START, BTN_SELECT
from carmessagestx import CarMessageUdpTx, CarMessageForge

class Cockpit:
    def __init__(self, joystick, car):
        self._pilot = JoystickPilot(joystick)

        self._cartx = CarMessageUdpTx()
        self._cartx.usePrivilegeLevel(1, b'\0\0\0\0\0\0')
        self._cartx.setDestination(car)

        self._forge = CarMessageForge()
        self._cartx.send(self._forge.cmd_engine_on())
        self._engine_on = True

        # Use higher privilege level to extend max speed
        self._cartx.usePrivilegeLevel(2, b'\0\0\0\0\0\0')
        self._cartx.send(self._forge.cmd_limit_speed(32767, -16000))

        # Back to lower level
        self._cartx.usePrivilegeLevel(1, b'\0\0\0\0\0\0')

    def process(self):
        self._pilot.decode()

        msg = b''

        throttle, steering = self._pilot.pilot_commands()
        throttle = int(throttle*32767)
        steering = int(steering*32767)
        msg += self._forge.cmd_pilot(throttle, steering)

        j = self._pilot.joystick()
        if j.button(BTN_START, True):
            self._engine_on = not self._engine_on
            print("Turn engine '%s'" % ('on' if self._engine_on else 'off'))
            msg += self._forge.cmd_engine_on(self._engine_on)

        if j.button(BTN_SELECT, True):
            print("Turn assist mode '%s'" % ('on' if self._pilot.assistance_enabled() else 'off')) # Change is done in pilot, but let's display a message

        btn_x = j.button(BTN_X, True)
        if btn_x is not None:
            if self._engine_on:
                msg += self._forge.cmd_headlights(65535 if btn_x else 20000)

        # Send all commands in a row to the car
        self._cartx.send(msg)

if __name__ == '__main__':
    detector = CarDetector()
    detector.start()

    print('This script allows to play with a joystick.')
    print('\nFirst, choose your joystick.')
    joy = choose_joystick()
    if joy is None:
        print('No joystick.')
        exit()

    print('\nNow, choose your car.')
    car_info = detector.choose_car()
    car = (car_info['ip'], car_info['port'])

    cockpit = Cockpit(joy, car)

    while True:
        time.sleep(0.05)
        cockpit.process()
