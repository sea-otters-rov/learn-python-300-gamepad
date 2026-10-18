"""Spike: sweep the left stick and blink A, so a browser can see the gamepad."""

import math
import time

import gamepad

SECONDS = 25

pad = gamepad.Gamepad()
print("gamepad found, sweeping")
start = time.monotonic()
sent = 0
while time.monotonic() - start < SECONDS:
    t = time.monotonic() - start
    wave = math.sin(t * 2)
    pad.left_x = wave
    pad.left_y = -wave
    pad.right_x = 0.5
    pad.right_y = -0.5
    pad.set_button(gamepad.A, int(t) % 2 == 0)
    pad.send()
    sent += 1
    time.sleep(0.01)
pad.left_x = pad.left_y = pad.right_x = pad.right_y = 0.0
pad.release(gamepad.A)
pad.send()
print(f"sent {sent} loops in {SECONDS} s")
