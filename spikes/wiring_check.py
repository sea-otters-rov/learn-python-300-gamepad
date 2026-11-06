"""Spike: is anything on the I2C pins, and does the D0 button read?

An idle I2C bus sits HIGH, pulled up by resistors on the breakouts -- but only
if a breakout is powered and wired to that pin. A pin that reads high with no
internal pull-up therefore says "something powered is pulling this line up";
a floating or grounded line says otherwise.
"""

import time

import board
import busio
import digitalio

print("board.SDA is D4:", board.SDA is board.D4, " board.SCL is D5:", board.SCL is board.D5)

for name, pin in (("SDA (D4)", board.SDA), ("SCL (D5)", board.SCL)):
    line = digitalio.DigitalInOut(pin)
    line.switch_to_input(pull=None)
    readings = []
    for _ in range(20):
        readings.append(line.value)
        time.sleep(0.005)
    print(f"{name}: high {readings.count(True)} of {len(readings)} with no pull-up")
    line.deinit()

# Sharper: drive the line low, let go, and count reads until it is high again.
# A breakout's pull-up (a few kilohms) brings it back within the first read or
# two; a floating wire stays low far longer -- or reads high only by chance.
for name, pin in (("SDA (D4)", board.SDA), ("SCL (D5)", board.SCL)):
    line = digitalio.DigitalInOut(pin)
    line.switch_to_output(value=False)
    time.sleep(0.01)
    line.switch_to_input(pull=None)
    reads = 0
    while not line.value and reads < 100_000:
        reads += 1
    verdict = "pulled up" if reads < 5 else "NOT pulled up (floating)"
    print(f"{name}: high again after {reads} reads -> {verdict}")
    line.deinit()

for frequency in (100_000, 400_000):
    try:
        i2c = busio.I2C(board.SCL, board.SDA, frequency=frequency)
    except Exception as error:  # noqa: BLE001 -- the message is the finding
        print(f"busio.I2C at {frequency}: {error}")
        continue
    while not i2c.try_lock():
        pass
    found = [hex(address) for address in i2c.scan()]
    i2c.unlock()
    i2c.deinit()
    print(f"scan at {frequency}: {found}")

# bitbangio does I2C in software on any two pins, so it can try the wires
# both ways round -- the hardware I2C cannot swap SDA and SCL.
import bitbangio  # noqa: E402

for label, scl, sda in (("as wired in code", board.SCL, board.SDA), ("SWAPPED", board.SDA, board.SCL)):
    try:
        i2c = bitbangio.I2C(scl, sda, frequency=50_000)
    except Exception as error:  # noqa: BLE001
        print(f"bitbang {label}: {error}")
        continue
    while not i2c.try_lock():
        pass
    found = [hex(address) for address in i2c.scan()]
    i2c.unlock()
    i2c.deinit()
    print(f"bitbang scan {label}: {found}")

button = digitalio.DigitalInOut(board.D0)
button.switch_to_input(pull=digitalio.Pull.UP)
print("D0 with pull-up reads", button.value, "(False = pressed or shorted to GND)")
