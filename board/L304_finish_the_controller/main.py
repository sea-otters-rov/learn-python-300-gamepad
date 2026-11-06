"""Add both thumbsticks and the rest of the buttons.

The thumbsticks go through the ADS1115, a second chip on the same two I2C wires
as the tilt sensor. Wire the buttons by the pin picture, save, and check every
stick and button on the Controller check page. This is your controller for the
rest of the course -- the ROV sim lessons are flown with it.

Keep the sticks and the board still for the first second: that is when the
sticks' centers and "level" are measured.
"""

import time

import board
import busio
import digitalio

import gamepad
import imu
import sticks

pad = gamepad.Gamepad()

# One I2C bus, two chips: the tilt sensor and the ADS1115. 400_000 runs the bus
# four times faster than board.I2C() does -- reading four stick channels takes
# about 9 ms even so, the slowest part of the loop.
i2c = busio.I2C(board.SCL, board.SDA, frequency=400_000)
sensors = imu.IMU(i2c)

# ---- How this breadboard is built ---------------------------------------------
# Check each on the Controller check page: push a stick up, its dot must go up;
# push it right, it goes right.
#
# connect() measures where each stick rests, then hands back the stick wired to
# A0/A1 first. On this breadboard that one is on the RIGHT. Wired the other way
# round, swap the two names: left, right = sticks.connect(i2c)
right, left = sticks.connect(i2c)
# The left stick is mounted turned 180 degrees from the right one, so both of its
# axes read backwards. Mounted facing the same way, delete these two lines. One
# axis wrong on its own? Flip only that one.
left.flip_x = -1
left.flip_y = -1
# -------------------------------------------------------------------------------

# Every button: which gamepad button it is, and which pin it is wired to.
# These are the pins in the pin picture, the same on every board.
buttons = (
    (gamepad.A, board.D7),
    (gamepad.B, board.D8),
    (gamepad.X, board.D9),
    (gamepad.Y, board.D10),
    (gamepad.LB, board.D0),
    (gamepad.RB, board.D1),
    (gamepad.LT, board.D2),
    (gamepad.RT, board.D3),
    (gamepad.START, board.D6),
)
switches = []
for button_name, pin in buttons:
    switch = digitalio.DigitalInOut(pin)
    switch.switch_to_input(pull=digitalio.Pull.UP)  # pressed reads False
    switches.append((button_name, switch))

# Tilt, the same as lesson 303.
full_tilt = 5.0  # m/s^2 for a full stick: about 30 degrees of tip
level_readings = 40
total_x = 0.0
total_y = 0.0
for reading in range(level_readings):
    sensor_x, sensor_y, sensor_z = sensors.acceleration
    total_x += sensor_y  # the sensor sits turned on the breadboard
    total_y += sensor_x
level_x = total_x / level_readings
level_y = total_y / level_readings

# True: tilt steers the left stick, for the marble maze. False: the left stick does.
use_tilt = False

while True:
    # Each .x or .y asks the ADS1115 for a fresh reading, about 2 ms each, so
    # read each one once and keep it.
    left_x = left.x
    left_y = left.y
    right_x = right.x
    right_y = right.y

    sensor_x, sensor_y, sensor_z = sensors.acceleration
    board_x = sensor_y  # turned, as above
    board_y = sensor_x
    tip_x = board_x - level_x
    tip_y = board_y - level_y
    pad.tilt_x = tip_x / full_tilt
    pad.tilt_y = tip_y / full_tilt

    pad.right_x = right_x
    pad.right_y = right_y
    if use_tilt:
        pad.left_x = pad.tilt_x
        pad.left_y = pad.tilt_y
    else:
        pad.left_x = left_x
        pad.left_y = left_y

    for button_name, switch in switches:
        pad.set_button(button_name, not switch.value)

    pad.send()

    print(
        f"left {pad.left_x:+.2f} {pad.left_y:+.2f}"
        f"  right {right_x:+.2f} {right_y:+.2f}"
        f"  tilt {pad.tilt_x:+.2f} {pad.tilt_y:+.2f}"
        f"  buttons {pad.buttons:016b}"
    )


# Try these:
#   - Let go of a stick and watch the console. Does it come back to exactly 0?
#     Now add left.dead_zone = 0 under the flip lines. What changed, and why
#     would that matter to an ROV that is meant to sit still?
#   - Set use_tilt = True and play the maze with tilt, then with the stick.
#     Which is easier? Why might a pilot want both?
#   - Swap the names to left, right = sticks.connect(i2c). Which dot moves now
#     when you push your left stick?
#   - Change gamepad.START to gamepad.BACK in the buttons. Which button lights
#     on the page now?
#   - Change frequency=400_000 to frequency=100_000. Count how many lines the
#     console prints in a few seconds before and after. Why did it change?
#   - Give two buttons the same pin: change board.D10 to board.D7. The error
#     says RX, a name you never typed -- D7's other name is RX, used when the
#     pin talks to another chip. Which line of yours does it point at?
