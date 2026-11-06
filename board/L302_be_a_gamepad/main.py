"""Make your button press A on the Controller check page.

Your board is now a USB gamepad, like a game controller. Open the Controller
check page, press your button once so the page notices the board, and watch
"0 A" light up every time you press.
"""

import time

import board
import digitalio

import gamepad

# The same button as lesson 301, on D7.
button = digitalio.DigitalInOut(board.D7)
button.switch_to_input(pull=digitalio.Pull.UP)  # pressed reads False

light = digitalio.DigitalInOut(board.LED)
light.switch_to_output()

# The computer sees your board as a gamepad. Everything you put in pad is sent
# to it when you call pad.send().
pad = gamepad.Gamepad()

check_every = 0.05  # seconds between looks at the button

while True:
    pin_value = button.value
    pressed = not pin_value

    light.value = not pressed  # the USR light is wired backwards: False is on

    # gamepad.A is the A button's number, 0. The Controller check page and every
    # game number their buttons the same way, so it shows up there as "0 A".
    pad.set_button(gamepad.A, pressed)
    pad.send()

    print(f"pressed {pressed}  buttons {pad.buttons:016b}")
    time.sleep(check_every)


# Try these:
#   - Change gamepad.A to gamepad.B. Which button lights on the page now, and
#     what number is next to it? Which digit changes in the console's buttons?
#   - Put a # in front of pad.send(). What does the page show when you press?
#   - Set check_every to 0.5 and tap the button as quickly as you can. Does the
#     page catch every tap?
#   - Change gamepad.A to gamepad.a. Read the error: what is it looking for?
