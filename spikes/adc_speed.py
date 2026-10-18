"""Spike: what does an analog reading cost, and how much of it can we get back?

Interleaved rounds; each round reopens the bus at 100 kHz and at 400 kHz.
"""

import time

import analogio
import board
import busio
from adafruit_ads1x15 import ADS1115, AnalogIn
from adafruit_bus_device.i2c_device import I2CDevice

import imu

ROUNDS = 3
READS = 20
SETTLE_NS = 1_300_000  # 1/860 s is 1.163 ms; the ADS oscillator is +-10%


def ms_per(fn, count=READS):
    start = time.monotonic_ns()
    for _ in range(count):
        fn()
    return (time.monotonic_ns() - start) / count / 1e6


class RawADS:
    """Single-shot ADS1115 reads with no library in the way."""

    def __init__(self, i2c):
        self.device = I2CDevice(i2c, 0x48)
        self.out = bytearray(3)
        self.pointer = bytearray(1)  # 0 = conversion register
        self.into = bytearray(2)

    def start(self, channel):
        # start | AINx vs GND | +-4.096 V | single shot | 860 SPS | no comparator
        config = 0x8000 | (4 + channel) << 12 | 1 << 9 | 0x0100 | 7 << 5 | 3
        self.out[0] = 1
        self.out[1] = config >> 8
        self.out[2] = config & 0xFF
        with self.device as d:
            d.write(self.out)

    def result(self):
        with self.device as d:
            d.write_then_readinto(self.pointer, self.into)
        value = self.into[0] << 8 | self.into[1]
        return value - 65536 if value & 0x8000 else value

    def read(self, channel):
        self.start(channel)
        done = time.monotonic_ns() + SETTLE_NS
        while time.monotonic_ns() < done:
            pass
        return self.result()


internal = analogio.AnalogIn(board.A0)
results = {}

for round_number in range(ROUNDS):
    for frequency in (100_000, 400_000):
        i2c = busio.I2C(board.SCL, board.SDA, frequency=frequency)
        sensors = imu.IMU(i2c)
        ads = ADS1115(i2c, data_rate=860)
        lib_channels = [AnalogIn(ads, pin) for pin in range(4)]
        raw = RawADS(i2c)

        if round_number == 0:
            lib_counts = [c.value >> 0 for c in lib_channels]
            raw_counts = [raw.read(ch) for ch in range(4)]
            print(f"{frequency // 1000} kHz  library {lib_counts}  raw {raw_counts}")

        k = frequency // 1000
        tests = {
            f"ADS library, 4 ch       @{k}": lambda: [c.value for c in lib_channels],
            f"ADS raw, 4 ch           @{k}": lambda: [raw.read(ch) for ch in range(4)],
            f"ADS raw, I2C only x4    @{k}": lambda: [
                (raw.start(ch), raw.result()) for ch in range(4)
            ],
            f"accelerometer only      @{k}": lambda: sensors.acceleration,
            f"accel + gyro            @{k}": lambda: (
                sensors.acceleration,
                sensors.rotation,
            ),
        }
        for name, fn in tests.items():
            results.setdefault(name, []).append(ms_per(fn))
        i2c.deinit()

    results.setdefault("internal ADC, 4 reads", []).append(
        ms_per(lambda: [internal.value for _ in range(4)])
    )

print("--- ms per call, best / worst of rounds")
for name in sorted(results):
    times = results[name]
    print(f"  {name:<34} {min(times):7.3f} {max(times):7.3f}")
print("--- done")
