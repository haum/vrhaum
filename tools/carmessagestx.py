#!/usr/bin/env python3

import socket
import struct

class CarMessageTx:
    def __init__(self, send):
        self._send_msg = send
        self.usePrivilegeLevel(1, b'\0\0\0\0\0\0')

    def useAdminLevel(self):
        import os
        pwd = b'\0\0\0\0\0\0'
        try:
            with open(os.path.join(os.path.dirname(__file__), 'admin_pass'), 'rb') as f:
                pwd = bytes((f.read(6)+b'\0'*6)[:6])
        except:
            pass
        self.usePrivilegeLevel(3, pwd)

    def usePrivilegeLevel(self, lvl, passwd):
        self.cis_lvl_passwd = b'CIS' + bytes([lvl]) + bytes(passwd)

    def input_usePrivilegeLevel(self):
        from ast import literal_eval
        from input_utils import choice_input
        lvl = choice_input(['1', '2', '3'], 'Which level?')
        passwd = ''
        while passwd == '':
            try:
                passwd = (literal_eval('b\''+input('Password? ')+'\'') + b'\0'*6)[:6]
            except SyntaxError:
                print('Invalid input.')
        self.usePrivilegeLevel(lvl, passwd)

    def send(self, msg):
        if self._send_msg:
            self._send_msg(self.cis_lvl_passwd + msg)

class CarMessageUdpTx(CarMessageTx):
    def __init__(self):
        super().__init__(self._send)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dest = ('127.0.0.1', 4210)

    def setDestination(self, dest):
        self.dest = dest

    def _send(self, msg):
        if self.dest:
            self.sock.sendto(msg, self.dest)

class CarMessageTcpTx(CarMessageTx):
    def __init__(self):
        super().__init__(self._send)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def invite_and_wait(self, port=4212, dest=('127.0.0.1', 4210)):
        invite_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        forge = CarMessageForge()
        self.sock.bind(('0.0.0.0', port))
        self.sock.listen()
        invite_sock.sendto(self.cis_lvl_passwd + forge.cmd_open_tcp_link(port), dest)

        conn, addr = self.sock.accept()
        self.sock.close()
        self.sock = conn

    def _send(self, msg):
        self.sock.send(msg)

class CarMessageForge:
    def cmd_open_tcp_link(self, port=4212):
        return struct.pack('!BH', 0x01, port)

    def cmd_engine_on(self, on=True):
        return struct.pack('!BB', 0x10, 1 if on else 0)

    def cmd_pilot(self, throttle, steering):
        return struct.pack('!Bhh', 0x11, throttle, steering)

    def cmd_headlights(self, power):
        return struct.pack('!BH', 0x12, power)

    def cmd_save_config(self):
        return b'\x20'

    def cmd_change_pass_lvl1(self, passwd):
        return b'\x21' + bytes((passwd+b'\0'*6)[:6])

    def cmd_change_pass_lvl2(self, passwd):
        return b'\x22' + bytes((passwd+b'\0'*6)[:6])

    def cmd_change_pass_lvl3(self, passwd):
        return b'\x23' + bytes((passwd+b'\0'*6)[:6])

    def cmd_change_name(self, name):
        return b'\x24' + (name+b'\0'*17)[:17]

    def cmd_change_trims(self, steering_trim, start_fw, start_bw):
        return struct.pack('!BhHH', 0x25, steering_trim, start_fw, start_bw)

    def cmd_limit_speed(self, pos, neg):
        return struct.pack('!Bhh', 0x30, pos, neg)

    def cmd_invert_steering(self, on):
        return struct.pack('!BB', 0x31, on)

    def cmd_invert_throttle(self, on):
        return struct.pack('!BB', 0x32, on)

    def cmd_set_color(self, r, g, b):
        return struct.pack('!BBBB', 0x33, r, g, b)

if __name__ == '__main__':
    forge = CarMessageForge()
    print('Show some binary formating')

    print('\nengine_on True')
    print(forge.cmd_engine_on(True))

    print('\npilot 256 512')
    print(forge.cmd_pilot(256, 512))

    print('\nheadlights 1024')
    print(forge.cmd_headlights(1024))

    print('\nsave_config')
    print(forge.cmd_save_config())

    print('\nchange_pass_lvl1 b\'\\1\\2\\3\\4\\5\\6\'')
    print(forge.cmd_change_pass_lvl1(b'\1\2\3\4\5\6'))
    print('\nchange_pass_lvl2 b\'\\1\\2\\3\\4\\5\\6\'')
    print(forge.cmd_change_pass_lvl2(b'\1\2\3\4\5\6'))
    print('\nchange_pass_lvl3 b\'\\1\\2\\3\\4\\5\\6\'')
    print(forge.cmd_change_pass_lvl3(b'\1\2\3\4\5\6'))

    print('\nchange_pass_lvl3 b\'\\1\\2\\3\'')
    print(forge.cmd_change_pass_lvl3(b'\1\2\3'))
    print('\nchange_pass_lvl3 b\'\\1\\2\\3\\4\\5\\6\\7\'')
    print(forge.cmd_change_pass_lvl3(b'\1\2\3\4\5\6\7'))

    print('\nchange_name NewName')
    print(forge.cmd_change_name(b'NewName'))

    print('\nchange_stering_trim 128')
    print(forge.cmd_change_steering_trim(128))

    print('\nlimit_speed 15000 -15000')
    print(forge.cmd_limit_speed(15000, -15000))
    print('\ninvert_steering True')
    print(forge.cmd_invert_steering(True))
    print('\ninvert_throttle False')
    print(forge.cmd_invert_throttle(False))
