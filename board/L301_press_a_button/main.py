"""Wire a button and make the board's light answer it.

Wire one leg of a button to D7 and the other leg to GND. Save this file, press
the button, and the little yellow light marked USR, next to the USB plug, comes
on. The console shows what the pin reads.
"""

import time

import board
import digitalio

# D7 is where the A button lives for the rest of the course, so this button
# stays put.
button = digitalio.DigitalInOut(board.D7)
# Pull.UP connects the pin to 3.3 V through a resistor inside the chip, so with
# the button up the pin reads True. Pressing connects the pin straight to GND,
# which wins, and the pin reads False. Pressed is False: backwards, but it is
# how almost every button is wired.
button.switch_to_input(pull=digitalio.Pull.UP)

light = digitalio.DigitalInOut(board.LED)
light.switch_to_output()

check_every = 0.1  # seconds between looks at the button

while True:
    pin_value = button.value
    pressed = not pin_value  # not turns True into False, and False into True

    # The USR light is wired backwards too: False turns it on.
    light.value = not pressed

    print(f"pin {pin_value}  pressed {pressed}")
    time.sleep(check_every)


# Try these:
#   - Hold the button down and watch the console. Why is pressed always the
#     opposite of what the pin reads?
#   - light.value = pin_value would light up the same way. Why? Which line would
#     make more sense to you if you came back to this in a month?
#   - Change Pull.UP to Pull.DOWN. Does pressing still do anything? Why not?
#   - Change check_every to 2. Can you press and let go so quickly that the
#     console never sees it?
#   - Change board.D7 to board.D20. Read the error carefully: what is it saying?
