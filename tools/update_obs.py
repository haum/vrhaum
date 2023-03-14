#!/usr/bin/env python3

from cardetector import CarDetector
from carmessagesrx import CarMulticastReceiver, CarMulticastDecoder
import obsws_python as obs

if __name__ == '__main__':
    detector = CarDetector()
    detector.start()

    obsc = obs.ReqClient(password=input('OBS password: '))

    print('Select Car-H')
    car_h = detector.choose_car()['ip']
    print('Select Car-A')
    car_a = detector.choose_car()['ip']
    print('Select Car-U')
    car_u = detector.choose_car()['ip']
    print('Select Car-M')
    car_m = detector.choose_car()['ip']

    config = [
        (car_h, 'RSSI', 'text', ['CAR_H_RSSI', 'RSSI: ', 'dB']),
        (car_a, 'RSSI', 'text', ['CAR_A_RSSI', 'RSSI: ', 'dB']),
        (car_u, 'RSSI', 'text', ['CAR_U_RSSI', 'RSSI: ', 'dB']),
        (car_m, 'RSSI', 'text', ['CAR_M_RSSI', 'RSSI: ', 'dB']),
    ]

    values = {}

    def upt_txt(v, name, prefix='', suffix=''):
        if values.get(name, None) != v:
            values[name] = v
            obsc.set_input_settings(name, {'text': prefix+str(v)+suffix}, True)

    actions = {
        'text': upt_txt
    }

    from select import select
    receiver = CarMulticastReceiver()
    decoder = CarMulticastDecoder()
    try:
        while True:
            rlist, _, _ = select([receiver], [], [])
            if rlist:
                packet, sender = receiver.recv()
                msgs = decoder.decode(packet)
                for m in msgs:
                    for c in config:
                        if c[0] == sender[0] and c[1] in m:
                            actions[c[2]](m[c[1]], *c[3])
    except KeyboardInterrupt:
        pass
