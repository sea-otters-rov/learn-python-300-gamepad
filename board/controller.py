"""Spike: two analog sticks, tilt and four buttons, as one USB gamepad.

Left stick   ADS1115 A0 (x), A1 (y), click D7   -> left_x, left_y, LEFT_CLICK
Right stick  ADS1115 A2 (x), A3 (y), click D8   -> right_x, right_y, RIGHT_CLICK
Tilt         accelerometer x, y                 -> tilt_x, tilt_y
                                                   (right edge down +, far edge down -)
Buttons      D9, D10, D0, D1                    -> A, B, X, Y

With use_tilt = True, tilt ALSO drives the left stick (the marble maze).
Keep the sticks and the board still for the first half second: that is when
the centers and "level" are measured.
"""

import math
import time

import board
import busio
import digitalio

import gamepad
import imu
import sticks

use_tilt = False

full_tilt = 5.0  # m/s^2 for a full stick; 5 is about 30 degrees
tilt_dead_zone = 0.5  # m/s^2
tilt_flip = (1, 1)  # x, y

tap_jolt = 8.0  # m/s^2 away from gravity that counts as a tap
tap_hold = 0.15  # seconds

settle_samples = 40  # readings averaged for "level"

pad = gamepad.Gamepad()
i2c = busio.I2C(board.SCL, board.SDA, frequency=400_000)
sensors = imu.IMU(i2c)
right, left = sticks.connect(i2c)

buttons = []
for name, pin in (
    (gamepad.A, board.D9),
    (gamepad.B, board.D10),
    (gamepad.X, board.D0),
    (gamepad.Y, board.D1),
):
    switch = digitalio.DigitalInOut(pin)
    switch.switch_to_input(pull=digitalio.Pull.UP)  # pressed reads False
    buttons.append((name, switch))


def average(read, count):
    total = 0.0
    for _ in range(count):
        total += read()
    return total / count


# The board's x and y are the accelerometer's y and x (see the loop), so "level"
# is measured the same way round.
level_x = average(lambda: sensors.acceleration[1], settle_samples)
level_y = average(lambda: sensors.acceleration[0], settle_samples)
print(f"left center {left.center_x:.3f} {left.center_y:.3f} V", end="  ")
print(f"right center {right.center_x:.3f} {right.center_y:.3f} V")
print(f"level x {level_x:.2f}  y {level_y:.2f} m/s^2")


def tilt_amount(acceleration):
    """Acceleration from tipping the board into -1.0 .. 1.0, with a dead zone."""
    size = abs(acceleration)
    if size < tilt_dead_zone:
        return 0.0
    amount = min((size - tilt_dead_zone) / (full_tilt - tilt_dead_zone), 1.0)
    if acceleration < 0:
        return -amount
    return amount


tap_until = 0
next_report = time.monotonic()
loops = 0
while True:
    pad.left_x = left.x
    pad.left_y = left.y
    pad.right_x = -right.x
    pad.right_y = -right.y

    ay, ax, az = sensors.acceleration
    pad.tilt_x = tilt_amount(ax - level_x) * tilt_flip[0]
    pad.tilt_y = tilt_amount(ay - level_y) * tilt_flip[1]
    if use_tilt:
        pad.left_x = pad.tilt_x
        pad.left_y = pad.tilt_y

    for name, switch in buttons:
        pad.set_button(name, not switch.value)
    pad.set_button(gamepad.LEFT_CLICK, left.pressed)
    pad.set_button(gamepad.RIGHT_CLICK, right.pressed)

    now = time.monotonic()
    # if abs(math.sqrt(ax * ax + ay * ay + az * az) - 9.8) > tap_jolt:
    #     tap_until = now + tap_hold
    # pad.set_button(gamepad.A, now < tap_until)

    pad.send()
    loops += 1
    if now >= next_report:
        sticks_now = (pad.left_x, pad.left_y, pad.right_x, pad.right_y)
        # + 0.0 turns -0.0 (a flipped zero) into 0.0, so rest never shows "-0.00"
        shown = " ".join(
            f"{a + 0.0:5.2f}" for a in sticks_now + (pad.tilt_x, pad.tilt_y)
        )
        print(f"axes {shown}  buttons {pad.buttons:016b}  {loops // 2}/s")
        next_report = now + 2
        loops = 0
