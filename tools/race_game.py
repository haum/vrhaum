#!/usr/bin/env python3

from input_utils import choice_input, yn_input

from cardetector import CarDetector
from carmessagesrx import CarMulticastReceiver, CarMulticastDecoder
from carmessagestx import CarMessageUdpTx, CarMessageForge
from joystick import choose_joystick, JoystickPilot, BTN_A, BTN_X, BTN_START, BTN_MODE

import pyglet
import math
import random

def time2str(t):
    minutes = t // 60
    seconds = t - 60 * minutes
    return f'{minutes:02.0f}:{seconds:05.2f}'

class GameManager:
    def __init__(self, gates, laps):
        pyglet.resource.path = ['./race_game']
        pyglet.resource.reindex()

        self.img_bg = pyglet.resource.image("bg.png")
        self.img_boost_mask = pyglet.resource.image("boost_mask.png")
        self.bg = pyglet.image.TileableTexture.create_for_image(self.img_bg)

        self.winw = 160
        self.window = pyglet.window.Window(self.winw*4, 200, 'CarInSitu - Race Game', visible=False)
        self.batch = pyglet.graphics.Batch()

        @self.window.event
        def on_draw():
            self.window.clear()
            self.bg.blit_tiled(0, 0, 0, self.window.width, self.window.height)
            self.batch.draw()

        self.gates = gates
        self.laps = laps
        self.receiver = CarMulticastReceiver()
        self.decoder = CarMulticastDecoder()
        self.ips = []
        self.players = []
        self.state = 'null'

    def set_players(self, players):
        self.players = players
        self.ips = [p.ip for p in self.players]

    def start(self):
        self.window.set_visible(True)
        self.change_state('getready')

    def recompute_ranks(self):
        for i, (_, _, n) in enumerate(sorted([(p.progress, -p.rank, p.nb) for p in self.players], reverse=True)):
            p = self.players[n]
            p.rank = i + 1
            lap = max(1, int(1 + p.progress // len(self.gates)))
            if lap > self.laps:
                p.txt_lap_title.visible = False
                p.txt_lap.visible = False
                p.txt_lap_total.visible = False
            p.txt_lap.text = str(lap)
            p.txt_rank.text = '?' if p.progress < 0 else str(p.rank)

    def change_state(self, nstate):
        stop = 'state__' + self.state + '__stop'
        if stop in dir(self): getattr(self, stop)()
        start = 'state__' + nstate + '__start'
        if start in dir(self): getattr(self, start)()
        tick = 'state__' + nstate + '__tick'
        self.state_tick = getattr(self, tick) if tick in dir(self) else self.tick_null
        self.state = nstate

    def state__getready__start(self):
        self.t = 0
        for p in self.players:
            p.ready = False
            p.txt_ready.text = 'Appuyez\nsur « A »'
            p.txt_ready.visible = True

    def state__getready__stop(self):
        for p in self.players:
            p.txt_ready.visible = False

    def state__getready__tick(self, dt):
        self.t += dt
        ready = sum(p.ready for p in self.players)

        for p in self.players:
            p.joystick.fetch_values()
            if p.joystick.button(BTN_A, True):
                if not ready: self.t = 0
                p.ready = True
                p.txt_ready.text = 'Prêt'

        if ready == len(self.players) and self.t > 1.5:
            self.change_state('countdown')

    def state__countdown__start(self):
        self.t = 3.1
        self.state__countdown__tick(0)
        for p in self.players:
            p.txt_countdown.visible = True

    def state__countdown__stop(self):
        for p in self.players:
            p.txt_countdown.text = ''
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
                p.process_pilot()
        if self.t < -0.5:
            self.change_state('race')

    def state__race__start(self):
        self.t = 1
        for p in self.players:
            p.reset()

            p.txt_lap.text = '1'
            p.txt_lap_total.text = '/' + str(self.laps)
            p.txt_rank.text = '?'
            p.txt_rank_total.text = '/' + str(len(self.players))

            p.bar_boost_bg.visible = True
            p.bar_boost.visible = True
            p.boost_mask.visible = True
            p.txt_lap_title.visible = True
            p.txt_lap.visible = True
            p.txt_lap_total.visible = True
            p.txt_rank_title.visible = True
            p.txt_rank.visible = True
            p.txt_rank_total.visible = True
            p.txt_time_title.visible = True
            p.txt_time.visible = True
            p.txt_besttime_title.visible = True
            p.txt_besttime.visible = True

    def state__race__stop(self):
        for p in self.players:
            p.bar_boost_bg.visible = False
            p.bar_boost.visible = False
            p.boost_mask.visible = False
            p.txt_lap_title.visible = False
            p.txt_lap.visible = False
            p.txt_lap_total.visible = False
            p.txt_rank_title.visible = False
            p.txt_rank.visible = False
            p.txt_rank_total.visible = False
            p.txt_time_title.visible = False
            p.txt_time.visible = False
            p.txt_besttime_title.visible = False
            p.txt_besttime.visible = False

    def state__race__tick(self, dt):
        self.t += dt
        str_t = time2str(self.t)
        if sum(p.duration is not None and self.t - p.duration_timestamp > 10 for p in self.players) == len(self.players):
            self.change_state('endgame')
        for p in self.players:
            if p.duration:
                p.txt_time.text = p.duration
                p.pilot.allow_boost(False)
            else:
                p.txt_time.text = str_t
                p.pilot.allow_boost(p.boost_allowed)
                if p.pilot.boost_used():
                    p.boost -= dt / 3
                    p.boost -= dt / 1.5 * p.throttle**2
                else:
                    p.boost += dt / 20 * (1 - 2 * abs(p.throttle))
                p.boost = min(1, p.boost)
                if p.boost > 0.75: p.boost_allowed = True
                if p.boost < 0.5 and not p.pilot.boost_used(): p.boost_allowed = False
                if p.boost < 0: p.boost_allowed = False
            p.bar_boost.height = max(p.boost, 0)*160
            p.process_pilot()

    def state__endgame__start(self):
        self.t = 0
        for p in self.players:
            p.bar_boost_bg.visible = True
            p.bar_boost.visible = True
            p.boost_mask.visible = True
            p.txt_rank_title.visible = True
            p.txt_rank.visible = True
            p.txt_rank_total.visible = True
            p.txt_time_title.visible = True
            p.txt_time.visible = True
            p.txt_besttime_title.visible = True
            p.txt_besttime.visible = True

    def state__endgame__stop(self):
        for p in self.players:
            p.reset()
            p.bar_boost_bg.visible = False
            p.bar_boost.visible = False
            p.boost_mask.visible = False
            p.txt_rank_title.visible = False
            p.txt_rank.visible = False
            p.txt_rank_total.visible = False
            p.txt_time_title.visible = False
            p.txt_time.visible = False
            p.txt_besttime_title.visible = False
            p.txt_besttime.visible = False

    def state__endgame__tick(self, dt):
        self.t += dt
        for p in self.players:
            p.joystick.fetch_values()
            if p.joystick.button(BTN_MODE, True):
                self.change_state('getready')
        if self.t > 60:
            self.change_state('getready')

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
    def __init__(self, car, joystick, gm, nb):
        self.nb = nb
        self.ip = car['ip']
        self.gm = gm
        self.ready = False

        self.joystick = joystick
        self.pilot = JoystickPilot(joystick)
        self.cartx = CarMessageUdpTx()
        self.forge = CarMessageForge()
        self.cartx.setDestination((car['ip'], car['port']))
        rnd_pass = random.randbytes(6)
        self.cartx.useAdminLevel()
        self.cartx.send(
            self.forge.cmd_change_pass_lvl1(rnd_pass) +
            self.forge.cmd_change_pass_lvl2(rnd_pass) +
            self.forge.cmd_limit_speed(32767, -16000)
        )
        self.cartx.usePrivilegeLevel(1, rnd_pass)

        x0 = nb * gm.winw
        self.txt_ready = pyglet.text.Label('', x=x0+gm.winw//2, y=gm.window.height//2, width=gm.winw, font_size=20, color=(30, 180, 0, 255), anchor_x='center', align='center', multiline=True, batch=gm.batch)
        self.txt_ready.visible = False
        self.txt_countdown = pyglet.text.Label('', x=x0+gm.winw//2, y=gm.window.height//2, font_size=50, color=(210, 210, 210, 255), anchor_x='center', batch=gm.batch)
        self.txt_countdown.visible = False

        mid = x0+10+gm.winw//2
        self.bar_boost_bg = pyglet.shapes.Rectangle(x=x0+15, y=20, width=20, height=160, color=(0xCC, 0xCC, 0xCC), batch=gm.batch)
        self.bar_boost_bg.visible = False
        self.bar_boost = pyglet.shapes.Rectangle(x=x0+15, y=20, width=20, height=160, color=(0x00, 0x88, 0xAA), batch=gm.batch)
        self.bar_boost.visible = False
        self.boost_mask = pyglet.sprite.Sprite(img=gm.img_boost_mask, x=x0+10, y=15, batch=gm.batch)
        self.boost_mask.visible = False
        self.txt_lap_title = pyglet.text.Label('Tour', x=x0+40, y=160, font_size=10, color=(120, 120, 120, 255), anchor_x='center', anchor_y='top', rotation=-90, batch=gm.batch)
        self.txt_lap_title.visible = False
        self.txt_lap = pyglet.text.Label('', x=mid+15, y=150, font_size=30, color=(0, 0, 0, 255), anchor_x='right', batch=gm.batch)
        self.txt_lap.visible = False
        self.txt_lap_total = pyglet.text.Label('', x=mid+15, y=150, font_size=15, color=(120, 120, 120, 255), anchor_x='left', batch=gm.batch)
        self.txt_lap_total.visible = False
        self.txt_rank_title = pyglet.text.Label('Rang', x=x0+40, y=120, font_size=10, color=(120, 120, 120, 255), anchor_x='center', anchor_y='top', rotation=-90, batch=gm.batch)
        self.txt_rank_title.visible = False
        self.txt_rank = pyglet.text.Label('', x=mid+15, y=110, font_size=30, color=(0, 0, 0, 255), anchor_x='right', batch=gm.batch)
        self.txt_rank.visible = False
        self.txt_rank_total = pyglet.text.Label('', x=mid+15, y=110, font_size=15, color=(120, 120, 120, 255), anchor_x='left', batch=gm.batch)
        self.txt_rank_total.visible = False
        self.txt_time_title = pyglet.text.Label('Temps de course', x=mid, y=80, font_size=10, color=(120, 120, 120, 255), anchor_x='center', batch=gm.batch)
        self.txt_time_title.visible = False
        self.txt_time = pyglet.text.Label('--:--.--', x=mid, y=60, font_size=15, color=(0, 0, 0, 255), anchor_x='center', batch=gm.batch)
        self.txt_time.visible = False
        self.txt_besttime_title = pyglet.text.Label('Meilleur tour', x=mid, y=40, font_size=10, color=(120, 120, 120, 255), anchor_x='center', batch=gm.batch)
        self.txt_besttime_title.visible = False
        self.txt_besttime = pyglet.text.Label('--:--.--', x=mid, y=20, font_size=15, color=(0, 0, 0, 255), anchor_x='center', batch=gm.batch)
        self.txt_besttime.visible = False

        self.reset()

    def reset(self):
        self.rank = -1
        self.progress = -1
        self.progress_next_gate = self.gm.gates[0]
        self.progress_prev_gate = self.gm.gates[-1]
        self.duration = None
        self.bestlap_time = 1e9
        self.lapstart = None
        self.throttle = 0
        self.boost = 0.5
        self.boost_allowed = False
        self.pilot.allow_boost(False)

        self.cartx.send(self.forge.cmd_engine_on())
        self.engine_on = True

    def process_pilot(self):
        self.pilot.decode()

        msg = b''

        j = self.pilot.joystick()
        if j.button(BTN_START, True):
            self.engine_on = not self.engine_on
            msg += self.forge.cmd_engine_on(self.engine_on)

        btn_x = j.button(BTN_X, True)
        if btn_x is not None:
            if self.engine_on:
                msg += self.forge.cmd_headlights(65535 if btn_x else 20000)

        throttle, steering = self.pilot.pilot_commands()
        if self.duration:
            reduc_fact = 1-(self.gm.t - self.duration_timestamp)/10
            if reduc_fact < 0 or reduc_fact > 1: reduc_fact = 0
            throttle *= reduc_fact
        self.throttle = throttle
        msg += self.forge.cmd_pilot(int(throttle*32767), int(steering*32767))

        self.cartx.send(msg)

    def set_color(self, r, g, b):
        if self.boost_allowed:
            self.bar_boost.color = (r, g, b, 255)
        else:
            self.bar_boost.color = (r//2, g//2, b//2, 128)

    def set_gate(self, gate):
        if gate == self.progress_next_gate:
            self.progress += 1
            if self.progress == len(self.gm.gates) * self.gm.laps:
                self.duration_timestamp = self.gm.t
                self.duration = time2str(self.duration_timestamp)
                self.progress_next_gate = self.progress_prev_gate = None
            else:
                self.progress_next_gate = self.gm.gates[(self.progress+1)%len(self.gm.gates)]
                self.progress_prev_gate = self.gm.gates[(self.progress-1)%len(self.gm.gates)]
            if self.progress % len(self.gm.gates) == 0:
                if self.lapstart:
                    d = self.gm.t - self.lapstart
                    if d < self.bestlap_time:
                        self.txt_besttime.text = time2str(d)
                        self.bestlap_time = d
                self.lapstart = self.gm.t
            self.gm.recompute_ranks()
        elif gate == self.progress_prev_gate:
            self.progress -= 1
            self.progress_next_gate = self.gm.gates[(self.progress+1)%len(self.gm.gates)]
            self.progress_prev_gate = self.gm.gates[(self.progress-1)%len(self.gm.gates)]
            self.gm.recompute_ranks()


def define_players(detector, gm):
    nb_cars = choice_input(['One car', 'Two cars', 'Three cars', 'Four cars', 'No cars'], 'How many cars?')
    if nb_cars == 5: nb_cars = 0
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

    gm = GameManager(b'HACKER', 2)
    gm.set_players(define_players(detector, gm))
    gm.start()

    pyglet.clock.schedule_interval(gm.tick, 0.005)
    pyglet.app.run()

