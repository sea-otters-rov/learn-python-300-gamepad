// rov_pilot.js -- the student's Python, flying the ROV.
//
// In pilot mode the sim does not mix thrusters itself (PilotAssist). It calls
// the student's pilot(pad, rov) instead, from sim/<lesson>/main.py, and the
// commands that comes back go straight to the thrusters.
//
// The Python runs in MicroPython compiled to WebAssembly -- the same dialect
// CircuitPython is built on -- loaded once from jsDelivr, pinned like three.js.
// Students edit in VS Code; tools/serve.py tells this page when a file under
// sim/ is saved, and the new code is running ~15 ms later without a reload.
//
// Which lesson runs is sim/pilot.py's one line, `from L305_tank_drive import
// main` -- the same launcher pattern as the board's code.py, rewritten by the
// lesson picker. Without sim/ (GitHub Pages, or no server) there is no pilot
// mode and the sim flies on its own pilot assist as before.
//
// Measured on the dev machine (spikes/browser_python): start-up 16-27 ms, one
// call with the commands handed back ~26 us. The call runs on the page's own
// thread, so a pilot() that never returns would freeze the page -- which is why
// a `while True` in a lesson is refused before it runs.

const MICROPYTHON =
  "https://cdn.jsdelivr.net/npm/@micropython/micropython-webassembly-pyscript@1.27.0/micropython.mjs";
const SIM = "../sim/"; // from games/
const LAUNCHER = "pilot.py";
const SHARED = ["sim.py", "cube.py", "triangle.py"];
const LAUNCH_LINE = /^from\s+(\w+)\s+import\s+main[ \t]*$/m;
const WHILE_TRUE = /^[ \t]*while\s+(True|1)\s*:/m;
const PRINT_LINES = 6; // how much print() output the panel keeps
const SLOW_CALL_MS = 20; // a pilot() slower than this gets a warning

// Python the student never sees. Its own objects live on the Python side, so a
// student's `pad.left_y` or `rov.thrust()` never crosses into JS; JS crosses
// once per call, and the commands come back written into a typed array.
const HARNESS = `
import sys

_pad = None
_rov = None
_pilot = None
_uses = ()  # which of cube / triangle the lesson itself imported


def load(launcher, thrusters):
    global _pad, _rov, _pilot, _uses
    for name in list(sys.modules):
        if name not in ("sys", "_harness"):
            del sys.modules[name]
    import sim

    _pad = sim.Pad()
    _rov = sim.Rov(thrusters)
    found = {}
    exec(launcher, found)
    # before check() imports both files itself
    _uses = tuple(name for name in ("cube", "triangle") if name in sys.modules)
    main = found["main"]
    if not hasattr(main, "pilot"):
        raise AttributeError(
            "there is no pilot() in this lesson's main.py -- the sim calls pilot(pad, rov)"
        )
    _pilot = main.pilot


def new_rov(thrusters):
    global _rov
    import sim

    _rov = sim.Rov(thrusters)


def check(module_name, ids):
    module = __import__(module_name)
    names = ids.split(",")
    problems = []
    for number, name in enumerate(names):
        value = getattr(module, name, None)
        if value is None:
            problems.append(f"{module_name}.py has no {name} -- it should be {number}")
        elif value != number:
            problems.append(f"{module_name}.{name} is {value}, but that thruster is number {number}")
    for name in dir(module):
        if name.isupper() and name not in names:
            problems.append(f"{module_name}.py has {name}, which is not a thruster")
    return "\\n".join(problems)


def uses(module_name):
    return 1 if module_name in _uses else 0


def step(out, lx, ly, rx, ry, tx, ty, buttons, ax, ay, az, depth, heading, amps, claw, camera):
    pad = _pad
    pad.left_x = lx
    pad.left_y = ly
    pad.right_x = rx
    pad.right_y = ry
    pad.tilt_x = tx
    pad.tilt_y = ty
    # the browser's button numbers, as in gamepad.py
    pad.a = bool(buttons & 1)
    pad.b = bool(buttons & 2)
    pad.x = bool(buttons & 4)
    pad.y = bool(buttons & 8)
    pad.left_bumper = bool(buttons & 16)
    pad.right_bumper = bool(buttons & 32)
    pad.left_trigger = bool(buttons & 64)
    pad.right_trigger = bool(buttons & 128)
    pad.start = bool(buttons & 512)
    rov = _rov
    commands = rov._commands
    for i in range(len(commands)):
        commands[i] = 0.0
    rov.claw_closed = bool(claw)
    rov.camera_onboard = bool(camera)
    rov.acceleration = (ax, ay, az)
    rov.depth = depth
    rov.heading = heading
    rov.amps = amps
    _pilot(pad, rov)
    for i in range(len(commands)):
        out[i] = commands[i]
    return (1 if rov.claw_closed else 0) | (2 if rov.camera_onboard else 0)
`;

// Python's traceback, minus the harness's own lines: a student should see
// their file and line, not ours.
function tidy(error) {
  return String(error.message || error)
    .split("\n")
    .filter((line) => !line.includes("_harness.py") && !line.includes("<stdin>"))
    .join("\n")
    .trim();
}

async function text(path) {
  const response = await fetch(SIM + path, { cache: "no-store" });
  if (!response.ok) throw new Error(`could not read sim/${path} (${response.status})`);
  return response.text();
}

export class Pilot {
  // Resolves to a Pilot, or null when there is no sim/pilot.py to fly.
  // `ids` is { cube: [...], triangle: [...] }: the thruster names each Python
  // file must hold, in profile order -- taken from rov_profiles.js, so the
  // profile stays the one source.
  static async start(profile, ids) {
    try {
      await text(LAUNCHER);
    } catch {
      return null;
    }
    const pilot = new Pilot(ids);
    const { loadMicroPython } = await import(MICROPYTHON);
    pilot.mp = await loadMicroPython({ stdout: (line) => pilot.print(line), stderr: (line) => pilot.print(line) });
    pilot.mp.FS.writeFile("/_harness.py", HARNESS);
    pilot.mp.runPython("import _harness");
    pilot.harness = pilot.mp.pyimport("_harness");
    await pilot.load(profile);
    new EventSource("/changes").onmessage = (event) => {
      if (event.data.startsWith("sim/")) pilot.load(pilot.profile);
    };
    return pilot;
  }

  constructor(ids) {
    this.ids = ids;
    this.lesson = null; // e.g. "L305_tank_drive"
    this.error = null; // a Python error the student must fix; pilot() is not called
    this.warning = null; // worth saying, but pilot() still runs
    this.output = []; // the last few lines of print()
    this.loads = 0;
    this.callMs = 0;
    this.profile = null;
    this.loading = null;
  }

  print(line) {
    this.output.push(line);
    if (this.output.length > PRINT_LINES) this.output.shift();
  }

  // Read the launcher and every file it needs, and import them fresh. Saving
  // two files at once asks twice; the second waits for the first.
  async load(profile) {
    this.profile = profile;
    while (this.loading) await this.loading;
    this.loading = this._load(profile);
    await this.loading;
    this.loading = null;
  }

  async _load(profile) {
    this.error = null;
    this.warning = null;
    this.output = [];
    try {
      const launcher = await text(LAUNCHER);
      const found = launcher.match(LAUNCH_LINE);
      if (!found) {
        throw new Error("sim/pilot.py should be one line, like: from L305_tank_drive import main");
      }
      this.lesson = found[1];
      const main = await text(`${this.lesson}/main.py`);
      if (WHILE_TRUE.test(main)) {
        throw new Error(
          `${this.lesson}/main.py has a while True loop. The sim calls pilot() 60 ` +
            "times a second for you, so pilot() must do its work and return.",
        );
      }
      const fs = this.mp.FS;
      for (const name of SHARED) fs.writeFile("/" + name, await text(name));
      try {
        fs.mkdir("/" + this.lesson);
      } catch {} // already there from an earlier load
      fs.writeFile(`/${this.lesson}/main.py`, main);
      this.harness.load(launcher, profile.thrusters.length);
      this.checkNames(profile);
    } catch (error) {
      this.error = tidy(error);
    }
    this.loads += 1;
  }

  checkNames(profile) {
    // Both name files are checked whichever ROV is flying: a wrong number in
    // either is a bug waiting for the day someone flies that ROV.
    const problems = [];
    for (const [module, ids] of Object.entries(this.ids)) {
      const found = this.harness.check(module, ids.join(","));
      if (found) problems.push(found);
    }
    if (problems.length) throw new Error(problems.join("\n"));
    const flying = profile.name.toLowerCase();
    const other = flying === "cube" ? "triangle" : "cube";
    if (this.harness.uses(other) && !this.harness.uses(flying)) {
      this.warning = `This lesson uses ${other}.py, but the ROV is the ${flying}. Press 1 or 2 to change ROV.`;
    }
  }

  // The new ROV has a different number of thrusters, so it needs a new Rov.
  changeProfile(profile) {
    this.profile = profile;
    if (this.error === null) {
      try {
        this.harness.new_rov(profile.thrusters.length);
        this.warning = null;
        this.checkNames(profile);
      } catch (error) {
        this.error = tidy(error);
      }
    }
  }

  // One call of the student's pilot(). `commands` gets one number per
  // thruster. Returns the claw and camera as the student left them, or null
  // if there is nothing to run (an error).
  call(inputs, commands) {
    if (this.error !== null || this.loading) return null;
    const i = inputs;
    const started = performance.now();
    let flags;
    try {
      flags = this.harness.step(
        commands,
        i.axes[0], i.axes[1], i.axes[2], i.axes[3], i.axes[4], i.axes[5],
        i.buttons,
        i.acceleration[0], i.acceleration[1], i.acceleration[2],
        i.depth, i.heading, i.amps,
        i.clawClosed ? 1 : 0, i.cameraOnboard ? 1 : 0,
      );
    } catch (error) {
      this.error = tidy(error);
      return null;
    }
    this.callMs = performance.now() - started;
    if (this.callMs > SLOW_CALL_MS && this.warning === null) {
      this.warning = `pilot() took ${this.callMs.toFixed(0)} ms -- it runs 60 times a second, so keep it quick.`;
    }
    return { clawClosed: Boolean(flags & 1), cameraOnboard: Boolean(flags & 2) };
  }
}
