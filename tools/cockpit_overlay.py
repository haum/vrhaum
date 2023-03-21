#!/usr/bin/env python3

from math import sin, cos, pi

from cardetector import CarDetector
from carmessagesrx import CarMulticastReceiver, CarMulticastDecoder

if __name__ == '__main__':
    receiver = CarMulticastReceiver()
    decoder = CarMulticastDecoder()

    detector = CarDetector()
    detector.start()

    print('\nChoose your car.')
    car_info = detector.choose_car()
    if not car_info:
        print('No car.')
        exit()
    car_ip = car_info['ip']

    import pyglet
    window = pyglet.window.Window(1280, 162, 'CarInSitu - Cockpit ' + car_info['name'])

    pyglet.resource.path = ['./cockpit_overlay']
    pyglet.resource.reindex()

    img_board = pyglet.resource.image("board.png")
    img_board.anchor_x = 0
    img_board.anchor_y = 0
    img_steering = pyglet.resource.image("steering.png")
    img_steering.anchor_x = img_steering.width//2
    img_steering.anchor_y = 98
    img_throttle_mask = pyglet.resource.image("throttle_mask.png")
    img_throttle_mask.anchor_x = 145/2
    img_throttle_mask.anchor_y = 145/2
    window.set_icon(img_steering)

    batch = pyglet.graphics.Batch()
    grp1 = pyglet.graphics.Group(1)
    board = pyglet.sprite.Sprite(img=img_board, x=0, y=0, batch=batch)
    name_txt = pyglet.text.Label(car_info['name'][8:], x=window.width//2, y=80, font_size=25, color=(210, 210, 210, 255), anchor_x='center', batch=batch)
    steering = pyglet.sprite.Sprite(img=img_steering, x=window.width//2, y=14, batch=batch, group=grp1)
    rssi_bar = pyglet.shapes.Rectangle(x=20, y=12, width=80, height=8, color=(0x00, 0x88, 0xAA), batch=batch)
    batt_bar = pyglet.shapes.Rectangle(x=1180, y=12, width=80, height=8, color=(0x00, 0x88, 0xAA), batch=batch)
    batt_txt = pyglet.text.Label('--', x=1170, y=12, font_size=20, color=(30, 30, 30, 255), anchor_x='right', batch=batch)
    rssi_txt = pyglet.text.Label('--', x=110, y=12, font_size=20, color=(30, 30, 30, 255), anchor_x='left', batch=batch)
    throttle = pyglet.shapes.Sector(x=375, y=85, radius=70, angle=0, start_angle=-3*pi/4, color=(0, 0, 0, 255), batch=batch)
    throttle_mask = pyglet.sprite.Sprite(img=img_throttle_mask, x=375, y=85, batch=batch, group=grp1)
    thr_txt = pyglet.text.Label('--', x=375, y=78, font_size=18, color=(30, 30, 30, 255), anchor_x='center', batch=batch)

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    def set_rssi(v):
        p = min(max(0, v + 120) / 120, 1)
        rssi_bar.x = 20+(1-p)*80
        rssi_bar.width = p*80
        rssi_txt.text = str(v) + 'dB'

    def set_batt(v):
        volts = v/1024*8.8
        p = min(max(0, (volts-7)/(8.4-7)), 1)
        batt_bar.width = p*80
        batt_txt.text = str(round(p*1000)/10) + '%'

    def set_angle(v):
        a = 30*v/32768
        steering.rotation = a

    def set_throttle(v):
        p = v / 32768
        if p >= 0:
            throttle.start_angle = -2.23
            throttle.angle = -4.71*p
            throttle.color = (0x44, 0xAA, 0x00)
        else:
            throttle.start_angle = -0.78
            throttle.angle = -4.83*p
            throttle.color = (0xAA, 0x00, 0x00)
        thr_txt.text = str(round(p*100)) + '%'

    def handle_msgs(dt):
        packet, sender = receiver.recv()
        if sender[0] == car_ip:
            msgs = decoder.decode(packet)
            for m in msgs:
                if 'pilot_steering' in m:
                    set_throttle(m['pilot_throttle'])
                    set_angle(m['pilot_steering'])
                if 'batt_gauge' in m:
                    set_batt(m['batt_adc'])
                if 'RSSI' in m:
                    set_rssi(m['RSSI'])

    pyglet.clock.schedule_interval(handle_msgs, 0.005)
    pyglet.app.run()

