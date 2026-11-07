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
left.dead_zone = 0.1. In the same way, a stick pushed within edge of the end
reads exactly 1.0, because pushed all the way it stops a little short.

Reading .x or .y asks the ADS1115 for a fresh measurement, about 2 ms each. Read
each one once per loop and keep it in a variable.
"""

import time

import board
import digitalio
from adafruit_ads1x15 import ADS1115, AnalogIn

ADDRESS = 0x48  # the ADS1115's ADDR pin wired to GND
# The fastest setting. The library's default, 128, makes four channels take
# 39 ms instead of 8.
SAMPLES_PER_SECOND = 860
CENTER_READINGS = 40  # averaged to find where a stick rests
# Pushed all the way toward 0 V, a stick reads exactly 0 V. Toward 3.3 V it
# stops a little short (measured: 1.6% short), so it would never quite reach
# 1.0. Anything within EDGE of the end reads 1.0.
EDGE = 0.04
CONNECT_TRIES = 10  # asking the ADS1115 to answer, CONNECT_WAIT seconds apart
CONNECT_WAIT = 0.05


class Stick:
    """One thumbstick: two ADS1115 channels and, optionally, its push switch."""

    def __init__(self, ads, x_channel, y_channel, dead_zone=0.06, flip_x=1, flip_y=1):
        self.dead_zone = dead_zone
        self.edge = EDGE
        self.flip_x = flip_x  # set to -1 if this stick reads backwards
        self.flip_y = flip_y
        self._x = AnalogIn(ads, x_channel)
        self._y = AnalogIn(ads, y_channel)
        self.center_x = _average_volts(self._x)
        self.center_y = _average_volts(self._y)

    # + 0.0 turns the -0.0 that a flipped 0.0 makes into 0.0, so a resting stick
    # never prints as "-0.00".

    @property
    def x(self):
        """-1.0 (left) .. 1.0 (right)."""
        return self._position(self._x.voltage, self.center_x) * self.flip_x + 0.0

    @property
    def y(self):
        """-1.0 (pushed up) .. 1.0 (pulled down)."""
        return self._position(self._y.voltage, self.center_y) * self.flip_y + 0.0

    def _position(self, volts, center):
        # A centered stick sits at half the supply, so it can travel about one
        # center's worth of volts either way.
        position = (volts - center) / center
        size = abs(position)
        if size < self.dead_zone:
            return 0.0
        # Start again from 0 at the edge of the dead zone, so there is no jump,
        # and reach 1.0 edge short of the end.
        size = min((size - self.dead_zone) / (1 - self.dead_zone - self.edge), 1.0)
        if position < 0:
            return -size
        return size


def _average_volts(channel):
    total = 0.0
    for _ in range(CENTER_READINGS):
        total += channel.voltage
    return total / CENTER_READINGS


def _scan(i2c):
    """Every address that answers on the bus."""
    while not i2c.try_lock():
        pass
    try:
        return i2c.scan()
    finally:
        i2c.unlock()


def _explain(found):
    """What to tell a student when the ADS1115 does not answer at ADDRESS.

    found is the list of addresses that did answer, e.g. [0x0C, 0x53, 0x68, 0x77]
    for the tilt sensor alone.
    """
    listed = " ".join(f"0x{a:02X}" for a in found) or "nothing"
    listed = f"Found on the bus: {listed}."
    # The ADS1115 takes its address from what its ADDR pin is wired to: GND is
    # 0x48, and these are the other three.
    wired_to = {0x49: "3V3", 0x4A: "SDA", 0x4B: "SCL"}
    for address, pin in wired_to.items():
        if address in found:
            return (
                f"{listed} The ADS1115 answers at 0x{address:02X} instead: its ADDR"
                f" pin is wired to {pin}. Move that wire to GND."
            )
    if not found:
        return f"{listed} No chip answers: check SDA on D4, SCL on D5, 3V3 and GND."
    return (
        f"{listed} Other chips answer, so the bus works: check the ADS1115's"
        " own 3V3, GND, SDA and SCL wires."
    )


def _open_ads(i2c):
    # Sometimes, just after the USB cable goes in, the ADS1115 does not answer
    # yet. Ask a few times before giving up, and say so if it took more than one.
    for attempt in range(CONNECT_TRIES):
        try:
            ads = ADS1115(i2c, address=ADDRESS, data_rate=SAMPLES_PER_SECOND)
        except ValueError:
            time.sleep(CONNECT_WAIT)
            continue
        if attempt:
            print(f"sticks: the ADS1115 answered on try {attempt + 1}")
        return ads
    raise RuntimeError(f"No ADS1115 at 0x{ADDRESS:02X}. {_explain(_scan(i2c))}")


def connect(i2c, dead_zone=0.06):
    """Both sticks on the ADS1115: (left, right). Left is A0/A1, right is A2/A3."""
    ads = _open_ads(i2c)
    left = Stick(ads, 0, 1, dead_zone)
    right = Stick(ads, 2, 3, dead_zone)
    return left, right
