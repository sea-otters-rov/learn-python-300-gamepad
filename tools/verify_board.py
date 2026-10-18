"""Restart code.py on the XIAO and report what it printed.

    .\\.venv\\Scripts\\python.exe .\\tools\\verify_board.py

Ctrl-C then Ctrl-D: break into the REPL, then leave it, which reloads code.py
-- and re-enables auto-reload, so this is also the fix for "my saves stopped
working" after someone used the REPL. Only output after the LAST "code.py
output:" counts; the KeyboardInterrupt the Ctrl-C causes is expected.

Exit codes are in tools/repl.py: 0 running, 1 traceback, 2 port busy, 3 no board.
"""

import sys

import repl

MARKER = "code.py output:"
LISTEN = 5.0  # seconds after code.py starts; controller.py reports every 2 s


def main():
    with repl.open_console() as console:
        repl.break_in(console)
        console.write(repl.CTRL_D)
        text = repl.read(console, 10.0, stop=lambda t: MARKER in t)
        if MARKER not in text:
            print("\n[verify] code.py never started.")
            return repl.TRACEBACK
        text += repl.read(console, LISTEN)
    run = text.rsplit(MARKER, 1)[1]
    if "Traceback" in run:
        print("\n[verify] code.py raised a traceback.")
        return repl.TRACEBACK
    print("\n[verify] code.py is running.")
    return repl.OK


if __name__ == "__main__":
    sys.exit(main())
