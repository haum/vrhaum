#!/usr/bin/env python3

from ast import literal_eval
import socket, time

from input_utils import choice_input, yn_input
from gatedetector import GateDetector

if __name__ == '__main__':
    detector = GateDetector()
    detector.start()

    print('\nChoose the gate.')
    gate_info = detector.choose_gate()
    gate = (gate_info['ip'], gate_info['port'])

    code = input('Code? ').strip()
    try:
        code = literal_eval('b"'+code+'"')
    except:
        print('Invalid code')
        exit()
    if len(code) > 1: code = code[-1:]

    print('Send code', code)

    save = (yn_input('Save?') == 'Y')
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(gate)
    sock.send(b'!' + code + b'\n')
    time.sleep(0.5)
    if save:
        sock.send(b'Save\n')
    sock.close()

