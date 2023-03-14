#!/usr/bin/env python3

from inspect import signature
from ast import literal_eval

from input_utils import choice_input
from cardetector import CarDetector
from carmessagestx import CarMessageUdpTx, CarMessageForge

if __name__ == '__main__':
    detector = CarDetector()
    detector.start()

    print('\nChoose the car.')
    car_info = detector.choose_car()
    car = (car_info['ip'], car_info['port'])

    cartx = CarMessageUdpTx()
    cartx.setPassword(1, b'\0\0\0\0\0\0')
    cartx.setDestination(car)

    forge = CarMessageForge()
    cmds = ['[Change password]'] + [cmd[4:] for cmd in dir(forge) if cmd.startswith('cmd_')]

    while True:
        nb = choice_input(cmds, 'Command?')
        if nb == 1:
            cartx.input_setPassword()
        else:
            cmd = getattr(forge, 'cmd_' + cmds[nb-1])
            args = []
            for k in signature(cmd).parameters:
                args.append(literal_eval(input(k+'? ')))
            cartx.send(cmd(*args))
