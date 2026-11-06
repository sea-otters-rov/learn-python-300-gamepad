"""Spike: does the D0 button read, and which way round is the XIAO's user LED?

For 20 seconds the LED is given the button's raw value: pin reads True when
released (pull-up), False when pressed. Watch the small USR LED:

  lit while the button is HELD     -> the LED lights on False (active-low)
  lit while the button is RELEASED -> the LED lights on True

Every change of the button is printed with the time.
"""

import time

import board
import digitalio

SECONDS = 20

button = digitalio.DigitalInOut(board.D0)
button.switch_to_input(pull=digitalio.Pull.UP)
led = digitalio.DigitalInOut(board.LED)
led.switch_to_output()

start = time.monotonic()
last = None
changes = 0
print(f"watching D0 for {SECONDS} s -- press it a few times")
while time.monotonic() - start < SECONDS:
    value = button.value
    led.value = value
    if value != last:
        state = "released" if value else "PRESSED"
        print(f"{time.monotonic() - start:5.2f} s  D0 reads {value}  ({state})")
        last = value
        changes += 1
print(f"done: {changes - 1} changes seen")
led.deinit()
