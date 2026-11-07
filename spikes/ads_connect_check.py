"""Exercise sticks.connect(): the bus scan, a normal connect, and the give-up path.

    .\\.venv\\Scripts\\python.exe .\\tools\\run_on_board.py spikes\\ads_connect_check.py

The give-up path is forced by pointing sticks.ADDRESS at 0x49, where nothing
answers on this board, so the error message _explain() builds can be read
without pulling a wire.
"""

import time

import board
import busio

import sticks

i2c = busio.I2C(board.SCL, board.SDA, frequency=400_000)
print("on the bus:", " ".join(f"0x{a:02X}" for a in sticks._scan(i2c)))

start = time.monotonic()
left, right = sticks.connect(i2c)
print(f"connect ok in {time.monotonic() - start:.2f} s")

sticks.ADDRESS = 0x49
start = time.monotonic()
try:
    sticks.connect(i2c)
    print("connect at 0x49 unexpectedly worked")
except RuntimeError as exc:
    print(f"gave up after {time.monotonic() - start:.2f} s: {exc}")
