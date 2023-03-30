#!/usr/bin/env python3

import evdev
from evdev.ecodes import BTN_A, BTN_B, BTN_X, BTN_Y, BTN_TL, BTN_TR
from evdev.ecodes import BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL, BTN_THUMBR
from evdev.ecodes import ABS_X, ABS_Y, ABS_Z, ABS_RX, ABS_RY, ABS_RZ

class Joystick:
    def __init__(self, path, showcaps=False):
        self.dev = evdev.InputDevice(path)
        self.keys = {}
        self.keys_just_pressed = {}
        self.axes = {}
        self.axes_info = {}
        self.effects = None

        if showcaps:
            print(self.dev.capabilities(verbose=True))
        caps = self.dev.capabilities()
        if evdev.ecodes.EV_KEY in caps:
            for k in caps[evdev.ecodes.EV_KEY]:
                self.keys[k] = False

        if evdev.ecodes.EV_ABS in caps:
            for k,info in caps[evdev.ecodes.EV_ABS]:
                self.axes[k] = 0
                self.axes_info[k] = info

        if evdev.ecodes.EV_FF in caps and evdev.ecodes.FF_RUMBLE in caps[evdev.ecodes.EV_FF]:
            self.effects = []
            self._add_rumble_effects()

    def __del__(self):
        if self.effects:
            for effect_id in self.effects:
                self.dev.erase_effect(effect_id)

    def _add_rumble_effects(self):
        self.effects.append(
            self.dev.upload_effect(
                evdev.ff.Effect(
                    evdev.ecodes.FF_RUMBLE, -1, 0,
                    evdev.ff.Trigger(0, 0),
                    evdev.ff.Replay(length=200, delay=0),
                    evdev.ff.EffectType(ff_rumble_effect=evdev.ff.Rumble(
                            strong_magnitude=0x7fff,
                            weak_magnitude=0x0000
                    ))
                )
            )
        )
        self.effects.append(
            self.dev.upload_effect(
                evdev.ff.Effect(
                    evdev.ecodes.FF_RUMBLE, -1, 0,
                    evdev.ff.Trigger(0, 0),
                    evdev.ff.Replay(length=200, delay=0),
                    evdev.ff.EffectType(ff_rumble_effect=evdev.ff.Rumble(
                            strong_magnitude=0xffff,
                            weak_magnitude=0x0000
                    ))
                )
            )
        )
        self.effects.append(
            self.dev.upload_effect(
                evdev.ff.Effect(
                    evdev.ecodes.FF_RUMBLE, -1, 0,
                    evdev.ff.Trigger(0, 0),
                    evdev.ff.Replay(length=200, delay=0),
                    evdev.ff.EffectType(ff_rumble_effect=evdev.ff.Rumble(
                            strong_magnitude=0x0000,
                            weak_magnitude=0x7fff
                    ))
                )
            )
        )
        self.effects.append(
            self.dev.upload_effect(
                evdev.ff.Effect(
                    evdev.ecodes.FF_RUMBLE, -1, 0,
                    evdev.ff.Trigger(0, 0),
                    evdev.ff.Replay(length=200, delay=0),
                    evdev.ff.EffectType(ff_rumble_effect=evdev.ff.Rumble(
                            strong_magnitude=0x0000,
                            weak_magnitude=0xffff
                    ))
                )
            )
        )

    def name(self):
        return self.dev.name

    def fetch_values(self):
        self.keys_just_pressed = {}
        try:
            for event in self.dev.read():
                # DEBUG: print(evdev.util.categorize(event))
                if event.type == evdev.ecodes.EV_ABS:
                    self.axes[event.code] = event.value
                elif event.type == evdev.ecodes.EV_KEY:
                    self.keys[event.code] = (event.value != 0)
                    self.keys_just_pressed[event.code] = (event.value != 0)
        except BlockingIOError:
            pass

    def button(self, code, just_pressed=False):
        if just_pressed:
            return self.keys_just_pressed.get(code, None)
        else:
            return self.keys.get(code, False)

    def axis(self, code, centered=True):
        v = self.axes.get(code, None)
        if v is None: return 0
        vmin = self.axes_info[code].min
        vmax = self.axes_info[code].max
        vscaled = (v - vmin) / (vmax - vmin)
        if centered:
            vscaled = 2 * vscaled - 1
            if abs(vscaled) < 0.1: vscaled = 0
        if abs(vscaled) < 0.001: vscaled = 0
        return vscaled

    def rumble(self, nb):
        if self.effects and nb < len(self.effects):
            self.dev.write(evdev.ecodes.EV_FF, self.effects[nb], 1)

def choose_joystick(showcaps=False):
    from input_utils import choice_input
    while True:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        devices = list(filter(lambda dev: evdev.ecodes.EV_ABS in dev.capabilities() and evdev.ecodes.EV_KEY in dev.capabilities(), devices))
        names = ["[Refresh list]"] + ["\t".join((device.path, device.name, device.phys)) for device in devices]
        nb = choice_input(names, 'Which joystick to use?', 'No joystick found, reload list?')
        if nb and nb > 1:
            return Joystick(devices[nb - 2].path, showcaps)
        if nb is None: return None

class JoystickPilot:
    def __init__(self, joystick):
        self._joystick = joystick

        self._boost_allowed = True
        self._assisted_mode = True

        self._boost_used = False
        self._speed = 0
        self._steering = 0

    def decode(self):
        j = self._joystick
        j.fetch_values()

        if j.button(BTN_SELECT, True):
            self._assisted_mode = not self._assisted_mode

        throttle_fw = j.axis(ABS_RZ, False)
        throttle_bw = j.axis(ABS_Z, False)

        speed = throttle_fw - throttle_bw
        if throttle_fw and throttle_bw: speed = 0 # Stop car if both trigger buttons are pressed

        self._boost_used = self._boost_allowed and j.button(BTN_A)
        if not self._boost_used:
            speed *= 0.25

        steering = j.axis(ABS_X)
        if self._assisted_mode: # In assist mode, limit steering angle based on speed (more speed, less steering angle)
            steering = steering * abs(steering) * (1-abs(speed)*0.9)

        self._speed = speed
        self._steering = steering

    def joystick(self):
        return self._joystick

    def set_assistance(self, v=True):
        self._assisted_mode = v

    def assistance_enabled(self):
        return self._assisted_mode

    def boost_used(self):
        return self._boost_used

    def pilot_commands(self):
        return self._speed, self._steering

    def allow_boost(self, v=True):
        self._boost_allowed = v

if __name__ == '__main__':
    import time

    j = choose_joystick(True)
    pilot = JoystickPilot(j)

    print(j.name())
    while True:
        pilot.decode()
        speed, steer = pilot.pilot_commands()
        print('CMD', speed, steer)
        time.sleep(.1)

        if abs(speed) > 0.8: j.rumble(3)
        elif abs(speed) > 0.4:  j.rumble(2)
