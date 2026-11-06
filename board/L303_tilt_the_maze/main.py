"""Wire the tilt sensor and roll the marble through the maze.

The SEN0140 is a sensor board that feels gravity. Wire it with four wires --
3V3, GND, SDA to D4, SCL to D5 -- lay your board flat, save, and open the
Marble Maze. Tip the board and the marble rolls. Keep the board still on the
desk for the first second: that is when it learns what "level" is.
"""

import time

import board
import digitalio

import gamepad
import imu

button = digitalio.DigitalInOut(board.D7)
button.switch_to_input(pull=digitalio.Pull.UP)  # pressed reads False

pad = gamepad.Gamepad()

# I2C is two wires, SDA (data) and SCL (clock), that many chips can share. Each
# chip answers to its own address, so one pair of wires reaches all of them.
i2c = board.I2C()
sensors = imu.IMU(i2c)

# How hard to tip the board for a stick pushed all the way. Tipping moves part
# of gravity (9.8 m/s^2) sideways: 5 is about 30 degrees of tip.
full_tilt = 5.0  # m/s^2
level_readings = 40

# No desk is perfectly level, and no sensor reads exactly 0 lying flat. So add
# up some readings while the board sits still, and take the average as "level".
total_x = 0.0
total_y = 0.0
for reading in range(level_readings):
    sensor_x, sensor_y, sensor_z = sensors.acceleration
    # The sensor sits turned on the breadboard: its y runs left to right across
    # the breadboard, and its x runs near to far.
    total_x += sensor_y
    total_y += sensor_x
level_x = total_x / level_readings
level_y = total_y / level_readings
print(f"level x {level_x:.2f}  y {level_y:.2f} m/s^2")

check_every = 0.02  # seconds

while True:
    pin_value = button.value
    pad.set_button(gamepad.A, not pin_value)

    sensor_x, sensor_y, sensor_z = sensors.acceleration
    board_x = sensor_y  # turned, as above
    board_y = sensor_x

    # How far from level, in m/s^2: right edge down is +, far edge down is -.
    tip_x = board_x - level_x
    tip_y = board_y - level_y

    # A stick runs -1.0 to 1.0. Anything past full_tilt gets sent as 1.0.
    pad.tilt_x = tip_x / full_tilt
    pad.tilt_y = tip_y / full_tilt

    # The maze steers with the left stick, so tilt drives the left stick too.
    pad.left_x = pad.tilt_x
    pad.left_y = pad.tilt_y
    pad.send()

    print(f"tip {tip_x:+.2f} {tip_y:+.2f}  stick {pad.left_x:+.2f} {pad.left_y:+.2f}")
    time.sleep(check_every)


# Try these:
#   - Change tip_x = board_x - level_x to tip_x = board_x, and the same for y.
#     Lay the board flat on the desk. What does the marble do now, and why?
#   - Make full_tilt 2. What changes in the maze? What about 20?
#   - Change board_x = sensor_y to board_x = sensor_x. Tip the right edge down.
#     Which way does the marble go?
#   - Hold the board as still as you can. Do the tip numbers sit still? What
#     could you do so tiny wobbles send exactly 0?
#   - Set full_tilt = 0. Read the error: which line is it pointing at, and why?
