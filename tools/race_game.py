#!/usr/bin/env python3

from input_utils import choice_input, yn_input

from cardetector import CarDetector
from carmessagesrx import CarMulticastReceiver, CarMulticastDecoder
from joystick import choose_joystick, JoystickPilot

import pyglet
import math

class GameManager:
    def __init__(self, gates):
        pyglet.resource.path = ['./race_game']
        pyglet.resource.reindex()

        self.img_bg = pyglet.resource.image("bg.png")
        self.bg = pyglet.image.TileableTexture.create_for_image(self.img_bg)

        self.winw = 160
        self.window = pyglet.window.Window(self.winw*4, 200, 'CarInSitu - Race Game', visible=False)
        self.batch = pyglet.graphics.Batch()

        @self.window.event
        def on_draw():
            self.window.clear()
            self.bg.blit_tiled(0, 0, 0, self.window.width, self.window.height)
            self.batch.draw()

        @self.window.event
        def on_key_press(symbol, modifiers):
            if self.state == 'wait_start': self.change_state('countdown')

        self.gates = gates
        self.receiver = CarMulticastReceiver()
        self.decoder = CarMulticastDecoder()
        self.ips = []
        self.players = []
        self.state = 'null'
        self.change_state('wait_start')

    def set_players(self, players):
        self.players = players
        self.ips = [p.ip for p in self.players]
        self.window.set_visible(True)

    def change_state(self, nstate):
        stop = 'state__' + self.state + '__stop'
        if stop in dir(self): getattr(self, stop)()
        start = 'state__' + nstate + '__start'
        if start in dir(self): getattr(self, start)()
        tick = 'state__' + nstate + '__tick'
        self.state_tick = getattr(self, tick) if tick in dir(self) else self.tick_null
        self.state = nstate

    def state__countdown__start(self):
        self.t = 3.1
        self.state__countdown__tick(0)
        for p in self.players:
            p.txt_countdown.visible = True

    def state__countdown__stop(self):
        for p in self.players:
            p.txt_countdown.visible = False

    def state__countdown__tick(self, dt):
        t0 = self.t
        self.t -= dt
        n = math.ceil(self.t)
        if math.ceil(t0) != n:
            for p in self.players:
                p.txt_countdown.text = str(n)
                c = (255, 0, 0, 255)
                if n == 1: c = (255, 180, 0, 255)
                if n == 2: c = (255, 90, 0, 255)
                p.txt_countdown.color = c
        if self.t < 0:
            for p in self.players:
                p.txt_countdown.text = 'GO'
                p.txt_countdown.color = (30, 180, 0, 255)
        if self.t < -1:
            self.change_state('race')

    def state__race__start(self):
        for p in self.players:
            p.boost.visible = True

    def state__race__stop(self):
        for p in self.players:
            p.boost.visible = False

    def state__race__tick(self, dt):
        pass

    def tick_null(self, dt):
        pass

    def tick(self, dt):
        self.state_tick(dt)
        packet, sender = self.receiver.recv()
        if sender[0] in self.ips:
            player = self.players[self.ips.index(sender[0])]
            msgs = self.decoder.decode(packet)
            for m in msgs:
                if 'car_color_r' in m:
                    player.set_color(m['car_color_r'], m['car_color_g'], m['car_color_b'])
                if 'gate' in m:
                    player.set_gate(m['gate'])


class Player:
    def __init__(self, car, joystick, gm, i):
        self.ip = car['ip']
        self.gm = gm

        self.progress = 0
        self.progress_next_gate = self.gm.gates[0]

        x0 = i * gm.winw
        self.txt_countdown = pyglet.text.Label('', x=x0+gm.winw//2, y=gm.window.height//2, font_size=50, color=(210, 210, 210, 255), anchor_x='center', batch=gm.batch)
        self.txt_countdown.visible = False

        self.boost = pyglet.shapes.Rectangle(x=x0+20, y=30, width=10, height=140, color=(0x00, 0x88, 0xAA), batch=gm.batch)
        self.boost.visible = False

    def set_color(self, r, g, b):
        self.boost.color = (r, g, b, 255)

    def set_gate(self, gate):
        if gate == self.progress_next_gate:
            self.progress += 1
            self.progress_next_gate = self.gm.gates[(self.progress+1)%len(self.gm.gates)]
            self.gm.recompute_places()


def define_players(detector, gm):
    nb_cars = choice_input(['One car', 'Two cars', 'Three cars', 'Four cars'], 'How many cars?')
    players = []
    for i in range(nb_cars):
        print('\nCar n°'+str(i+1))
        print('Which car?')
        car = detector.choose_car()
        print('Which joystick?')
        joy = choose_joystick()
        players.append((car, joy, gm, len(players)))
    return list(map(lambda x: Player(*x), players))


if __name__ == '__main__':
    detector = CarDetector()
    detector.start()

    gm = GameManager(b'ABCDEF')
    gm.set_players(define_players(detector, gm))

    pyglet.clock.schedule_interval(gm.tick, 0.005)
    pyglet.app.run()

