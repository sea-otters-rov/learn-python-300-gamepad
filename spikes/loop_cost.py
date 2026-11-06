"""Spike: what each part of controller.py's loop costs, in ms per call.

Run when the loop rate changes, to see which part moved. Measured on this
board's bus at 400 kHz, as controller.py runs it.
"""

import time

import board
import busio

import imu
import sticks

ROUNDS = 200

i2c = busio.I2C(board.SCL, board.SDA, frequency=400_000)
sensors = imu.IMU(i2c)
right, left = sticks.connect(i2c)
left.flip_x = -1
left.flip_y = -1


def board_acceleration():
    sensor_x, sensor_y, sensor_z = sensors.acceleration
    return sensor_y, sensor_x, sensor_z


def cost(label, job):
    start = time.monotonic_ns()
    for _ in range(ROUNDS):
        job()
    ms = (time.monotonic_ns() - start) / ROUNDS / 1_000_000
    print(f"{label:<34} {ms:6.3f} ms")


cost("sensors.acceleration", lambda: sensors.acceleration)
cost("board_acceleration()", board_acceleration)
cost("one stick axis (left.x)", lambda: left.x)
cost("four stick axes", lambda: (left.x, left.y, right.x, right.y))
