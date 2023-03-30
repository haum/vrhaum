#!/usr/bin/env python3

import socket
import struct

class CarMulticastReceiver:
    def __init__(self, mcast_grp = '239.255.0.1', mcast_port = 4211):
        # Listen socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setblocking(False)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, struct.pack("4sl", socket.inet_aton(mcast_grp), socket.INADDR_ANY))
        sock.bind((mcast_grp, 4211))
        self.sock = sock

    def fileno(self):
        return self.sock.fileno()

    def recv(self):
        try:
            return self.sock.recvfrom(10240)
        except BlockingIOError:
            return b'', ('', 0)

class CarMulticastDecoder:
    def __init__(self):
        self.msgs = {
            0x01: ['i', 'RSSI'],
            0x02: ['B', 'gate'],
            0x03: ['hhh', 'simu_x', 'simu_y', 'simu_angle'],
            0x04: ['H', 'headlights'],
            0x05: ['BBBBBB', 'car_color_r', 'car_color_g', 'car_color_b', 'led_color_r', 'led_color_g', 'led_color_b'],
            0x06: ['Hh', 'batt_adc', 'batt_soc'],
            0x07: ['hhhhhh', 'imu_a_x', 'imu_a_y', 'imu_a_z', 'imu_g_x', 'imu_g_y', 'imu_g_z'],
            0x08: ['hhB', 'pilot_throttle', 'pilot_steering', 'pilot_started'],
        }

    def decode(self, packet):
        ret = []
        if len(packet) < 3: return []
        if packet[:3] != b'CIS': return []
        packet = packet[3:]
        while len(packet) > 0:
            d = packet[0]
            if not d in self.msgs: break
            fmt = self.msgs[d][0]
            length = struct.calcsize(fmt)
            fields = self.msgs[d][1:]
            obj = {}
            for k,v in zip(fields, struct.unpack(fmt, packet[1:1+length])):
                obj[k] = v
            ret.append(obj)
            packet = packet[length+1:]
        return ret


if __name__ == '__main__':
    from select import select
    import sys
    receiver = CarMulticastReceiver()
    decoder = CarMulticastDecoder()
    filters = sys.argv[1:]
    def filter_ok(m):
        if len(filters) == 0: return True
        for f in filters:
            if f in m: return True
        return False
    try:
        while True:
            rlist, _, _ = select([receiver], [], [])
            if rlist:
                packet, sender = receiver.recv()
                msgs = decoder.decode(packet)
                for m in msgs:
                    if filter_ok(m):
                        print(sender[0] + ': ' + str(m))
    except KeyboardInterrupt:
        pass
