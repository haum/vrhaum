#!/usr/bin/env python3

from inspect import signature
from ast import literal_eval

from input_utils import choice_input
from cardetector import CarDetector
from carmessagestx import CarMessageUdpTx, CarMessageTcpTx, CarMessageForge

def interactive(tx):
    forge = CarMessageForge()
    cmds = ['[Change password]'] + [cmd[4:] for cmd in dir(forge) if cmd.startswith('cmd_')]

    while True:
        nb = choice_input(cmds, 'Command?')
        if nb == 1:
            tx.input_usePrivilegeLevel()
        else:
            cmd = getattr(forge, 'cmd_' + cmds[nb-1])
            args = []
            for k in signature(cmd).parameters:
                args.append(literal_eval(input(k+'? ')))
            tx.send(cmd(*args))

if __name__ == '__main__':
    import sys

    detector = CarDetector()
    detector.start()

    print('\nChoose the car.')
    car_info = detector.choose_car()
    car = (car_info['ip'], car_info['port'])

    if len(sys.argv) == 2 and sys.argv[1] == 'tcp':
        cartx = CarMessageTcpTx()
        cartx.input_usePrivilegeLevel()
        cartx.invite_and_wait(4212, car)
    elif (len(sys.argv) == 2 and sys.argv[1] == 'udp') or len(sys.argv) == 1:
        cartx = CarMessageUdpTx()
        cartx.usePrivilegeLevel(1, b'\0\0\0\0\0\0')
        cartx.setDestination(car)
    else:
        print('Usage: ' + sys.argv[0] + '[udp|tcp]')
        exit()

    interactive(cartx)
