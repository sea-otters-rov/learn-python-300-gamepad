"""Open the XIAO's serial console in the terminal: REPL, print() output, tracebacks.

An alternative to the Serial Monitor panel, for real key passthrough: Ctrl-C
breaks into the REPL, Ctrl-D reloads, Ctrl-] quits. Only one program can hold
the port, so close the Serial Monitor panel first.
"""

import sys

import repl
from serial.tools import miniterm


def main():
    console = repl.open_console()
    port = console.port
    console.close()
    print(f"[console] {port}  --  Ctrl-C = REPL, Ctrl-D = reload, Ctrl-] = quit")
    sys.argv = ["miniterm", port, "115200", "--raw"]
    miniterm.main()


if __name__ == "__main__":
    main()
