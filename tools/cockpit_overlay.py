#!/usr/bin/env python3

import sys, time
from math import pi, atan2
from pyglet.math import Mat4, Vec3, Vec4

from cardetector import CarDetector
from carmessagesrx import CarMulticastReceiver, CarMulticastDecoder

if __name__ == '__main__':
    receiver = CarMulticastReceiver()
    decoder = CarMulticastDecoder()

    detector = CarDetector()
    detector.start()

    if len(sys.argv) > 1:
        carname = sys.argv[1]
        print('Searching ' + carname + '...')
        found = False
        while not found:
            cars = detector.detected_cars()
            for c in cars:
                if cars[c]['name'] == carname:
                    car_info = cars[c]
                    found = True
                    break
            time.sleep(0.5)
    else:
        print('\nChoose your car.')
        car_info = detector.choose_car()
        if not car_info:
            print('No car.')
            car_info = {'ip': '', 'name': 'CarNode-NoCar'}
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
    img_steering_color = pyglet.resource.image("steering_color.png")
    img_steering_color.anchor_x = img_steering_color.width//2
    img_steering_color.anchor_y = 25
    img_throttle_mask = pyglet.resource.image("throttle_mask.png")
    img_throttle_mask.anchor_x = 145/2
    img_throttle_mask.anchor_y = 145/2
    window.set_icon(img_steering)

    batch2D = pyglet.graphics.Batch()
    grp1 = pyglet.graphics.Group(1)
    board = pyglet.sprite.Sprite(img=img_board, x=0, y=0, batch=batch2D)
    name_txt = pyglet.text.Label(car_info['name'][8:], x=window.width//2, y=80, font_size=25, color=(210, 210, 210, 255), anchor_x='center', batch=batch2D)
    steering = pyglet.sprite.Sprite(img=img_steering, x=window.width//2, y=14, batch=batch2D, group=grp1)
    steering_color = pyglet.sprite.Sprite(img=img_steering_color, x=window.width//2, y=14, batch=batch2D, group=grp1)
    rssi_bar = pyglet.shapes.Rectangle(x=20, y=12, width=80, height=8, color=(0x00, 0x88, 0xAA), batch=batch2D)
    batt_bar = pyglet.shapes.Rectangle(x=1180, y=12, width=80, height=8, color=(0x00, 0x88, 0xAA), batch=batch2D)
    batt_txt = pyglet.text.Label('--', x=1170, y=12, font_size=20, color=(30, 30, 30, 255), anchor_x='right', batch=batch2D)
    rssi_txt = pyglet.text.Label('--', x=110, y=12, font_size=20, color=(30, 30, 30, 255), anchor_x='left', batch=batch2D)
    throttle = pyglet.shapes.Sector(x=375, y=85, radius=70, angle=0, start_angle=-3*pi/4, color=(0, 0, 0, 255), batch=batch2D)
    throttle_mask = pyglet.sprite.Sprite(img=img_throttle_mask, x=375, y=85, batch=batch2D, group=grp1)
    thr_txt = pyglet.text.Label('--', x=375, y=78, font_size=18, color=(30, 30, 30, 255), anchor_x='center', batch=batch2D)
    batch3D= pyglet.graphics.Batch()
    diode = pyglet.resource.model("diode.obj", batch=batch3D)
    diode.matrix = Mat4.from_rotation(pi/2, (1, 0, 0)) @ Mat4.from_translation((0, 0, -10))

    @window.event
    def on_draw():
        window.clear()

        pyglet.gl.glDisable(pyglet.gl.GL_DEPTH_TEST)
        window.projection = Mat4.orthogonal_projection(0, window.width, 0, window.height, -1, 1)
        window.viewport = (0, 0, window.width, window.height)
        batch2D.draw()

        pyglet.gl.glEnable(pyglet.gl.GL_DEPTH_TEST)
        window.projection = Mat4.perspective_projection(window.aspect_ratio, z_near=0.1, z_far=255)
        window.viewport = (178, 5, window.width+178, window.height+5)
        batch3D.draw()

    def set_rssi(v):
        p = min(max(0, v + 120) / 120, 1)
        rssi_bar.x = 20+(1-p)*80
        rssi_bar.width = p*80
        rssi_txt.text = str(v) + 'dB'

    def set_batt(v):
        soc = v/25600
        p = min(max(0, soc), 1)
        batt_bar.width = p*80
        batt_txt.text = str(round(p*1000)/10) + '%'

    def set_angle(v):
        a = 30*v/32768
        steering.rotation = a
        steering_color.rotation = a

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

    def set_imu(v):
        a = Vec3(-v['imu_a_y'], v['imu_a_z'], -v['imu_a_x']).normalize()
        rot_x = Mat4.from_rotation(pi/4-atan2(a[2], a[1]), Vec3(1, 0, 0))
        rot_y = Mat4.from_rotation(atan2(a[0], a[1]), Vec3(*(rot_x @ Vec4(0, 0, 1, 0))[:3]))
        trans = Mat4.from_translation(Vec3(0, 0, -10))
        diode.matrix = rot_x @ rot_y @ trans

    def set_color(r, g, b):
        steering_color.color = (r, g, b)

    def handle_msgs(dt):
        packet, sender = receiver.recv()
        if sender[0] == car_ip:
            msgs = decoder.decode(packet)
            for m in msgs:
                if 'pilot_steering' in m:
                    set_throttle(m['pilot_throttle'])
                    set_angle(m['pilot_steering'])
                if 'batt_soc' in m:
                    set_batt(m['batt_soc'])
                if 'RSSI' in m:
                    set_rssi(m['RSSI'])
                if 'imu_a_x' in m:
                    set_imu(m)
                if 'car_color_r' in m:
                    set_color(m['car_color_r'], m['car_color_g'], m['car_color_b'])

    pyglet.clock.schedule_interval(handle_msgs, 0.005)
    pyglet.app.run()

