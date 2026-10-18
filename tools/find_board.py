"""Find the attached Part 3 board: its CIRCUITPY drive, and its serial port.

A board is recognised by the boot_out.txt CircuitPython writes to its own drive,
and ONLY if that file names a board in SUPPORTED. Any other CircuitPython board
is ignored on purpose. A MatrixPortal from Parts 1-2 can be plugged into the
same laptop, and a save or a clean sync landing on it would wipe its lessons --
the drive letter says nothing about which board is which.

Keep imports to os and sys at the top. tools/sync.py imports this on every
Ctrl+S, and every module imported is paid for on every save. pyserial is only
imported inside serial_port(), which the save path never calls.
"""

import os

# circuitpython.org board ids, as boot_out.txt prints them after "Board ID:".
SUPPORTED = ("seeeduino_xiao_rp2350",)


def candidate_roots():
    """Places a mounted CIRCUITPY could be.

    Windows hands out drive letters. Elsewhere the desktop auto-mounter puts
    removable media under a per-user directory: /media/$USER (GNOME), or
    /run/media/$USER, or /Volumes on macOS.
    """
    if os.name == "nt":
        return [c + ":\\" for c in "DEFGHIJKLMNOPQRSTUVWXYZ"]
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    roots = []
    for parent in ("/media/" + user, "/run/media/" + user, "/media", "/Volumes"):
        try:
            names = sorted(os.listdir(parent))
        except OSError:
            continue
        roots += [os.path.join(parent, n) for n in names]
    return roots


def read_boot_out(root):
    """(board id, uid) for a CircuitPython drive, or None for anything else."""
    try:
        with open(os.path.join(root, "boot_out.txt")) as fh:
            text = fh.read()
    except OSError:
        return None
    if not text.startswith("Adafruit CircuitPython"):
        return None
    board_id = uid = ""
    for line in text.splitlines():
        if line.startswith("Board ID:"):
            board_id = line[9:].strip()
        elif line.startswith("UID:"):
            uid = line[4:].strip().upper()
    return board_id, uid


def scan(roots=None):
    """Every CircuitPython drive attached: [(root, board id, uid)].

    `roots` overrides where to look, which is how this gets tested without a
    real board.
    """
    found = []
    for root in candidate_roots() if roots is None else roots:
        info = read_boot_out(root)
        if info:
            found.append((root, info[0], info[1]))
    return found


def boards(roots=None):
    """(ours, others): Part 3 boards, and CircuitPython boards to leave alone."""
    ours, others = [], []
    for root, board_id, uid in scan(roots):
        (ours if board_id in SUPPORTED else others).append((root, board_id, uid))
    return ours, others


def serial_port(uid):
    """The console COM port of the board with this UID, or None.

    CircuitPython uses the CPU UID as the USB serial number, so this matches
    the right board however many are plugged in. MI_00 is the console when a
    board also exposes a second, data-only serial port.
    """
    import serial.tools.list_ports

    ports = [
        p
        for p in serial.tools.list_ports.comports()
        if uid and uid in (p.hwid or "").upper()
    ]
    consoles = [p for p in ports if "MI_00" in (p.hwid or "").upper()] or ports
    return consoles[0].device if consoles else None


def describe(others):
    """One line about boards that were found and deliberately not touched."""
    names = [f"{root} ({board_id or 'unknown board'})" for root, board_id, _ in others]
    return ", ".join(names)
