#!/usr/bin/env python3

import time
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
    window = pyglet.window.Window(1024, 1024, 'CarInSitu - Simulation display')

    pyglet.resource.path = ['./display_simulation/']
    pyglet.resource.reindex()

    anchor_adj = 180
    img_car = pyglet.resource.image("car.png")
    img_car.anchor_x = img_car.width // 2
    img_car.anchor_y = img_car.height // 5 + anchor_adj
    img_lights = pyglet.resource.image("lights.png")
    img_lights.anchor_x = img_lights.width // 2
    img_lights.anchor_y = anchor_adj - 364
    img_tile = pyglet.resource.image("tile.png")
    background = pyglet.image.TileableTexture.create_for_image(img_tile)
    window.set_icon(img_car)

    batch = pyglet.graphics.Batch()
    led = pyglet.shapes.Rectangle(x=window.width//2, y=window.height//2, width=18, height=18, color=(0,0,0), batch=batch)
    led.anchor_x = 9
    led.anchor_y = 50 + anchor_adj/2
    car = pyglet.sprite.Sprite(img=img_car, x=window.width//2, y=window.height//2, batch=batch)
    car.scale=0.5
    lights = pyglet.sprite.Sprite(img=img_lights, x=window.width//2, y=window.height//2, batch=batch)
    lights.scale=0.5

    @window.event
    def on_draw():
        window.clear()
        background.blit_tiled(0, 0, 0, window.width, window.height)
        batch.draw()

    def set_xy(x, y):
        # x and y are reversed, because x+ of the car is up on the screen
        background.anchor_x = y % img_tile.width
        background.anchor_y = x % img_tile.height

    def set_angle(a):
        led.rotation = a
        car.rotation = a
        lights.rotation = a

    def set_hl(v):
        lights.opacity = v * 255

    def set_led(c):
        led.color = c

    def handle_msgs(dt):
        packet, sender = receiver.recv()
        if sender[0] == car_ip:
            msgs = decoder.decode(packet)
            for m in msgs:
                if 'simu_x' in m:
                    set_xy(m['simu_x']/32768*1024, m['simu_y']/32768*1024)
                    set_angle(m['simu_angle'] * 180 / 32768)
                if 'headlights' in m:
                    set_hl(m['headlights']/65535)
                if 'led_color_r' in m:
                    set_led((m['led_color_r'], m['led_color_g'], m['led_color_b']))

    pyglet.clock.schedule_interval(handle_msgs, 0.005)
    pyglet.app.run()

