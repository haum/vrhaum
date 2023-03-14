#!/usr/bin/env python3

from zeroconf import Zeroconf, ServiceListener
from input_utils import yn_input, choice_input

class CarDetector:
    def __init__(self):
        self._catalog = {}

    def start(self):
        self.zconf = Zeroconf()
        self.zconf.add_service_listener("_carnode._udp.local.", self)
        from time import sleep
        sleep(0.1)

    def createobj(self, zeroconf, serviceType, name):
        info = zeroconf.get_service_info(serviceType, name)
        return {
                'ip': info.parsed_addresses()[0],
                'port': info.port,
                'name': info.name[:-21],
                'servicename': info.name,
                'server': info.server,
                'properties': info.properties,
        }

    def add_service(self, zeroconf, serviceType, name):
        o = self.createobj(zeroconf, serviceType, name)
        self._catalog[o.get('ip')] = o

    def remove_service(self, zeroconf, serviceType, name):
        o = self.createobj(zeroconf, serviceType, name)
        self._catalog.pop(o.get('ip'))

    def update_service(self, zeroconf, serviceType, name):
        o = self.createobj(zeroconf, serviceType, name)
        self._catalog[o.get('ip')] = o

    def detected_cars(self):
        return self._catalog

    def choose_car(self):
        ret = None
        while ret == None:
            lst = ['[Reload list]'] + [self._catalog[k]['name'] for k in self._catalog]
            nbmax = len(lst)
            if nbmax == 1:
                yn = yn_input('No car found, search again?')
                if yn == 'N': break
            else:
                nb = choice_input(lst, 'Which car?')
                if nb and nb > 1:
                    name = lst[nb - 1]
                    for v in self._catalog.values():
                        if v.get('name') == name: return v
                    return None
        return ret

if __name__ == '__main__':
    import sys
    detector = CarDetector()
    detector.start()

    def action__list():
        while True:
            cars = detector.detected_cars()
            for k in cars: print(cars[k])
            if yn_input('List again?', 'Y') == 'N': break

    def action__choose():
        print('You chose:', detector.choose_car())

    actions = [x[8:] for x in locals() if x.startswith('action__')]
    op = sys.argv[1] if len(sys.argv) == 2 and sys.argv[1] in actions else ''
    if op == '': op = actions[choice_input(actions, 'Which test?')-1]

    f = locals().get('action__' + op, None)
    if f: f()
