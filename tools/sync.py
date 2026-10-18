"""Copy one saved file from board/ onto the attached XIAO. Run by VS Code on Ctrl+S.

Writing to the CIRCUITPY drive is what makes CircuitPython reload, so this copy
IS "run my code". Full-tree and clean syncs live in sync.ps1, off the hot path.

Inherited from the LED-panel course (led-panel-learn-python, tools/sync.py),
where each of these cost real debugging time. Measured on Windows only:

1. A plain Python read/write, not robocopy. robocopy skips a file whose size and
   timestamp look unchanged, and FAT timestamps are only good to 2 seconds, so a
   one-character edit saved quickly is silently not copied. Forcing it makes it
   the slowest option. Python is ~110 ms to start; PowerShell is ~500 ms.
2. No os.fsync. Windows disables write caching on removable drives, so fsync
   bought nothing there. Linux page-caches FAT writes, so a Linux port will
   probably need it back -- re-measure rather than inherit this.
3. A UTF-8 BOM is stripped from .py files on the way. CircuitPython does not
   skip one: it reports a SyntaxError on line 1 pointing at a valid line.
   PowerShell's Set-Content -Encoding utf8 writes one by default.

No drive letter is cached. Finding the board is one small file read per drive
letter, a few milliseconds against a save that is mostly the flash waiting, and
a cache would need the stale-letter handling the old course carries.

Only boards named in find_board.SUPPORTED are written to. A MatrixPortal from
Parts 1-2 plugged in beside the XIAO is left strictly alone.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import find_board  # noqa: E402

BOARD = os.path.normcase(os.path.join(os.path.dirname(HERE), "board"))
BOM = b"\xef\xbb\xbf"


def copy(src, dst):
    folder = os.path.dirname(dst)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(src, "rb") as fh:
        data = fh.read()
    if src.endswith(".py") and data.startswith(BOM):
        data = data[len(BOM) :]
        print(
            f"[sync] stripped a UTF-8 BOM from {os.path.basename(src)} -- "
            "the board cannot parse one. Save it as UTF-8 without BOM."
        )
    with open(dst, "wb") as fh:
        fh.write(data)


def main():
    if len(sys.argv) < 2:
        print("[sync] usage: sync.py <file>")
        return 2
    src = os.path.abspath(sys.argv[1])
    if not os.path.isfile(src):
        return 0
    # Saves outside board/ (tools, games, README) are not board content.
    if not os.path.normcase(src).startswith(BOARD + os.sep):
        return 0
    rel = src[len(BOARD) + 1 :]

    ours, others = find_board.boards()
    if others:
        print(f"[sync] leaving alone: {find_board.describe(others)}")
    if not ours:
        print("[sync] No XIAO RP2350 found.")
        print("       Check the USB cable is a DATA cable, not charge-only.")
        print("       If the board is in the bootloader, press reset once.")
        return 1

    failed = []
    for root, _, _ in ours:
        try:
            copy(src, os.path.join(root, rel))
        except OSError as exc:
            failed.append(f"{root} ({exc})")
    if failed:
        print(f"[sync] FAILED: {', '.join(failed)}")
        return 1
    print(f"[sync] {rel} -> {', '.join(root for root, _, _ in ours)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
