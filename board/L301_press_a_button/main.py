"""Wire a button and make the board's light respond.

Wire one leg of a button to D7 and the other leg to GND. Save this file, press
the button, and the little yellow light marked USR, next to the USB plug, comes
on. The console shows what the pin reads.
"""

import time

import board
import digitalio

# D7 is where the A button lives.
button = digitalio.DigitalInOut(board.D7)
# Pull.UP connects the pin to 3.3 V through a resistor inside the chip, so with
# the button unpressed the pin reads True. Pressing connects the pin straight to GND,
# forcing the pin to False. Pressed is False: backwards, but it is
# how almost every button is wired.
button.switch_to_input(pull=digitalio.Pull.UP)

light = digitalio.DigitalInOut(board.LED)
light.switch_to_output()

while True:
    unpressed = button.value
    pressed = not unpressed  # not turns True into False, and False into True

    # The USR light is wired backwards too: False turns it on.
    light.value = not pressed

    print(f"pin {unpressed}  pressed {pressed}")
    time.sleep(0.1)


# Try these:
#   - light.value = unpressed would light up the same way, but which line would
#     make more sense to you if you came back to this in a month?
#   - Change Pull.UP to Pull.DOWN. Does pressing still do anything? Why not?
#   - Change board.D7 to board.D20. Read the error carefully: what is it saying?
