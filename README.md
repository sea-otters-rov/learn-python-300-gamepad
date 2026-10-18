# learn-python-300-gamepad

Part 3 of Learning Python: build a USB gamepad from a Seeed XIAO RP2350, two
analog sticks and a motion sensor, then use it to fly an underwater robot in a
browser game.

The board runs CircuitPython. You edit Python on your laptop, press **Ctrl+S**,
and about a second later it is running on the board. There is no Run button:
**saving is running**.

**Play the games:** https://sea-otters-rov.github.io/learn-python-300-gamepad/

## Hardware

- Seeed XIAO RP2350, running CircuitPython **10.3.1**
- DFRobot SEN0140 10-DOF IMU (accelerometer, gyro, magnetometer, barometer)
- ADS1115 analog-to-digital converter breakout
- Two analog thumbsticks with push switches
- Four push buttons
- A breadboard and a USB **data** cable (charge-only cables are a common trap)

### Wiring

Power everything from **3V3**, never 5V -- including the thumbsticks.

| From | To |
| --- | --- |
| SEN0140 and ADS1115 SDA | XIAO D4 |
| SEN0140 and ADS1115 SCL | XIAO D5 |
| ADS1115 ADDR | GND (address 0x48) |
| Left stick X / Y | ADS1115 A0 / A1 |
| Right stick X / Y | ADS1115 A2 / A3 |
| Left stick switch | XIAO D7 |
| Right stick switch | XIAO D8 |
| Button A | XIAO D9 |
| Button B | XIAO D10 |
| Button X | XIAO D0 |
| Button Y | XIAO D1 |

Every switch and button connects its pin to **GND** when pressed. The board's
internal pull-ups do the rest, so a pressed button reads `False`.

## Setup (once per laptop)

You need VS Code (with its `code` command on PATH) and Python 3.10 or newer.

```bash
git clone https://github.com/sea-otters-rov/learn-python-300-gamepad.git
```

Open the folder in VS Code, then run the task **Board: set up this machine**
(or `& .\tools\setup.ps1` in a PowerShell terminal). It installs the VS Code
extensions and a `.venv` with autocomplete for the board. Then:

1. `Ctrl+Shift+P` -> **Python: Select Interpreter** -> `.venv`
2. Plug in the XIAO. If it is new, flash CircuitPython 10.3.1 from
   https://circuitpython.org/board/seeeduino_xiao_rp2350/
3. Run **Board: sync all files (clean)**. This makes the board match `board\`
   exactly, and **deletes anything else on it** -- copy off anything you want
   to keep first.
4. Press the board's **reset** button once. `boot.py` (which turns the board
   into a gamepad) only runs after a reset, never after a save.

## Every day

- Edit files in `board\` and press **Ctrl+S**. That is the whole workflow.
- **Serial Monitor** panel: pick the board's COM port to see `print()` output
  and errors. Only one program can use the port at a time.
- Tasks (sidebar, or `Ctrl+Shift+P` -> **Tasks: Run Task**):
  - **Board: verify** -- restart the board and show what it printed
  - **Board: serial console** -- the REPL, with Ctrl-C and Ctrl-D
  - **Board: sync all files** -- after adding files or libraries
  - **Games: play in the browser** -- serve the games locally at
    http://localhost:8765, for trying changes before they are published

If saves stop doing anything, you probably used the REPL: run **Board: verify**
once and they start again.

## The games

Open a game in Chrome, then **press any button on the board** -- browsers hide
a gamepad until it has been used. No board? Arrows, W A S D, T F G H, Space,
B, X, Y and Enter stand in for it, and **I** shows exactly what the game is
receiving.

- **Controller check** -- what every stick, tilt and button is sending
- **Marble Maze** -- roll a marble through four mazes with the left stick, or
  with tilt: set `use_tilt = True` in `board\controller.py`
- **ROV Sim** -- fly a ROV around a pool, collect five crabs with the claw,
  drop them in the basket. A closes the claw, B opens it, X switches camera,
  Y switches pitch between tilt and holding level

Changes pushed to `main` under `games\` publish themselves to GitHub Pages.
