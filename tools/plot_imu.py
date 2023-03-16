#!/usr/bin/env python3

import time
from cardetector import CarDetector
from carmessagesrx import CarMulticastReceiver, CarMulticastDecoder
import matplotlib.pyplot as plt
import numpy as np
from select import select

if __name__ == '__main__':
    detector = CarDetector()
    detector.start()

    print('Select car')
    car = detector.choose_car()['ip']

    x_vec = np.linspace(-100, 0)[0:-1]
    y_vecs = {
        'imu_a_x': np.zeros(len(x_vec), dtype=int),
        'imu_a_y': np.zeros(len(x_vec), dtype=int),
        'imu_a_z': np.zeros(len(x_vec), dtype=int),
        'imu_g_x': np.zeros(len(x_vec), dtype=int),
        'imu_g_y': np.zeros(len(x_vec), dtype=int),
        'imu_g_z': np.zeros(len(x_vec), dtype=int),
    }
    def add(key, value):
        y_vecs[key] = np.roll(y_vecs[key], -1)
        y_vecs[key][-1] = value

    running = True
    def on_closed(event):
        global running
        running = False

    plt.ion()
    fig = plt.figure(figsize=(12,8))
    fig.canvas.mpl_connect('close_event', on_closed)
    fig.suptitle('IMU data')

    ax = {}
    ax['imu_a'] = fig.add_subplot(211)
    ax['imu_g'] = fig.add_subplot(212, sharex = ax['imu_a'])
    lines = {}
    for k in y_vecs:
        lines[k], = ax[k[:5]].plot(x_vec, y_vecs[k], '-o', label=k)        
    for a in ax:
        ax[a].set_ylabel('Value LSB')
        ax[a].set_ylim([-32768, 32768])
        ax[a].legend(loc='upper left')

    plt.tight_layout()
    fig.subplots_adjust(hspace=0)
    plt.show()

    receiver = CarMulticastReceiver()
    decoder = CarMulticastDecoder()
    last_plot = 0
    try:
        while running:
            rlist, _, _ = select([receiver], [], [])
            if rlist:
                packet, sender = receiver.recv()
                msgs = decoder.decode(packet)
                replot = False
                if sender[0] == car:
                    for m in msgs:
                        for k in m:
                            if k in y_vecs:
                                replot = True
                                add(k, m[k])
                now = time.time()
                if replot and now - last_plot > 0.1:
                    last_plot = now
                    for k in y_vecs:
                        lines[k].set_ydata(y_vecs[k])
                    plt.pause(0.001)
    except KeyboardInterrupt:
        pass
