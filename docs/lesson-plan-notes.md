# Part 3 lesson plan -- working notes

Internal notes for designing Part 3's lessons. `CLAUDE.md` holds the hardware
facts and measurements; this file holds the *teaching* decisions.

**Status, 2026-11-06: the sequence below is agreed with the user. The four
board lessons, 301-304, are written and verified on hardware**, the sim's
pilot mode is built and verified (see "What the sim needs"), and **the sim
lessons 305-311 plus the worked answer 399 are written and verified in the
sim**. `board/controller.py` is still in `board/` -- 304 is
its lesson form -- and the games' contract in `CLAUDE.md` still names it.

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
| 305 | `sim/L305_tank_drive` | Drive the cube ROV with tank controls. | Code that runs in the sim: `pilot(pad, rov)`, thruster names | Drives and turns | 30 |
| 306 | `sim/L306_every_direction` | Add up, down and sideways. | More inputs to more thrusters; a button becomes a named power | Flies in 3D | 30 |
| 307 | `sim/L307_grab_a_crab` | Work the claw and collect your first crab. | State that lasts between calls; a press, not a hold | First crab in the basket | 30 |
| 308 | `sim/L308_tilt_to_pitch` | Tilt your controller to pitch and roll the ROV. | Mixing: one thruster serves three inputs, then clamp | Fully controlled cube | 35 |
| 309 | `sim/L309_level_yourself` | Make the ROV hold itself level with its own accelerometer. | Feedback: measure, compare, correct (P control) | The heavy crab's dip cut from 15 deg to ~5 | 35 |
| 310 | `sim/L310_crab_mission` | Fly the whole mission on your own controls. | *(assembly, two TODOs)* | Capstone: every crab, heavy one included | 60-90 |
| 311 | `sim/L311_triangle` | Stretch: map the controls to the triangle ROV. | Thrusters at angles | Not expected to be finished | -- |
| 399 | `sim/L399_crab_mission_done` | Lesson 310's crab mission with every TODO filled in. | *(worked answer)* | -- | -- |

**Total: ~1h50 on the board (301-304), ~2h40 in the sim (305-309), plus
60-90 min for the capstone. ~5h45**, the same as Part 1. The sim is where the
time goes, as the user wants.

**All of 301-311 and 399 are written and verified** (board lessons on
hardware, sim lessons through `sim.fly` with the lesson's own `pilot()`).

**Renumbered 2026-11-06, twice.** A draft had 304 "find level" and 306 "every
button"; both were dropped and the rest closed up. Then the integral lesson
("the dip that stays") was dropped -- see "PID is Part 4" under Decisions --
and the capstone and the triangle moved up to 310 and 311.

**`L399_crab_mission_done` shows in the lesson picker**, like Part 1's L199:
`tools/lesson.py` lists any `L<number>_` folder with a `main.py`. If the
answers should not be one keystroke away, move it out of `sim/`.

Per lesson:

- **301 -- written and verified 2026-11-06** (`board/L301_press_a_button`).
  Doubles as the smoke test, like Part 1's L101: a save reaches the board,
  the Serial Monitor works, an LED lights. **The XIAO's USR LED
  (`board.LED`) is active-low** -- measured: it lit while a `Pull.UP` button
  was held with `led.value = button.value`. The lesson says so in a comment
  and writes `light.value = not pressed`; a try-this asks why
  `light.value = pin_value` lights the same way. The first button goes on
  **D7**, where A stays for the whole course. Verified on a D0 button (the
  test board's): released prints `pin True  pressed False`; held lights the
  LED; `Pull.DOWN` reads False released (and GND pressed), so the light just
  stays on; `board.D20` is `AttributeError: 'module' object has no attribute
  'D20'`. Also proved the picker's board path: `lesson.py 301` rewrote
  `board/code.py` from `import controller` and the board restarted into it.
- **302 -- written and verified 2026-11-06** (`board/L302_be_a_gamepad`).
  The page sees no gamepad until a button is pressed after it loads
  (`CLAUDE.md`), so the first press *is* the proof. `boot.py` is given and
  never edited. Keeps 301's button and light, adds `pad.set_button(gamepad.A,
  pressed)` and `pad.send()`, prints `pad.buttons` as 16 binary digits.
  Verified with the button on D7: `pad_test.html` (recorded in the browser
  pane) saw "CircuitPython HID", 6 axes, 16 buttons, and 16 presses as button
  0 and nothing else; the shortest, 60 ms, was caught at `check_every =
  0.05`. Trap `gamepad.a` is `AttributeError: 'module' object has no
  attribute 'a'`.
- **303 -- written and verified 2026-11-06** (`board/L303_tilt_the_maze`):
  `board.I2C()` and `imu.IMU`, the same x/y swap as `controller.py`, tip =
  reading - level, `tip / full_tilt` to `pad.tilt_x/y` and copied to the left
  stick for the maze; keeps the A button. Verified on the board through
  `pad_test.html`: right edge down reads x +1.00, far edge down y -1.00, and
  so on (a first run with the board turned 180 deg mirrored every one, as it
  should). At rest: level x -0.29, y -0.96 m/s^2 and tip wanders +-0.1, so
  the stick sits within +-0.02 -- without the level subtraction it would sit
  at -0.06, -0.19 and the marble creeps (the first try-this). `full_tilt = 0`
  is `ZeroDivisionError: division by zero`.

  Original plan for 303: carries the "level" measurement as given code: the average of a few
  dozen readings at startup, subtracted in the loop (what `controller.py` does
  with `level_x`/`level_y`). **The SEN0140 driver does not zero the
  accelerometer** -- `imu_calibration.py` removes only gyro bias and
  magnetometer offset -- so without it the marble creeps on a level desk. That
  makes the try-this: "delete the level line: what does the marble do?" Also
  here: `full_tilt` (sensitivity) and the tilt dead zone. A dropped draft
  lesson 304 had been calibration alone; the user cut it on 2026-11-06.
- **304 -- written and verified 2026-11-06**
  (`board/L304_finish_the_controller`): `controller.py` rewritten as a lesson
  on top of 303 -- `busio.I2C` at 400 kHz, the commented mounting block, the
  nine (button, pin) pairs, tilt and level as in 303, `use_tilt` as a
  variable, a live print every loop. Verified on the board: the user
  confirmed both sticks and the buttons on `pad_test.html` (the recorder's
  tail: left stick up -1.00, down +1.00, right +0.99, left -0.73, A). **The
  live print costs speed**: ~64 loops/s (295 lines in the verify window)
  against `controller.py`'s 91 printing twice a second -- still about one
  reading per game frame. At 100 kHz it fell to 196 lines (the try-this).
  `sticks.py` now adds `+ 0.0` so a flipped resting stick prints `+0.00`, not
  `-0.00`. **Two buttons on D7 is `ValueError: RX in use`** -- D7's other
  name -- so the try-this explains RX. **Classroom gotcha, seen on the test
  board:** a stick with its x and y wires swapped cannot be fixed by the
  mounting block's flips (pushing up moves the dot sideways); it needs
  rewiring.

  Original plan: uses `sticks.py` as given (decided: provide it, don't build it). The
  dead zone is a try-this: `dead_zone = 0` and watch the ROV creep in 305.
  Stick or tilt for the maze is a variable, not a button toggle. **This lesson
  also wires every button**, by the course's pin picture (below), so that **at
  the start of 305 every board has the same pins on the same gamepad buttons;
  only `pilot.py` differs** (user, 2026-11-06). The buttons loop -- a tuple of
  (button, pin) pairs -- is given code. After 304 the board is never edited
  again in Part 3: it runs 304 throughout the sim lessons.
Every sim lesson ships WORKING; the traps are in the try-these (the sign trap
moved out of 305's code into a question). Each copies the last one forward.
Measured with the final physics (cube float 10 cm, pitch/roll damping 3).
**On 2026-11-07 the thrusters changed to the maker's table** (10.3 N both
ways and 3.25 A at 13 V, was a guessed 11.7 N forward, 8.2 N reverse, 5.6 A).
The same day, thrust and current started falling with the water speed
into each propeller (`ZERO_THRUST_SPEED`, a 4 m/s guess). Figures re-measured
with both are marked (11-07); the rest are from before, and any amps among
them are now roughly 60% too high:

- **305 -- written and verified.** Left stick to `FORWARD_LEFT`, right to
  `FORWARD_RIGHT`, with the minus sign explained. Full forward 0.51 m/s at
  6.3 A (11-07); left stick alone turns right (89 deg in 2 s); **half power is
  0.35 m/s, not half speed, and 2.5 A, not half the current** (11-07) -- so the try-this
  asks "is half power half speed?". Without the minus signs it drives
  backwards 1.2 m in 3 s.
- **306 -- written and verified.** The bumpers heave (RB up, LB down;
  `heave_power` 0.5, named -- triggers until 2026-11-07, see "Buttons the
  lessons assume"), right stick x slides on both side thrusters. Rise reaches
  the surface in 3 s, dive 0.48 m/s; both bumpers: dive wins (last `if`); let
  go and it coasts 0.65 m and stops (neutral); `SIDE_FRONT` alone spins it
  141 deg in 3 s; full-power dive 11.6 A (11-07). (A `heave_power = "half"`
  try-this, erroring only on a press, was removed by the user 2026-11-07.)
- **307 -- written and verified.** One-button claw toggle on A (the right
  bumper until 2026-11-07; verified on A that day):
  `claw_was_pressed` at module level, `global`, `pressed and not
  was_pressed`. Normal grab works (1.5 A); without the `and not` the claw
  flips every call (`CoCoCo...`); **without `global`, the error only comes on
  the first press** -- `NameError: local variable referenced before
  assignment`, because `and` stops early while the button is up. The heavy
  crab pitches the nose ~15 deg and the ROV sinks -- **so far it cannot be
  dropped in the basket without raising `heave_power`** (user, 2026-11-07).
  Not designed, but kept on purpose: it gives a reason to change the lift
  settings, and to want tilt control, right before 308. The heavy-crab
  try-this points there. Don't "fix" it by lightening the crab or raising
  the default `heave_power`. Student module state
  survives R; only a save reloads it. Camera is a try-this, on a button the
  student picks; **from 308 on the lessons come with B switching the
  camera** (user, 2026-11-07), the same press-catching code as the claw.
- **308 -- written and verified.** `pitch = tilt_y * pitch_power`, `roll =
  tilt_x * roll_power`, four mixed lines, a `clamp()` function. Full forward
  tilt settles at 19.4 deg and the depth holds (11-07): the front pair's push
  down cancels the back pair's push up exactly. Until the maker's table, reverse
  was a guessed 70% and the ROV floated up unasked -- the try-this now asks
  why it doesn't, and what weaker reverse would do.
  **`clamp()` hides the red "asked" readout** -- the try-this removes the
  clamp on one thruster to show `asked 1.50`. With the heavy crab, holding
  level by hand takes ~80% back tilt.
- **309 -- written and verified.** P-only leveler on `rov.acceleration`, hand
  tilt as the target (`max_tip` 5, like 303's `full_tilt`), `level_gain`
  0.3. Heavy crab, depth held: 15.1 deg unleveled, ~5 deg at 0.3, ~10 at 0.1;
  at 1.0 it never settles (+-5 deg, up to 19 A). Full tilt reaches ~19 of
  30.7 deg (P alone stops short). **A reversed error sign flips the ROV over
  backwards within 4 s** when the controller is tipped forward -- the try-this.
- **310 -- capstone, written and verified.** 309's pilot rearranged so every
  power is worked out first and sent at the end, plus two TODOs: depth
  hold on a button of the student's choice, X or Y (P on `rov.depth`, to a
  depth they pick), and stay under the fuse (one shared scale on
  `rov.amps`). The camera toggle was a TODO until 2026-11-07, when B came
  given from 308 on. **Face the basket** (remember `rov.heading`, turn back
  the short way) was TODO 1 until the same day: it needs two buttons, and
  with LB/RB heaving and A on the claw only B, X and Y were left for three
  jobs. It went to an extra for LT/RT, then the user replaced that extra with
  **one-stick drive** (drive and turn on the left stick -- arcade mixing).
  Runs as given; **the whole mission completes in
  pilot mode** through the lesson's own claw code (all five crabs, the heavy
  one included, landed in the basket and the sim declared it finished).
- **399 -- worked answer, verified 2026-11-07.** A claw, B camera, Y holds
  just under the surface (0.41 m for a 0.4 target; ~0.5 with the heavy
  crab), current limited at **15 A** (the fuse L310 names; was 18 until
  11-07, which acted only with every input held -- L310's own code draws
  16.0 A for forward + slide + rise, 20.4 with full tilt too), and one-stick
  drive (`one_stick = True`; forward 0.51 m/s straight, full right turns
  51 deg in 1 s on the spot; False is tank drive). With everything held the
  limit hovers at 14.9-15.7 A. Its face-the-basket answer was dropped with
  that extra, before it was ever committed; the "they'll ask" table below
  has the method (and `turn_gain` 0.01 worked; 0.02 swung +-5 deg).
- **311 -- stretch, written and verified as a starting point.** Up/down and
  claw given; driving and leveling are TODOs with the measured push direction
  of each edge thruster. Forward-only (EDGE_LEFT +1, EDGE_RIGHT -1) drives straight
  (11-07; at the old 70% reverse it turned 34 deg in 2 s), but **lifts the nose
  5.5 deg and climbs 0.27 m in 5 s**: the edge thrusters sit below the center
  of mass. The hint says so. Unleveled, the heavy crab pitches the triangle
  ~41 deg (not onto its nose: the low claw swings under it as it pitches).

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
| A button becomes a named power | 306 | 310 |
| State that lasts between calls; a press vs a hold | 307 | 310 |
| Mixing: adding inputs per thruster, then clamp | 308 | 309, 310, 311 |
| Feedback / P control | 309 | 310 (depth, heading) |
| Scaling every thruster together (current limit) | 310 TODO | -- |
| Angle wraparound (heading) | 310 TODO | -- |
| Thrusters at angles | 311 | -- |

Not in Part 3: the integral and derivative terms. PID is Part 4.

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
  items on a long claw arm, pitching about 20-30 deg. Built: the cube's float
  **10 cm** above its center of mass (was 20; 6 was tried), and **one 8 N
  heavy crab** -- 15 deg unleveled on the cube, ~41 on the triangle. The user
  chose 10 cm over 6 (2026-11-06): less pitch from the crabs, while the
  triangle stays the tippy, "unstable by default" design.
- **PID is Part 4** (user, 2026-11-06: "I haven't gone into PIDs with them
  yet and doing it as part of coding will be difficult"). Part 3 levels with
  P only. Why it had to be decided: P-only with the sim's original damping
  guess never settled, and adding the planned integral lesson made it worse;
  only a full PID settled. Raising the cube's pitch/roll damping guess from
  0.5 to 3 (`rov_profiles.js`, with a pool test to measure the real one) made
  P alone settle in ~1.5 s. The dropped lesson was 310 "the dip that stays";
  no lesson replaced it (a "trim" button lesson was offered and not wanted).
  "Unless this convinces them to abandon the triangle idea altogether" --
  the triangle (311) is where the need for more than P shows.
- **The sim keeps its built-in pilot** (`PilotAssist`) as a demo mode and the
  GitHub Pages fallback; pilot mode is the student's.
- **Camera switching is the pilot's** (`rov.camera_onboard`) -- the real ROV
  needs the same. Students pick its button in 307's try-this; **from 308 on
  the lessons give it on B** (user, 2026-11-07; was "students decide",
  2026-11-06). Reset and profile switching move to keyboard keys that are not gamepad
  stand-ins.
- **Pin map, final** (user, 2026-11-06; matches `controller.py` and the pin
  picture students get):

      D0 LB    D1 RB    D2 LT    D3 RT    D6 Start
      D7 A     D8 B     D9 X     D10 Y    D4/D5 I2C (SDA/SCL)

  No stick clicks. `CLAUDE.md` matches (2026-11-06); **`README.md`'s wiring
  table still shows the old layout** (A D9, B D10, X D0, Y D1, clicks D7/D8).
- **Buttons the lessons assume: LB, RB, A, B, X, Y** (user, 2026-11-07). LT
  and RT (D2, D3) are not wired by default -- an extra a student can add --
  and no lesson relies on Start either. So the bumpers heave (RB up, LB down,
  306 on) and A works the claw (307 on), leaving B, X and Y for the student's
  own buttons; the one two-button idea, face the basket, was dropped (see
  310).
  Lesson 304's button list still names LT and RT: an unwired pin with the
  pull-up just reads "not pressed".
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
| A button to face the crab box | `rov.heading` | Medium, and two buttons -- not in the lessons (only X and Y are free in 310); for a student who wires LT/RT. The ROV cannot know where the box is: press one button facing it to remember the heading, another to turn back to it. Trap: 350 to 10 deg is +20, not -340 |
| Stay under 18 A | `rov.amps` | Medium. Scale *every* thruster by one factor; clipping one changes the direction (`CLAUDE.md`, stabilizer bug 3). Nudge the factor down while over, up while under |

Depth hold, heading hold and leveling are one idea on three sensors -- a sign
the sequence's center (309) is in the right place.

## What the sim needs before lesson 305

1. **Done 2026-11-06 -- pilot mode** (`games/rov_pilot.js`, verified; see
   `CLAUDE.md`, "rov_pilot.js"): MicroPython loaded once; the launcher line
   in `sim/pilot.py`; that lesson's `main.py` plus `sim.py`, `cube.py`,
   `triangle.py` in its filesystem; `pilot()` every 4th physics step; errors
   with the harness's frames removed, all thrusters off until fixed; the last
   six `print()` lines in a panel; `while True` refused before it runs;
   reload on save; `PilotAssist` with no `sim/` (Pages), and M switches.
2. **Done -- `sim/sim.py`** with `Pad` and `Rov`. `rov.thrust()` also
   rejects a thruster number that is not on this ROV (negative indexes would
   otherwise silently run the last one) and a power that is not a number.
3. **Done -- `sim/cube.py`, `sim/triangle.py`**, checked against each
   thruster's new `id` in `rov_profiles.js`. A lesson that imports the wrong
   ROV's file gets a warning, not an error.
4. **Done -- the accelerometer** (gravity only; no motion switch yet), and
   `depth`, `heading`, `amps`. Its signs follow the controller's tilt.
5. **Done 2026-11-06 -- profile changes.** Cube float at **10 cm** (6 was
   tried first), cube pitch/roll damping **3** (was 0.5), one **8 N heavy
   crab** (drawn bigger and darker). The target was the user's **last season:
   about 20-30 deg** of pitch with a heavy item; the user then chose less
   pitch on the cube (10 cm), with the triangle the tippy one. With depth
   held and no leveling the cube settles at 15.1 deg (16.3 on the grab), the
   triangle ~41. The cost of a dip is what actually happens (the claw camera
   loses the basket); **no crab slipping for now** (user: "let's wait").
   `CLAUDE.md`'s cube numbers are re-measured at the final settings.

   **Found on the way:** the built-in stabilizer, P plus an integral that
   only learned within 5 deg, held the heavy crab at 14.3 deg forever (6 cm
   float) -- the P term halved the dip and the steady error sat outside the
   integral's window. It now learns whenever the ROV has stopped turning, and
   levels the heavy crab in 5.6 s: the demo of where 309 is headed. And the
   damping guess decided whether students' P-only leveling works at all --
   see "PID is Part 4" under Decisions.
6. **Done -- keys**: R reset, 1 / 2 the ROV, M built-in pilot and back. In
   pilot mode the sim ignores every controller button.
7. **Done -- `serve.py` watches `sim/`, and `tools/lesson.py`** picks board
   and sim lessons (VS Code task "Lessons: choose one", the default build
   task, so Ctrl+Shift+B, as in Parts 1-2). A sim switch
   rewrites `sim/pilot.py` and an open sim reloads into it (verified); a board
   switch rewrites `board/code.py` -- which is still `import controller`, so
   the first switch replaces it with the lesson line -- and pushes it (not yet
   tried: no board lessons exist). The "Games: play in the browser" task now
   runs `serve.py` on port 8770 instead of `http.server` on 8765.
8. **Done -- the sim on a school laptop**: "a solid 60 fps" on one of the
   laptops the club will use (user, 2026-11-06).

`sim/L305_tank_drive/main.py` exists as pilot mode's test case: the given tank
example, sign trap included. It is not a finished lesson -- no try-these yet.

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
  against agility and current. With its old 20 cm float the cube could hold
  only 16 deg of tilt and burned 18.3 A doing it; at 10 cm, with the maker's
  thruster table, it holds the full 35 deg on 10.1 A (the triangle: 35 deg on
  2.0 A), and the heavy crab pitches it
  15 deg. `CLAUDE.md` has the table.
- The stabilizer tuning stories in `CLAUDE.md` (newtons not commands, lag as
  damping, scale don't clip, integral only near a still target) are the
  answer key for 309-311's hard cases.
- A keyboard HID with an "armed" switch was dropped in favor of gamepad-only;
  the "deliberate safe state before anything moves" habit is still worth
  teaching somewhere, since the ROV needs it.
