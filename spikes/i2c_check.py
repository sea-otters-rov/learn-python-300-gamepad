"""Spike: SEN0140 and ADS1115 sharing one I2C bus on the XIAO RP2350.

Run from the REPL with `import i2c_check`. Does not touch code.py.
"""

import time

from adafruit_ads1x15 import ADS1115, AnalogIn

import imu

ADS_ADDRESS = 0x48
ROUNDS = 3
READS = 20


def ms_per(fn, count):
    start = time.monotonic_ns()
    for _ in range(count):
        fn()
    return (time.monotonic_ns() - start) / count / 1e6


print("--- scan")
i2c = imu.open_i2c()
while not i2c.try_lock():
    pass
found = i2c.scan()
i2c.unlock()
for address in found:
    name = "ADC (ADS1115)" if address == ADS_ADDRESS else imu.guess(address)
    print(f"  0x{address:02X}  {name}")
print(f"  {len(found)} devices, ADS1115 {'present' if ADS_ADDRESS in found else 'MISSING'}")

print("--- one bus object, both drivers")
sensors = imu.IMU(i2c)
ads = ADS1115(i2c, address=ADS_ADDRESS)
channels = [AnalogIn(ads, pin) for pin in range(4)]
sensors.report()

print("--- readings (inputs floating, so the ADC numbers mean nothing yet)")
for _ in range(5):
    ax, ay, az = sensors.acceleration
    volts = " ".join(f"{c.voltage:6.3f}" for c in channels)
    print(f"  accel {ax:6.2f} {ay:6.2f} {az:6.2f}  hPa {sensors.pressure:8.2f}  V {volts}")
    time.sleep(0.2)

print("--- timing, ms per call, interleaved rounds")


def read_four():
    for c in channels:
        c.value


def read_imu():
    sensors.acceleration
    sensors.rotation


for round_number in range(ROUNDS):
    row = []
    for rate in (128, 860):
        ads.data_rate = rate
        row.append(f"4 ch @{rate:>3} SPS {ms_per(read_four, READS):6.2f}")
    row.append(f"accel+gyro {ms_per(read_imu, READS):5.2f}")
    print(f"  round {round_number + 1}:  " + "   ".join(row))
print("--- done")
