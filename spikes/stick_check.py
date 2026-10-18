"""Spike: read both sticks and their switches at rest. Nobody touching them."""

import time

import board
import busio
import digitalio
from adafruit_ads1x15 import ADS1115, AnalogIn

SAMPLES = 200

i2c = busio.I2C(board.SCL, board.SDA, frequency=400_000)
ads = ADS1115(i2c, data_rate=860)
channels = [AnalogIn(ads, pin) for pin in range(4)]

switches = {}
for name in ("D7", "D8"):
    pin = digitalio.DigitalInOut(getattr(board, name))
    pin.switch_to_input(pull=digitalio.Pull.UP)
    switches[name] = pin

readings = [[] for _ in channels]
switch_lows = {name: 0 for name in switches}
start = time.monotonic()
for _ in range(SAMPLES):
    for i, channel in enumerate(channels):
        readings[i].append(channel.voltage)
    for name, pin in switches.items():
        if not pin.value:
            switch_lows[name] += 1
seconds = time.monotonic() - start

print(f"{SAMPLES} samples of 4 channels in {seconds:.2f} s")
for i, values in enumerate(readings):
    mean = sum(values) / len(values)
    spread = max(values) - min(values)
    print(
        f"  A{i}  mean {mean:.4f} V  min {min(values):.4f}  max {max(values):.4f}"
        f"  spread {spread * 1000:.1f} mV  ({spread / 3.3 * 254:.2f} stick counts)"
    )
for name, lows in switch_lows.items():
    print(f"  {name}  read pressed {lows} of {SAMPLES} times")
print("--- done")
