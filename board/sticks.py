"""Thumbsticks wired to the ADS1115, read as numbers from -1.0 to 1.0.

    import sticks

    left, right = sticks.connect(i2c)
    print(left.x, left.y, left.pressed)

x is -1.0 all the way left and 1.0 all the way right. y is -1.0 pushed up (away
from you) and 1.0 pulled down. That is the same way round as a browser gamepad,
so a number read here arrives in a game unchanged.

Inside, each stick is two potentiometers across 3.3 V, so a centered stick reads
about 1.65 V -- but never exactly, and each one differently. connect() measures
every center while the sticks are untouched, so keep your thumbs off them for
the first half second.

A released stick does not spring back to quite the same spot each time, so
anything within dead_zone of center reads exactly 0.0. Change it per stick:
left.dead_zone = 0.1.

Reading .x or .y asks the ADS1115 for a fresh measurement, about 2 ms each. Read
each one once per loop and keep it in a variable.
"""

import board
import digitalio
from adafruit_ads1x15 import ADS1115, AnalogIn

ADDRESS = 0x48  # the ADS1115's ADDR pin wired to GND
# The fastest setting. The library's default, 128, makes four channels take
# 39 ms instead of 8.
SAMPLES_PER_SECOND = 860
CENTER_READINGS = 40  # averaged to find where a stick rests


class Stick:
    """One thumbstick: two ADS1115 channels and, optionally, its push switch."""

    def __init__(self, ads, x_channel, y_channel, dead_zone=0.06, flip_x=1, flip_y=1):
        self.dead_zone = dead_zone
        self.flip_x = flip_x  # set to -1 if this stick reads backwards
        self.flip_y = flip_y
        self._x = AnalogIn(ads, x_channel)
        self._y = AnalogIn(ads, y_channel)
        self.center_x = _average_volts(self._x)
        self.center_y = _average_volts(self._y)

    @property
    def x(self):
        """-1.0 (left) .. 1.0 (right)."""
        return self._position(self._x.voltage, self.center_x) * self.flip_x

    @property
    def y(self):
        """-1.0 (pushed up) .. 1.0 (pulled down)."""
        return self._position(self._y.voltage, self.center_y) * self.flip_y

    def _position(self, volts, center):
        # A centered stick sits at half the supply, so it can travel about one
        # center's worth of volts either way.
        position = (volts - center) / center
        size = abs(position)
        if size < self.dead_zone:
            return 0.0
        # Start again from 0 at the edge of the dead zone, so there is no jump.
        size = min((size - self.dead_zone) / (1 - self.dead_zone), 1.0)
        if position < 0:
            return -size
        return size


def _average_volts(channel):
    total = 0.0
    for _ in range(CENTER_READINGS):
        total += channel.voltage
    return total / CENTER_READINGS


def connect(i2c, dead_zone=0.06):
    """Both sticks on the ADS1115: (left, right). Left is A0/A1, right is A2/A3."""
    ads = ADS1115(i2c, address=ADDRESS, data_rate=SAMPLES_PER_SECOND)
    left = Stick(ads, 0, 1, dead_zone)
    right = Stick(ads, 2, 3, dead_zone)
    return left, right
