"""Spike: two analog sticks, tilt and nine buttons, as one USB gamepad.

Right stick  ADS1115 A0 (x), A1 (y)   -> right_x, right_y
Left stick   ADS1115 A2 (x), A3 (y)   -> left_x, left_y  (mounted turned 180 degrees)
Tilt         accelerometer            -> tilt_x, tilt_y
                                         (right edge down +, far edge down -)
Buttons      D7 D8 D9 D10             -> A B X Y
             D0 D1 D2 D3              -> LB RB LT RT
             D6                       -> START

How the sticks and the accelerometer sit on the breadboard is set in one place
each, below: "How this breadboard is built". A board built another way changes
only those lines.

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

# ---- How this breadboard is built ---------------------------------------------
# Check each on the Controller check page: push a stick up, its dot must go up
# (-1); push it right, right (+1). Tilt the right edge down, the tilt dot goes
# right; tip the far edge down, it goes up.
#
# connect() returns the stick wired to A0/A1 first. On this breadboard that one
# is on the RIGHT. If a board has them wired the other way round, swap the two
# names: left, right = sticks.connect(i2c)
right, left = sticks.connect(i2c)
# The left stick is mounted turned 180 degrees from the right one, so both of
# its axes read backwards. Mounted facing the same way as the right stick, delete
# these two lines. One axis wrong on its own? Flip only that one.
left.flip_x = -1
left.flip_y = -1


def board_acceleration():
    """(x, y, z) in m/s^2 the way the breadboard sees it, not the way the chip does.

    The SEN0140 sits turned on the breadboard: its y axis runs left-right across
    the breadboard and its x axis runs near-far. Mounted with its x axis
    left-right, return sensor_x, sensor_y, sensor_z instead. If a tilt then moves
    the dot along the right axis but the wrong way, change tilt_flip above.
    """
    sensor_x, sensor_y, sensor_z = sensors.acceleration
    return sensor_y, sensor_x, sensor_z


# -------------------------------------------------------------------------------

buttons = []
for name, pin in (
    (gamepad.A, board.D7),
    (gamepad.B, board.D8),
    (gamepad.X, board.D9),
    (gamepad.Y, board.D10),
    (gamepad.LB, board.D0),
    (gamepad.RB, board.D1),
    (gamepad.LT, board.D2),
    (gamepad.RT, board.D3),
    (gamepad.START, board.D6),
):
    switch = digitalio.DigitalInOut(pin)
    switch.switch_to_input(pull=digitalio.Pull.UP)  # pressed reads False
    buttons.append((name, switch))


def average(read, count):
    total = 0.0
    for _ in range(count):
        total += read()
    return total / count


# Through board_acceleration(), so "level" is measured the same way round as the
# loop reads tilt.
level_x = average(lambda: board_acceleration()[0], settle_samples)
level_y = average(lambda: board_acceleration()[1], settle_samples)
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
    pad.right_x = right.x
    pad.right_y = right.y

    ax, ay, az = board_acceleration()
    pad.tilt_x = tilt_amount(ax - level_x) * tilt_flip[0]
    pad.tilt_y = tilt_amount(ay - level_y) * tilt_flip[1]
    if use_tilt:
        pad.left_x = pad.tilt_x
        pad.left_y = pad.tilt_y

    for name, switch in buttons:
        pad.set_button(name, not switch.value)

    now = time.monotonic()

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
