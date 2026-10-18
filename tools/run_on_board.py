"""Run a spike (or one line of Python) on the XIAO and show its output.

    .\\.venv\\Scripts\\python.exe .\\tools\\run_on_board.py spikes\\adc_speed.py
    .\\.venv\\Scripts\\python.exe .\\tools\\run_on_board.py "help('modules')"

A spike file is copied to the board's root and imported, then deleted again, so
it never becomes part of the board image. code.py is restarted at the end.

The order matters. The REPL is entered BEFORE the file is copied, because
entering the REPL turns auto-reload off -- copy first and the board restarts
code.py, and a code.py that reads the keyboard eats the typed import as input.

Finished means the >>> prompt came back. Exit codes are in tools/repl.py.
"""

import os
import sys

import repl

TIMEOUT = 120.0  # seconds; the slowest spike here takes about 20


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    what = sys.argv[1]
    spike = what if what.endswith(".py") and os.path.isfile(what) else None

    with repl.open_console() as console:
        repl.break_in(console)
        copied = None
        if spike:
            ours, _ = repl.find_board.boards()
            name = os.path.basename(spike)
            copied = os.path.join(ours[0][0], name)
            with open(spike, "rb") as src, open(copied, "wb") as dst:
                dst.write(src.read())
            statement = f"import {name[:-3]}"
        else:
            statement = what
        try:
            console.write(statement.encode() + b"\r\n")
            text = repl.read(console, TIMEOUT, stop=lambda t: t.endswith(">>> "))
        finally:
            if copied:
                os.remove(copied)
            console.write(repl.CTRL_D)  # back to code.py
    print()
    if not text.endswith(">>> "):
        print(f"[run] still running after {TIMEOUT:.0f} s; stopped listening.")
        return repl.TRACEBACK
    return repl.TRACEBACK if "Traceback" in text else repl.OK


if __name__ == "__main__":
    sys.exit(main())
