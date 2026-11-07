r"""List the lessons and switch which one runs -- on the board, or in the ROV sim.

    .\.venv\Scripts\python.exe .\tools\lesson.py            pick from a list
    .\.venv\Scripts\python.exe .\tools\lesson.py list       just show them
    .\.venv\Scripts\python.exe .\tools\lesson.py 305        switch directly
    .\.venv\Scripts\python.exe .\tools\lesson.py L305_tank_drive

The same pattern as Parts 1-2 (led-panel-learn-python, tools/lesson.py), for
two kinds of lesson:

- board\L3xx_*\main.py runs on the XIAO. Switching rewrites board\code.py to
  the one line `from L301_press_a_button import main` and copies it onto the
  board, which restarts into it -- the same as a save.
- sim\L3xx_*\main.py runs inside the ROV sim. Switching rewrites sim\pilot.py
  the same way, and a sim open from tools\serve.py reloads into it.

Switching to a sim lesson leaves the board alone: it keeps running the last
board lesson, which is the controller the sim is flown with.

The list is built by scanning both folders for lesson folders holding a
main.py, and the synopsis is the first line of that file's docstring. There is
no catalog file to keep in step -- add a lesson folder and it appears here.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import find_board  # noqa: E402
from sync import copy  # noqa: E402

ROOT = os.path.dirname(HERE)
FOLDERS = {
    "board": os.path.join(ROOT, "board"),
    "sim": os.path.join(ROOT, "sim"),
}
LAUNCHERS = {
    "board": os.path.join(FOLDERS["board"], "code.py"),
    "sim": os.path.join(FOLDERS["sim"], "pilot.py"),
}
LESSON_RE = re.compile(r"^L(\d+)_\w+$")
# [ \t]* rather than \s*: \s is greedy across newlines, so it ate the file's
# trailing newline and every switch left the launcher without one (Parts 1-2).
IMPORT_RE = re.compile(r"^from\s+(\w+)\s+import\s+main[ \t]*$", re.MULTILINE)


def synopsis(kind, folder):
    """First line of main.py's docstring, or a placeholder."""
    path = os.path.join(FOLDERS[kind], folder, "main.py")
    try:
        # utf-8-sig, not utf-8: a stray BOM is not whitespace, so it would stop
        # the docstring regex matching and the lesson would look undescribed.
        with open(path, encoding="utf-8-sig") as fh:
            src = fh.read()
    except OSError:
        return "(unreadable)"
    m = re.search(r'^\s*(?:r|u|b)?("""|\'\'\')(.*?)\1', src, re.DOTALL)
    if m:
        for line in m.group(2).splitlines():
            if line.strip():
                return line.strip()
    return "(no description -- add a docstring to main.py)"


def lessons():
    """{lesson number: (kind, folder)} for every lesson folder with a main.py."""
    found = {}
    for kind, folder in FOLDERS.items():
        try:
            names = os.listdir(folder)
        except OSError:
            continue
        for name in names:
            m = LESSON_RE.match(name)
            if m and os.path.isfile(os.path.join(folder, name, "main.py")):
                found[int(m.group(1))] = (kind, name)
    return dict(sorted(found.items()))


def current(kind):
    """The lesson a launcher runs now, or None."""
    try:
        with open(LAUNCHERS[kind], encoding="utf-8-sig") as fh:
            m = IMPORT_RE.search(fh.read())
    except OSError:
        return None
    return m.group(1) if m else None


def show(found):
    running = {current(kind) for kind in FOLDERS}
    width = max(len(name) for _, name in found.values())
    for number, (kind, name) in found.items():
        mark = "*" if name in running else " "
        print(f" {mark} {number:>4}. {kind:<5} {name.ljust(width)}  {synopsis(kind, name)}")
    print("\n   * = running now (one on the board, one in the sim)")


def write_launcher(kind, name):
    path = LAUNCHERS[kind]
    line = f"from {name} import main"
    try:
        with open(path, encoding="utf-8-sig") as fh:
            src = fh.read()
    except OSError:
        src = ""
    if IMPORT_RE.search(src):
        src = IMPORT_RE.sub(line, src)
    else:
        # board\code.py starts as `import controller` (the spike), with no
        # lesson line to rewrite -- the launcher becomes just the lesson line.
        src = line + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)


def switch(kind, name):
    write_launcher(kind, name)
    if kind == "sim":
        print(f"[lesson] the sim now runs {name} -- an open sim reloads into it.")
        return 0
    print(f"[lesson] the board now runs {name}")
    ours, others = find_board.boards()
    if others:
        print(f"[lesson] leaving alone: {find_board.describe(others)}")
    if not ours:
        print("[lesson] No XIAO RP2350 found -- saved; sync when it is plugged in.")
        return 0
    failed = []
    for root, _, _ in ours:
        try:
            copy(LAUNCHERS["board"], os.path.join(root, "code.py"))
        except OSError as exc:
            failed.append(f"{root} ({exc})")
    if failed:
        print(f"[lesson] could not push to {', '.join(failed)}")
        return 1
    print(f"[lesson] pushed to {', '.join(r for r, _, _ in ours)} -- restarting into it.")
    return 0


def pick(found, choice):
    """A lesson number or folder name -> (kind, folder), or None."""
    if choice.isdigit() and int(choice) in found:
        return found[int(choice)]
    for kind, name in found.values():
        if name == choice:
            return kind, name
    return None


def main():
    found = lessons()
    if not found:
        print(r"[lesson] No lessons found: a lesson is board\L3xx_*\ or sim\L3xx_*\ ")
        print("         holding a main.py.")
        return 1

    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg == "list":
        show(found)
        return 0
    if arg:
        chosen = pick(found, arg)
        if chosen is None:
            print(f"[lesson] No lesson called {arg!r}. Available:")
            show(found)
            return 1
        return switch(*chosen)

    print("Lessons:\n")
    show(found)
    try:
        choice = input("\nNumber to switch to (Enter to cancel): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n[lesson] canceled")
        return 0
    if not choice:
        print("[lesson] canceled")
        return 0
    chosen = pick(found, choice)
    if chosen is None:
        print(f"[lesson] {choice!r} is not one of the numbers above.")
        return 1
    return switch(*chosen)


if __name__ == "__main__":
    sys.exit(main())
