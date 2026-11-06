# Part 3 lesson plan -- working notes

Internal notes for designing Part 3's lessons. `CLAUDE.md` holds the hardware
facts and measurements; this file holds the *teaching* decisions.

**Status, 2026-11-06: the sequence below is agreed with the user. No lesson is
written yet.** `board/controller.py` is still the spike every game runs against.
Before any sim lesson can be written, the sim needs the changes listed under
"What the sim needs" -- the Python-in-the-browser part of that is proven by a
spike (`spikes/browser_python/`, results below), nothing else is built.

The design was settled across two sessions: the one that built the hardware,
games and ROV sim (2026-10-14 .. 2026-11-05), and a lesson-design session
(2026-11-05 .. 06) whose decisions are recorded here.

## Who and why

- **High school students in a MATE ROV club.** Most have *some* programming
  (a class, a little Python or Java, Scratch) but none to rely on. Parts 1-2
  (repo `sea-otters-rov/led-panel-learn-python`, MatrixPortal M4 + 64x32 LED
  panel) come first, so by Part 3 they know variables, loops, `if`, lists,
  functions, `global`, reading an accelerometer, a little networking and
  classes (L206). Part 3 must still not assume much: plenty will join here.
- **Where the course is heading: an ROV that levels itself.** Every Part 3
  lesson is a step toward the club's real ROV control code -- reading inputs,
  mapping them to thrusters, mixing, calibrating "level", holding an attitude.
  The club's ROVs run an RP2350 and a **BNO085** IMU (on-chip sensor fusion, so
  real orientation comes nearly free); they have a depth sensor.
- **The user's own stated arc** (2026-10-14): "start with a bit of simple
  digital electronics, hooking the MCU to a few buttons, then sensors like the
  SEN0140 and ADS1115 with some analog joysticks, building up to [the board as
  a USB device] controlling simple PC games." Revised 2026-11-05: get to the
  maze fast, then the sim, **"where I expect them to spend most of their
  time."**

## Hard constraints from the user

- **No guns or shooters in any game.** A twin-stick shooter capstone was
  proposed and rejected. Games are peaceful and preferably ROV/MATE themed.
- **Simple browser games we write ourselves**, kept small. No new games are
  being built for Part 3 (decided 2026-11-05): the check page, the maze and
  the ROV sim carry everything.
- **The board is a plain gamepad**, so it can be swapped for an Xbox controller
  later. Calibration, dead zones and making tilt sensible belong to the board's
  Python. **Mapping inputs to thrusters belongs to the student's `pilot.py`,
  which runs inside the sim** (decided 2026-11-05). Games themselves still add
  no dead zone, smoothing, auto-repeat or calibration of their own.
- **Gamepad only, never a keyboard HID device**, so a student's loop cannot
  type into the editor it was saved from.
- **Ask before downloading anything.** MicroPython-WASM loads from jsDelivr at
  page load, pinned, like three.js; nothing is vendored into the repo.

## House style for lesson code (carried over from Parts 1-2)

The user edits lesson code toward these, consistently:

- **Name every number.** No bare literal unless self-evident; put it on its own
  line above the loop (or above `pilot()`).
- **Derive from the source of truth** so a try-this still works when a student
  changes one value.
- **One transformation per line.** Never compose two ideas in one expression.
- **Comments say why, not what**, and call back to earlier lessons.
- **Show more than the lesson needs** -- unpack all three accelerometer axes
  with real names even if only two are used; do not teach `_`.
- **Keep the debug `print()` live in the loop.** It is the instrument. (In the
  sim, `print()` from `pilot.py` needs somewhere visible to go -- see the sim
  changes.)
- **Try-these ask questions, not instructions**, and at least one is a
  deliberate trap with a readable error.
- **Verify every claim on hardware, try-thats included.** Parts 1-2 found
  several exercises that asked students to observe things that never happened.
  For sim lessons, "hardware" means the real sim driven through `sim.fly` and
  the student's actual `pilot.py`.
- American spellings; `snake_case` for anything a student might edit (no
  SCREAMING_CAPS in lesson code; library surface like `gamepad.A` and
  `cube.FORWARD_LEFT` keeps caps); f-strings; ruff format at 88 columns.

Carried over from Parts 1-2 and **decided** for this repo:

- One folder per lesson with a `main.py`, numbered `L301`, `L302`... The first
  docstring line of `main.py` is the lesson's picker entry: short, says what
  the student will *do*.
- **Switching lessons is explicit, as in Parts 1-2** (user, 2026-11-06): a
  picker rewrites one launcher line. Board lessons live in `board/L3xx_*/`
  with `board/code.py` as the launcher; sim lessons live in `sim/L3xx_*/` with
  `sim/pilot.py` as the launcher (one line, `from L305_tank_drive import
  main`). One `tools/lesson.py` lists both kinds and rewrites whichever
  launcher the chosen lesson belongs to. **Not built yet.**
- Course modules at the board root (`gamepad.py`, `sticks.py`, like Part 1's
  `screen.py`) are the surface students use; `lib/` is third-party only. The
  sim's equivalents are `sim/sim.py`, `sim/cube.py`, `sim/triangle.py`.
- `docs/lesson-plan.md` (one page for students and parents) vs this file
  (internals). Not written yet.

## The sequence

| # | Folder | Picker line | The one new idea | Student sees | Min |
| --- | --- | --- | --- | --- | --- |
| 301 | `board/L301_press_a_button` | Wire a button and make the board's light answer it. | Digital input; `Pull.UP`, so pressed reads `False` | Onboard LED while held, live `print` | 20 |
| 302 | `board/L302_be_a_gamepad` | Make your button press A on the Controller check page. | The board as a USB gamepad (`gamepad.py`, buttons numbered from 0) | "0 A" lights on `pad_test.html` | 20 |
| 303 | `board/L303_tilt_the_maze` | Wire the tilt sensor and roll the marble through the maze. | I2C: a sensor on four wires; acceleration becomes a stick | Marble rolls through the maze | 35 |
| 304 | `board/L304_finish_the_controller` | Add both thumbsticks and the rest of the buttons. | A second chip on the same bus (ADS1115 through `sticks.py`) | Every stick and button on the check page; maze by stick | 35 |
| 305 | `sim/L305_tank_drive` | Drive the cube ROV with tank controls. | Code that runs in the sim: `pilot(pad, rov)`, thruster names | Drives and turns -- backwards at first (the sign trap) | 30 |
| 306 | `sim/L306_every_direction` | Add up, down and sideways. | More inputs to more thrusters; a button becomes a named power | Flies in 3D | 30 |
| 307 | `sim/L307_grab_a_crab` | Work the claw and collect your first crab. | State that lasts between calls; a press, not a hold | First crab in the basket | 30 |
| 308 | `sim/L308_tilt_to_pitch` | Tilt your controller to pitch and roll the ROV. | Mixing: one thruster serves three inputs, then clamp | Fully controlled cube | 35 |
| 309 | `sim/L309_level_yourself` | Make the ROV hold itself level with its own accelerometer. | Feedback: measure, compare, correct (P control) | The heavy crab no longer drags the nose down | 35 |
| 310 | `sim/L310_the_dip_that_stays` | Make the last bit of the dip go away. | Feedback that learns a steady load (I term) | Level, even holding the heavy crab | 30 |
| 311 | `sim/L311_crab_mission` | Fly the whole mission on your own controls. | *(assembly)* | Capstone: every crab, heavy one included | 60-90 |
| 312 | `sim/L312_triangle` | Stretch: map the controls to the triangle ROV. | Thrusters at angles | Not expected to be finished | -- |

**Total: ~1h50 on the board (301-304), ~3h10 in the sim (305-310), plus
60-90 min for the capstone. ~6h15.** The sim is where the time goes, as the
user wants.

**Renumbered 2026-11-06.** A draft had 304 "find level" and 306 "every
button"; both were dropped (below) and the rest closed up. A worked answer for
the capstone (Part 1's L199 pattern) is undecided.

Per lesson:

- **301** doubles as the smoke test, like Part 1's L101: a save reaches the
  board, the Serial Monitor works, an LED lights. The XIAO's user LED needs
  checking on hardware (`board.LED`, and whether it is active-low).
- **302** -- the page sees no gamepad until a button is pressed after it
  loads (`CLAUDE.md`), so the first press *is* the proof. `boot.py` is given
  and never edited.
- **303** carries the "level" measurement as given code: the average of a few
  dozen readings at startup, subtracted in the loop (what `controller.py` does
  with `level_x`/`level_y`). **The SEN0140 driver does not zero the
  accelerometer** -- `imu_calibration.py` removes only gyro bias and
  magnetometer offset -- so without it the marble creeps on a level desk. That
  makes the try-this: "delete the level line: what does the marble do?" Also
  here: `full_tilt` (sensitivity) and the tilt dead zone. A dropped draft
  lesson 304 had been calibration alone; the user cut it on 2026-11-06.
- **304** uses `sticks.py` as given (decided: provide it, don't build it). The
  dead zone is a try-this: `dead_zone = 0` and watch the ROV creep in 305.
  Stick or tilt for the maze is a variable, not a button toggle. **This lesson
  also wires every button**, by the course's pin picture (below), so that **at
  the start of 305 every board has the same pins on the same gamepad buttons;
  only `pilot.py` differs** (user, 2026-11-06). The buttons loop -- a tuple of
  (button, pin) pairs -- is given code. After 304 the board is never edited
  again in Part 3: it runs 304 throughout the sim lessons.
- **305** starts from a given example: left stick up/down to the left forward
  thruster, right stick to the right one, which is how the club's ROVs were
  driven last season. It cannot go up or down or work the claw. The sign trap
  comes free: a stick pushed away reads -1, a thruster wants +1 for forward.
- **306** adds the four verticals together (buttons, so full power or a named
  fraction) and the two side thrusters.
- **307** -- the claw is `rov.claw_closed`, which stays set until changed, so
  hold-to-grip works with no new idea. A one-button toggle needs last call's
  button state (a module variable and `global`, from Part 1's L108), and is
  the lesson's real content. The camera (`rov.camera_onboard`) gets the same
  treatment, on a button the student picks.
- **308** is the first time a thruster gets more than one input:
  `up FL = heave + pitch + roll` and so on, which passes 1.0 and needs a clamp.
  Hand tilt *commands* thrust here, and the cube does not end up at the angle
  being held -- its float pushes back. That is the setup for 309.
- **309** closes the loop on `rov.acceleration`, the ROV's own (simulated)
  accelerometer: for small tilts, x and y are about g times the angle, so
  `correction = gain * y` is a working leveler with no trig. The hand tilt
  becomes the *target*. Needs a heavy crab to matter (below).
- **310** -- a P-only leveler leaves a steady dip under a constant load,
  because its correction exists only while there is an error. The integral
  term learns the load. `CLAUDE.md` has the sim's own evidence (the triangle
  at 5.3 deg without it, worse than its float alone) and the trap that came
  with it (learning during a big deliberate tilt overshot to 44 deg).
- **311** -- the mission with the heavy crab. The "they will ask for it"
  extras below are its make-it-yours list.
- **312** -- the triangle's horizontal thrusters are 120 deg apart, so mixing
  needs trig or a given table. The user does not expect students to finish.

### Pushback and risks

- **`global` in 307 is a Part 1 idea (L108) that Part 3 newcomers will not
  have.** It is one line and the lesson can teach it in place, but it is the
  one spot where joining at Part 3 shows.
- **304 is the heaviest board lesson**: a second chip, two sticks, eight more
  buttons of wiring. If it runs long, the wiring can be a pre-class job.
- **Sim lessons need the local server running** (`tools/serve.py`); GitHub
  Pages cannot serve `sim/`. The sim falls back to its built-in pilot there.

## Where each concept first appears

| Concept | First taught | Needed by |
| --- | --- | --- |
| Digital input; `Pull.UP`, pressed reads `False` | 301 | 302, 304 |
| The onboard LED (digital output) | 301 | -- |
| The board as a USB gamepad; buttons numbered from 0 | 302 | 303, 304 |
| The Controller check page as the debugging tool | 302 | everything |
| I2C: a sensor on four wires | 303 | 304 |
| Acceleration scaled into -1..1 (`full_tilt`, clamp) | 303 | 308, 309 |
| Dead zone | 303 | 304, 305 |
| Calibration: average at startup ("level") | 303 | 309 |
| A second chip on the same bus; I2C addresses | 304 | -- |
| A module's objects (`sticks.py`'s `.x`, `.y`) | 304 | 305 |
| A tuple of pairs, unpacked in a `for` | 304 | -- |
| Code that runs in the sim; `pilot()` called 60 times a second | 305 | all sim lessons |
| Thruster names as constants (`cube.FORWARD_LEFT`) | 305 | all sim lessons |
| Sign conventions (stick away = -1) | 305 | 308 |
| Type hints -- read, not written (the header is given) | 305 | -- |
| A button becomes a named power | 306 | 311 |
| State that lasts between calls; a press vs a hold | 307 | 310, 311 |
| Mixing: adding inputs per thruster, then clamp | 308 | 309, 311, 312 |
| Feedback / P control | 309 | 310, 311 |
| An accumulator over time (I term) | 310 | 311 |
| Scaling every thruster together (current limit) | 311 extra | -- |
| Angle wraparound (heading) | 311 extra | -- |
| Trig: thrusters at angles | 312 | -- |

## Decisions, 2026-11-05 .. 06

Each was an open question or an undecided idea in the earlier notes.

- **New games: none.** Sonar Ping (reaction timer), Block Drop (auto-repeat),
  Descent (response curves) and Thruster Drive (2D mixing) are all dropped.
  Auto-repeat and response curves are out of the course; response curves can
  come back as a capstone extra if claw work feels twitchy.
- **The RP2350's own ADC is skipped**; the sticks go straight to the ADS1115
  (user: "let's go straight to the ADS").
- **Tilt before sticks**: four wires, straight to the maze, and a place to
  talk about I2C. Sticks then give a second way to play the maze.
- **Modules: provide `gamepad.py` and `sticks.py`; students do not build
  them.**
- **No board-in-the-loop thruster mode, no WebHID, no 8-axis descriptor.** The
  student's mapping runs in the sim, so the sim's own sensors are right beside
  it and self-leveling needs no channel back to the board.
- **Student code in the sim is Python, run by MicroPython-WASM.** Pyodide (10
  MB, seconds to start) and Brython/Skulpt (Python translated to JS, errors
  stop looking like Python) were the alternatives. Same dialect as the board,
  and the mapping is close to what could run on the ROV's own RP2350.
- **Students edit in VS Code; a local server live-reloads the sim.** Autocomplete
  and lint come from VS Code reading real `.py` files (`sim.py`, `cube.py`),
  not from the browser.
- **Thruster names are constants, never strings**, for both profiles from day
  one (`cube.py`, `triangle.py`), checked against `rov_profiles.js` when the
  sim loads them. A misspelling is a Pylance underline and a readable
  `AttributeError`. (MicroPython has no `enum`; class-free module constants,
  like `gamepad.A`.)
- **Type hints are fine** (`def pilot(pad: Pad, rov: Rov)`): students fill in
  bodies; headers are given.
- **Buttons are attributes**: `pad.left_bumper`, not `pad.pressed(LB)`.
- **`pilot()` runs at a fixed rate**, 60 times a second (every 4th 240 Hz
  physics step), the same on every laptop.
- **The ROV's sensor is an accelerometer vector**, `(x, y, z)` in m/s^2 like
  the matrix board's -- **gravity only** for now. Motion in the reading (and
  the smoothing it would need) is deferred; the real ROV's BNO085 fuses it
  away anyway. No gyro: the user does not expect students to use one.
- **Self-leveling must be noticeable on the cube** -- the club had exactly
  this problem last season, mostly from low stability and partly from heavier
  items on a long claw arm. Starting estimates, to tweak: the cube's float
  **6 cm** above its center of mass (was 20), and **one 5 N heavy crab** in
  the mission. Hand calculation (righting up to ~7 N m, claw ~0.4 m ahead):
  ~2 deg dip with a normal crab, ~17 deg with the heavy one -- enough for the
  claw camera to lose the basket. Verify in the sim; the cube's numbers in
  `CLAUDE.md` all change with it.
- **The sim keeps its built-in pilot** (`PilotAssist`) as a demo mode and the
  GitHub Pages fallback; pilot mode is the student's.
- **Camera switching is the pilot's** (`rov.camera_onboard`), and **students
  decide which button does it** (user, 2026-11-06) -- the real ROV needs the
  same. Reset and profile switching move to keyboard keys that are not gamepad
  stand-ins.
- **Pin map, final** (user, 2026-11-06; matches `controller.py` and the pin
  picture students get):

      D0 LB    D1 RB    D2 LT    D3 RT    D6 Start
      D7 A     D8 B     D9 X     D10 Y    D4/D5 I2C (SDA/SCL)

  No stick clicks. `CLAUDE.md` matches (2026-11-06); **`README.md`'s wiring
  table still shows the old layout** (A D9, B D10, X D0, Y D1, clicks D7/D8).
- **The mounting swaps in `controller.py` are how students will build it
  too** (user, 2026-11-06): the A0/A1 stick is the right one, the left stick is
  turned 180 degrees from it, and the SEN0140's x/y are swapped. They are now
  one commented block ("How this breadboard is built") so a board built
  another way -- both sticks facing up, say -- is a guided one-line change.
  Lesson 304's code keeps that block and those comments.

## `pilot()` -- what students write against

Draft surface, from the decisions above. The sim calls `main.pilot(pad, rov)`
60 times a second; thruster commands reset to 0 before each call, everything
else on `rov` keeps its value.

    pad.left_x, pad.left_y, pad.right_x, pad.right_y, pad.tilt_x, pad.tilt_y
                                    -1.0 .. 1.0, exactly what the board sent
    pad.a, pad.b, pad.x, pad.y, pad.left_bumper, pad.right_bumper,
    pad.left_trigger, pad.right_trigger, pad.start
                                    True while held

    rov.thrust(cube.FORWARD_LEFT, power)   -1.0 .. 1.0
    rov.claw_closed                 set True/False; stays until changed; readable
    rov.camera_onboard              same
    rov.acceleration                (x, y, z) m/s^2, gravity only; level reads
                                    about (0, 0, 9.8) -- axis signs to be fixed so
                                    they match the board's tilt sense
    rov.depth                       m below the surface (the real ROV has one)
    rov.heading                     compass degrees (the BNO085 gives one)
    rov.amps                        the sim's current estimate for the whole ROV

**What students will ask for, and the answer** (user, 2026-11-06):

| They ask | Data | How hard |
| --- | --- | --- |
| One button toggles the claw | `rov.claw_closed` (readable) | Easy -- it is 307 |
| A button to rise to the surface | `rov.depth` | Easy after 309: depth hold is leveling's P control on another reading |
| A button to face the crab box | `rov.heading` | Medium. The ROV cannot know where the box is: press one button facing it to remember the heading, another to turn back to it. Trap: 350 to 10 deg is +20, not -340 |
| Stay under 18 A | `rov.amps` | Medium. Scale *every* thruster by one factor; clipping one changes the direction (`CLAUDE.md`, stabilizer bug 3). Nudge the factor down while over, up while under |

Depth hold, heading hold and leveling are one idea on three sensors -- a sign
the sequence's center (309) is in the right place.

## What the sim needs before lesson 305

None of this is built except the spike.

1. **Pilot mode in `rov_sim.html`**: load MicroPython once; read the
   launcher line in `sim/pilot.py`; write that lesson's `main.py` plus
   `sim.py`, `cube.py`, `triangle.py` into its filesystem; call `pilot()`
   every 4th physics step; show Python errors with the harness's own frame
   removed; show `print()` output somewhere visible; reload on save through
   `serve.py`'s `/changes`. Fall back to `PilotAssist` with no `sim/` (Pages).
2. **`sim/sim.py`** with `Pad` and `Rov` as above, real classes so Pylance
   autocompletes -- the same file the browser runs.
3. **`sim/cube.py`, `sim/triangle.py`**: one constant per thruster in
   profile order, checked by name at load.
4. **A simulated accelerometer** on the vehicle, gravity only, with a switch
   for motion later. Plus `depth`, `heading`, `amps` exposed.
5. **Profile changes**: cube float to 6 cm; one 5 N heavy crab; decide what a
   big dip costs (camera loses the basket; maybe the crab slips past some
   angle). Re-verify and update `CLAUDE.md`'s cube numbers.
6. **Keys**: reset and profile switching on keys that are not gamepad
   stand-ins in `pad.js`.
7. **`tools/serve.py`** watches `sim/` as well; **`tools/lesson.py`** (new
   here) picks board and sim lessons.
8. Still open from before: **the sim's fps on a school laptop** (press Q to
   step resolution).

## Spike: student Python in the browser (2026-11-05)

`spikes/browser_python/` + `tools/serve.py`, served at
`http://localhost:8770/spikes/browser_python/index.html` (launch config
`serve`). Runs a tank-drive `pilot.py` through
`@micropython/micropython-webassembly-pyscript@1.27.0` and draws the eight
commands. Measured on the dev machine:

    MicroPython download               mjs 105 KB + wasm 424 KB; 33 + 45 ms uncached
    start-up                           16-27 ms
    one JS -> Python call, 6 floats    ~2.5 us
    tank pilot() + harness             ~11-15 us
    ... returning 8 commands           ~26 us (written into a JS Float64Array)
                                       ~35-44 us (as a comma-joined string)
    at 240 calls/s                     ~6 ms per second, 0.6% of a core
    save in VS Code -> new code live   ~15 ms, no page reload

Found on the way:

- **`localhost` cost 310 ms per request** against a server bound to 127.0.0.1:
  Chrome tries ::1 first. `serve.py` listens on both loopbacks (5 ms).
- **One MicroPython per page.** A second `loadMicroPython()` broke the first
  ("NULL object").
- **A returned tuple cannot be indexed from JS**; hand results back by writing
  into a typed array JS passes in.
- **Tracebacks arrive whole**: `File "pilot.py", line 11, in pilot` /
  `AttributeError: module 'cube' has no attribute 'FORWARD_RIGTH'`.
- **Type hints are accepted. No `enum`, no `time.monotonic()`** (`ticks_ms`
  exists) -- the fixed call rate means students never need a clock.
- Not verified: Pylance underlining a misspelled constant in VS Code (basic
  type checking reports unknown module attributes, so it should).

## What exists to teach with

**Board side** (`board/`, XIAO RP2350, CircuitPython 10.3.1):

- `boot.py` -- 6-axis, 16-button gamepad descriptor. Runs only on a hard
  reset, so students never edit it.
- `gamepad.py` -- `Gamepad` with `left_x`, `left_y`, `right_x`, `right_y`,
  `tilt_x`, `tilt_y` as -1.0..1.0 and buttons as named constants numbered from
  0 like the browser (`A B X Y = 0-3`, `LB RB LT RT = 4-7`, `BACK START = 8, 9`,
  `LEFT_CLICK RIGHT_CLICK = 10, 11`, D-pad 12-15). `set_button(name,
  pressed)`, `send()`.
- `sticks.py` -- the only code that knows about volts. `connect(i2c)` returns
  two `Stick`s reading `.x`, `.y` as -1.0..1.0, centers measured at startup,
  default dead zone 0.06, `flip_x/flip_y`. Each read is a ~2 ms ADS1115
  conversion, so read once per loop.
- `imu.py` and friends (SEN0140: ADXL345 accel, ITG-3205 gyro, VCM5883L
  magnetometer, BMP280 barometer). Accelerometer read ~0.4 ms at 400 kHz.
- `controller.py` -- the spike, and in effect lesson 304's finished form.
  Sticks + tilt + nine buttons -> gamepad, ~104 loops/s. Startup "level"
  measurement (averaging 40 readings), `tilt_amount()` (dead zone, then scale
  to full tilt, keep the sign), `use_tilt`, a twice-a-second status print with
  loops/s.

**Browser side** (`games/`, published to GitHub Pages):

- `pad.js` -- shared input; keyboard fallback for everything; **I** shows an
  inspector with the raw axes and buttons the page receives.
- `pad_test.html` -- the controller check page: three sticks (left, right,
  tilt) and every button. The debugging tool students will use most.
- `marble_maze.html` -- tilt a board, roll a marble through levels. Reads the
  left stick, so `use_tilt = True` on the board is what makes tilt play it.
- `rov_sim.html` + `rov_physics.js` + `rov_profiles.js` -- a 3D MATE-style
  crab-collection mission with real 6-DOF physics (thrusters, buoyancy, drag,
  added mass, current draw against a 15 A fuse), two ROV profiles (`cube`,
  `triangle`). `PilotAssist` (the mixer + stabilizer) is separate from
  `Vehicle` (the physics); pilot mode replaces `PilotAssist` with the
  student's `pilot()`.

## Background worth keeping

- **"Who owns the mapping" is Part 2's "who owns the ball" again.** The game
  stays fixed and the student's code adapts to it.
- **Tilt in the pilot's hand vs. tilt on the vehicle.** 308 uses hand tilt as
  a command; 309 makes it a target and measures the vehicle's own attitude --
  which is what the real ROV's IMU does.
- **Measured physics facts make good lesson material**: stability trades
  against agility and current (the current cube holds 16 deg at 18.3 A; the
  triangle 35 deg at 5.6 A). These numbers change when the cube's float moves
  to 6 cm -- re-measure before quoting them in a lesson.
- The stabilizer tuning stories in `CLAUDE.md` (newtons not commands, lag as
  damping, scale don't clip, integral only near a still target) are the
  answer key for 309-311's hard cases.
- A keyboard HID with an "armed" switch was dropped in favor of gamepad-only;
  the "deliberate safe state before anything moves" habit is still worth
  teaching somewhere, since the ROV needs it.
