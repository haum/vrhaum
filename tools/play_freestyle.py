#!/usr/bin/env python3

import time

from cardetector import CarDetector
from joystick import choose_joystick, JoystickPilot
from carmessagestx import CarMessageUdpTx, CarMessageForge
from evdev.ecodes import BTN_X, BTN_START, BTN_SELECT

class Cockpit:
    def __init__(self, joystick, car):
        self._joystick = joystick
        self._pilot = JoystickPilot()

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

        # Use a buffer to send messages
        self._msg = b''

        # Register event-based functions
        self._joystick.registerOnKeyEvent(BTN_START, self.toogleEngine)
        self._joystick.registerOnKeyEvent(BTN_X, self.setHeadLights)
        self._joystick.registerOnKeyEvent(BTN_SELECT, self.toogleAssistMode)

    def toogleEngine(self, key, value):
        # Only toogle engine when button is pressed (not released)
        if value == 0: return

        self._engine_on = not self._engine_on
        print("Turn engine '%s'" % ('on' if self._engine_on else 'off'))
        self._msg += self._forge.cmd_engine_on(self._engine_on)

    def toogleAssistMode(self, key, value):
        # Only toogle assist mode when button is pressed (not released)
        if value == 0: return
        self._pilot._assist_mode = not self._pilot._assist_mode
        print("Turn assist mode '%s'" % ('on' if self._pilot._assist_mode else 'off'))

    def setHeadLights(self, key, value):
        if self._engine_on:
            self._msg += self._forge.cmd_headlights(65535 if value else 20000)

    def process(self):
        # Empty the buffer
        self._msg = b''

        # Decode and execute event-driven registered functions if relevant
        # NOTE: Event-based function will add their commands during this
        throttle, steering = self._pilot.decode(self._joystick)
        throttle = int(throttle*32767)
        steering = int(steering*32767)
        self._msg += self._forge.cmd_pilot(throttle, steering)

        # Send all commands in a row to the car
        self._cartx.send(self._msg)

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
