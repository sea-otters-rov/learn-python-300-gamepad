"""Talk to the XIAO's serial console: shared by verify_board.py and run_on_board.py.

Exit codes, the same in every tool that uses this:
    0  ran, no traceback
    1  the board raised a traceback (printed)
    2  serial port busy -- close the Serial Monitor (or whatever holds it), retry
    3  no XIAO found

The serial port is exclusive: only one program can hold it. The VS Code Serial
Monitor panel is the usual culprit, and exit 2 says so rather than leaving a
bare Windows "Access is denied".
"""

import re
import sys
import time

import find_board

try:
    import serial
except ImportError:
    sys.exit("pyserial is missing. Run .\\tools\\setup.ps1 first.")

OK, TRACEBACK, BUSY, NO_BOARD = 0, 1, 2, 3
CTRL_C, CTRL_D = b"\x03", b"\x04"

# Terminal title and cursor codes CircuitPython prints around its status line.
ANSI = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b\[[0-9;?]*[A-Za-z]")


def open_console():
    """An open serial.Serial on the XIAO's console, or exit with a clear code."""
    ours, others = find_board.boards()
    if others:
        print(f"[board] leaving alone: {find_board.describe(others)}")
    if not ours:
        print("[board] No XIAO RP2350 found. Is it plugged in with a data cable?")
        sys.exit(NO_BOARD)
    if len(ours) > 1:
        print(f"[board] {len(ours)} XIAOs attached; using {ours[0][0]}.")
    root, _, uid = ours[0]
    port = find_board.serial_port(uid)
    if not port:
        print(f"[board] Found the drive {root} but no serial port for UID {uid}.")
        sys.exit(NO_BOARD)
    try:
        return serial.Serial(port, 115200, timeout=0.1)
    except serial.SerialException as exc:
        if "denied" in str(exc).lower() or "busy" in str(exc).lower():
            print(f"[board] {port} is busy. Close the Serial Monitor, then retry.")
            sys.exit(BUSY)
        raise


def break_in(console):
    """Stop whatever is running and get to a quiet >>> prompt.

    Entering the REPL also turns auto-reload off until the next Ctrl-D, so a
    file copied to the board now will not restart code.py underneath us.
    """
    console.write(CTRL_C + CTRL_C)
    time.sleep(0.5)
    console.reset_input_buffer()
    console.write(b"\r\n")
    time.sleep(0.2)
    console.reset_input_buffer()


def read(console, seconds, stop=None):
    """Echo and collect output for up to `seconds`, ending early when stop(text)."""
    text = ""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        chunk = console.read(512)
        if not chunk:
            continue
        piece = ANSI.sub("", chunk.decode(errors="replace"))
        text += piece
        sys.stdout.write(piece)
        sys.stdout.flush()
        if stop and stop(text):
            break
    return text
