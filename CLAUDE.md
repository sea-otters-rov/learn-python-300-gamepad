# learn-python-300-gamepad

Part 3 of the Learning Python course for high school students in a MATE ROV
club: a Seeed XIAO RP2350 on a breadboard becomes a USB gamepad -- two analog
sticks, tilt from an IMU, buttons -- and drives browser games, building toward
ROV control. CircuitPython 10.3.1.

Parts 1-2 are a separate repo, `sea-otters-rov/led-panel-learn-python` (a
MatrixPortal M4 and a 64x32 LED panel). It was split off because Part 3 broke
three things that repo assumes: one board image, one firmware version, and one
kind of USB device. Findings there that carry over are repeated here, not
linked, so this file stands alone.

`README.md` covers setup, wiring and the daily workflow. This file is
orientation for working *on* the project.

## Layout

    board/      EXACT image of the XIAO's root -- see Invariants
    games/      browser games; published to GitHub Pages by .github/workflows
    sim/        students' Python for the ROV sim (pilot mode); NOT published --
                only tools/serve.py serves it
    spikes/     the experiments behind the numbers below; not board content
    tools/      setup, sync, verify, run-a-spike, console, serve (local web
                server, live reload), lesson (switch board or sim lesson)

No lessons are written yet, but **the sequence is agreed: `docs/lesson-plan-notes.md`**
holds it (L301-L312), with the concept table, every decision and why, the
`pilot()` API, and what the sim needs before the sim lessons. Read it before
writing a lesson. In short: four board lessons make the gamepad, then students
write the ROV's input-to-thruster mapping in Python **that runs inside the
sim** (MicroPython-WASM, edited in VS Code, live-reloaded by `tools/serve.py`),
in `sim/L3xx_*/` folders that do not exist yet.

`board/controller.py` is the working spike that
every game currently runs against; `board/code.py` imports it. It is built on
two course modules at the board root (like Part 1's `screen.py`, these are the
surface students use; `lib/` is for third-party code):

- **`gamepad.py`** -- `Gamepad` with axes `left_x`, `left_y`, `right_x`,
  `right_y`, `tilt_x`, `tilt_y` as **-1.0 .. 1.0**, and buttons as named
  constants numbered **from 0, exactly as the browser numbers them**
  (`gamepad.A` is `buttons[0]`). `set_button(name, pressed)` for the common
  case. Converting to the report's -127 .. 127 is its job alone.
- **`sticks.py`** -- `left, right = sticks.connect(i2c)`; each `Stick` reads
  `.x`, `.y` as -1.0 .. 1.0 (y up is -1, like the browser). The stick on A0/A1
  comes first. Measures each center at connect(), default `dead_zone` 0.06,
  `flip_x/y` (-1 for a stick mounted the other way round). It
  is the only code that knows about volts. Each `.x`/`.y` is a fresh ADS1115
  conversion (~2 ms), so read once per loop.

**Buttons were 1-based until 2026-10-18** (HID descriptors and Windows'
control panel count from 1, and that leaked into `gamepad.py`), so every
button number in Python was one off from the browser and the Controller check
page students debug with. Do not reintroduce a bare button number anywhere.

Verified end to end: `left_x = 0.5` arrives as 0.504 (64/127, the report's
resolution), `right_y = -0.25` as -0.252, `tilt_y = -1.0` as -1;
`gamepad.A` and `gamepad.RIGHT_CLICK` light "0 A" and "11 R click".
Rewriting `controller.py` onto these modules left it at 104 loops/s, the same
as the hand-rolled version.

## Canonical commands

Permission rules match the exact command string, so vary these and you buy the
user another approval prompt. Run from the repo root, one per call:

    .\.venv\Scripts\python.exe .\tools\verify_board.py
    .\.venv\Scripts\python.exe .\tools\run_on_board.py spikes\adc_speed.py
    & .\tools\sync.ps1
    & .\tools\sync.ps1 -Clean
    git add -A
    git commit --quiet -F .commitmsg

**Never `git add <paths>`** -- every path list is a new command string and
prompts every time. Stage everything; say in the message what it covers. Write
commit messages to `.commitmsg` (gitignored). Never prefix git with `cd` or
`git -C`. **Do not launch the sync through `powershell -File`** from here: it
prompts every time regardless of allow rules. `& .\tools\sync.ps1` is the same
script without the child process. (The VS Code tasks use `-File`; that is fine,
students click those.)

`verify_board.py` and `run_on_board.py` exit 0 ok, 1 traceback, 2 port busy,
3 no board. **On a 2, ask the user to close whatever holds the port** (usually
the Serial Monitor panel) and retry -- do not route around it.

## Hardware facts that change decisions

- **Every tool refuses any board but a XIAO RP2350**, by the `Board ID:` line
  in `boot_out.txt` (`tools/find_board.py`, `SUPPORTED`; and `$Supported` in
  `tools/sync.ps1`). A MatrixPortal from Parts 1-2 can be on the same laptop,
  and `sync.ps1 -Clean` aimed at it would wipe its lessons. Drive letters say
  nothing about which board is which.

  The Parts 1-2 repo's tools do NOT yet check the board type: with only the
  XIAO plugged in, its `sync.ps1 -Clean` would wipe this board. Use this repo's
  tools for the XIAO.

- **The firmware has `adafruit_bus_device` and `adafruit_pixelbuf` built in.**
  So `board/lib` must not contain them: a copy in `lib/` is loaded instead of
  the built-in one. circup puts `adafruit_bus_device` back as a dependency of
  every sensor library -- delete it after any circup run. The board this repo
  was built on still had a stale copy (and unused `adafruit_hid`,
  `adafruit_motor`, `adafruit_register`) from before; `sync.ps1 -Clean` removes
  them, along with anything else not in `board/`.

  Also built in and worth knowing: `keypad` (debounced buttons, in C),
  `usb_hid`, `usb_host`, `analogio`, `rainbowio`.

- **Pins, XIAO RP2350.** Only **A0-A2** (= D0-D2) are usable analog inputs:
  `board.A3` is `board.VOLTAGE_MONITOR`, the battery sense pin. I2C is D4/D5
  (`board.I2C()`). D8/D9/D10 are also SCK/MISO/MOSI, and D0/D1 are also A0/A1
  -- the breadboard uses all of them for buttons, so SPI and the RP2350's own
  ADC are unavailable (the course goes straight to the ADS1115 anyway).
  D11-D18 are pads on the underside, not breadboard pins. **Every breadboard
  pin is in use, final as of 2026-11-06** (and in the pin picture students
  get): D0 LB, D1 RB, D2 LT, D3 RT, D4/D5 I2C, D6 Start, D7 A, D8 B, D9 X,
  D10 Y. No stick clicks.

- **Wire buttons to GND with the internal pull-up** (`Pull.UP`, pressed reads
  `False`). RP2350 erratum E9: with the internal pull-DOWN on, a pin driven high
  can latch at ~2 V. A later stepping may fix it, but classroom boards are of
  unknown stepping, and pull-up is the convention anyway.

- **Power everything from 3V3, joysticks included.** The ADS1115 must never see
  an input above its own supply. Stick centers measured 1.657-1.677 V, which
  confirms 3.3 V.

- **The ADS1115 is the expensive read; the IMU is cheap.** Measured on the
  XIAO, interleaved rounds, ms per call (`spikes/adc_speed.py`):

        ADS library, 4 ch, 128 SPS (default)  @100 kHz   39.3
        ADS library, 4 ch, 860 SPS            @100 kHz   13.0
        ADS library, 4 ch, 860 SPS            @400 kHz    8.3
        ADS raw single-shot, 4 ch             @400 kHz    7.3   (floor ~4 x 1.16 ms)
        ADS raw, I2C transactions only x4     @400 kHz    1.5   (if conversions overlap)
        accelerometer only                    @400 kHz    0.41  (1.06 @100)
        accel + gyro                          @400 kHz    0.83  (2.13 @100)
        internal ADC (analogio), 4 reads                  0.053

  So: **`data_rate=860` and the bus at 400 kHz** are free 4.5x. Every chip on
  this bus handles 400 kHz, and the breadboard ran it cleanly with both
  breakouts' pull-ups in parallel. `imu.open_i2c()` uses `board.I2C()`, which
  is 100 kHz and takes no frequency -- `controller.py` opens its own
  `busio.I2C(..., frequency=400_000)` for that reason.

  `controller.py` runs ~104 loops/s: 4 stick channels + accelerometer + 6
  buttons. **Budget a controller against the USB report rate (~8 ms) and the
  game's frame (16.7 ms), not a display frame** -- this loop draws nothing.

- **Stick noise is negligible; the springs are the dead-zone problem.** At rest:
  under 2 mV of noise per channel, 0.13 of one stick count. Each center differs
  by up to 19 mV, so `controller.py` measures centers at startup. The 6% dead
  zone covers where a released stick happens to stop, which varies per release.
  Both live in `sticks.py`.

## The gamepad (boot.py)

- **boot.py runs only on a hard reset** -- the reset button, unplugging, or
  `microcontroller.reset()` from the REPL. Never on a save. A changed descriptor
  does nothing until then, and `gamepad.py` sending the new report length
  against the old descriptor raises until it is reset.
- **The gamepad is the ONLY HID device.** No keyboard, so no program can type
  into the editor it was saved from. That was the deciding argument for gamepad
  over keyboard; the other was analog axes, which tilt needs.
- **Chrome places each axis in a fixed slot by its usage name**: X 0, Y 1, Z 2,
  Rx 3, Ry 4, Rz 5. The first descriptor (Adafruit's example: X, Y, Z, Rz) put
  the right stick at slots 2 and **5**, with two dead slots between. Naming them
  X Y Z Rx Ry Rz gives six contiguous slots. Verified in Chrome: 6 axes, 16
  buttons, values scale linearly (64 -> 0.504, -100 -> -0.787).
- **Windows picked up a changed descriptor after a plain hard reset**, same
  VID/PID. The feared "Windows caches the old layout" did not happen.
- **The browser reports `mapping: ""`, never "standard"**, and that cannot be
  fixed from CircuitPython (it would mean impersonating an Xbox/PlayStation
  pad). The games read slots by number, so it does not matter.
- **A page sees no gamepad until a button is pressed after it loads.** Tilt and
  stick noise do not count. This is browser privacy policy, not a bug.

## Games

**Games stay dumb on purpose.** No dead zone, no smoothing, no auto-repeat in
any game. Calibration, sensitivity and dead zones live in the board's Python;
**mapping inputs to thrusters will live in the student's `pilot.py`, run by
the sim** (decided 2026-11-05, not built), so the board stays a plain gamepad
that an Xbox controller could replace. The marble creeping on a "level" board
is the lesson, not a bug to fix in JS.

**`games/pad.js` and `board/controller.py` are two halves of one contract.**
Change a slot in one, change the other. The slots:

    slot           gamepad.py                 wired to
    axes[0], [1]   left_x, left_y             ADS1115 A2, A3  (-1 left/up .. +1 right/down)
    axes[2], [3]   right_x, right_y           ADS1115 A0, A1
    axes[4], [5]   tilt_x, tilt_y             accelerometer: right edge down +1,
                                              far edge down -1
    buttons[0..3]  A, B, X, Y                 D7, D8, D9, D10
    buttons[4..7]  LB, RB, LT, RT             D0, D1, D2, D3
    buttons[9]     START                      D6
    buttons[10/11] LEFT_CLICK, RIGHT_CLICK    not wired
    buttons[12-15] DPAD_UP ... DPAD_RIGHT     not sent (tried, removed for clarity)

**The breadboard's mounting is set in one block of `controller.py`** ("How this
breadboard is built"), expected to be how students build theirs too: the stick
on A0/A1 is the RIGHT one (`right, left = sticks.connect(i2c)`), the left stick
is turned 180 degrees from it (`left.flip_x = left.flip_y = -1`), and the
SEN0140 is turned so its x and y are the breadboard's y and x
(`board_acceleration()`). "Level" is measured through the same function, so the
swap cannot drift out of step with the loop. A board built another way changes
only that block; each comment says what to change. After the 2026-11-06
rewrite (the same mapping, moved from minus signs and an `ay, ax, az` unpack in
two places) the user confirmed both sticks on a second, freshly flashed board;
**tilt direction is not yet re-checked**. That board runs 91 loops/s, not 104:
`spikes/loop_cost.py` puts four stick axes at 9.2 ms there (8.3 in the table
below) and `board_acceleration()` at +0.006 ms. `spikes/wiring_check.py`
diagnoses a silent I2C bus (pull-ups present? chips answer, either way round?).
On that board: lines pulled up, no chip answering, either way round -- which
points at the breakouts' GND; a wiring fix brought all five chips back.

In the ROV sim's built-in pilot, **B switches ROV, X switches camera, Y
switches pitch AND roll between following tilt and holding level by itself,
LB/RB close/open the claw, Start resets**. In pilot mode (planned) students
choose their own buttons for all of it, camera included. The keyboard
stands in for everything (see `pad.js`; X and Y keys are the X and Y buttons),
and **a held key overrides a connected gamepad** -- otherwise a teacher
demonstrating with a board plugged in finds the keyboard dead.

- **All Pages sites in the `sea-otters-rov` org share one origin**, so
  localStorage is shared across every game in every repo. Prefix every key
  with the game's name (`rov-sim-...`, `marble-maze-...`).
- **three.js comes from jsDelivr, pinned to 0.160.0**, via an import map. It
  needs internet; vendoring it into `games/lib` is the fix if classrooms are
  ever offline. It has not been downloaded -- ask before doing so.
- **The rov sim's numbers on an RTX 2070:** 1.3-1.9k triangles, 45-64 draw
  calls, and the physics costs 2.5-3.4 us per 240 Hz step (~0.014 ms per
  frame). Not yet measured on a school laptop, which is the number that
  matters -- press Q in the sim to step the drawing resolution.
- **`window.sim` in rov_sim.html is for testing**: `sim.fly(axes, seconds,
  buttons)` runs the whole sim on made-up inputs, and `sim.thrusters([...],
  seconds)` drives the thrusters directly, skipping the pilot assist. Use them
  rather than synthetic key events: a hidden browser pane throttles
  requestAnimationFrame -- or stops it outright -- so time-based tests through
  the real loop under-run, and the fps readout freezes.
- **marble_maze.html** checks nothing at load, but every level must be solvable:
  a hole filling a one-tile corridor is an invisible wall. Level 3 shipped with
  exactly that bug, caught by a BFS from S to G.

### The ROV sim's physics (since 2026-10-25)

Four files, so each can change alone (the fourth, `rov_pilot.js`, is pilot
mode -- see below):

- **`games/rov_profiles.js`** -- each ROV as numbers: mass, centers of mass and
  buoyancy, inertia, added mass, drag, and every thruster's position and
  direction. **Every number is a guess until the ROV is built**, and each says
  where it came from. Two profiles: `cube` (8 thrusters, each along one axis;
  6 cm between centers of buoyancy and mass since 2026-11-06, was 20) and
  `triangle` (3 vertical in the corners + 3 along the bottom edges; 5 cm).
  Both use the club's **APISQUEEN U3** thrusters at `VOLTS = 13` (they run
  12-14 V). The product page gives only "3Kg" max, 12-24 V, 12 A, 290 W,
  173 g -- so 3 kg is taken as forward at 24 V, scaled by volts^1.5 (between
  ideal volts^2 and the T200's measured ~volts^1.3), with reverse at 70%:
  **11.7 N forward, 8.2 N reverse at 13 V**, a third of a T200. Measuring one
  thruster on a luggage scale replaces the most important guess in the file.
- **`games/rov_physics.js`** -- `Vehicle` is a 6-DOF rigid body that only
  knows forces: thrusters, weight at the center of mass, buoyancy at the center
  of buoyancy, per-axis drag and added mass, thruster spin-up lag, impulse
  contacts at hull points. `PilotAssist` is the "flight computer": a
  pseudo-inverse mixer (thrust allocation) from six wanted pushes to N
  thrusters, a PD stabilizer for pitch/roll with the float's torque cancelled
  as feed-forward, a yaw-RATE controller, and "staying upright beats moving"
  when thrusters saturate. In pilot mode the student's Python replaces
  `PilotAssist`, so keep the two separate.
- **`rov_sim.html`** builds the 3D model from the profile. B switches profile
  (also `?profile=triangle`, and keys 1 / 2), V cycles forces (thrust arrows,
  then also weight and lift, then off), P hides the right-hand panels, LB/RB
  close/open the claw (keys "," and "."), R resets, and a panel shows each
  thruster's command and newtons.
- **`rov_pilot.js`** -- pilot mode (built 2026-11-06): the student's
  `pilot(pad, rov)` from `sim/<lesson>/main.py`, run by MicroPython-WASM
  1.27.0 (jsDelivr, pinned, loaded only when `sim/pilot.py` can be fetched --
  so never on Pages) every 4th physics step (`PILOT_EVERY`: 60/s in sim time).
  It replaces `PilotAssist`; M switches back. In pilot mode every controller
  button is the student's: the sim keeps only R, 1 / 2 and M. `sim/sim.py`
  holds the `Pad`/`Rov` classes students see; a hidden harness in
  `rov_pilot.js` fills them, so a call crosses into Python once. Each
  thruster's `id` in `rov_profiles.js` is its constant in `sim/cube.py` /
  `triangle.py`, checked on every load. Live reload: `serve.py`'s `/changes`.

  Verified 2026-11-06 through `sim.fly`: the L305 example drives 1.2 m
  backwards in 3 s with both sticks forward (the intended sign trap); a
  misspelled constant shows `File "L305_tank_drive/main.py", line 20, in pilot`
  and stops every thruster; `while True` is refused before it runs (a pilot()
  that never returns would freeze the page -- it runs on the page's thread);
  a wrong constant number names the right one; holding LB through Python
  grips a crab (1.5 A); the triangle with a cube lesson warns; 10 s of sim at
  rest costs 55 ms. The accelerometer reads (0, 0, 9.81) level, x +2.90 right
  side down 17 deg, y -2.90 nose down -- signed like the controller's tilt.
  **Gotchas:** a second `loadMicroPython()` in one page breaks the first; a
  returned tuple cannot be indexed from JS (results go back through a
  Float64Array); the harness must record which of cube/triangle the lesson
  imported BEFORE checking names, since the check imports both.

Verified 2026-10-25 with the U3 at 13 V, both profiles, through `sim.fly` /
`sim.thrusters` (the hand calculation is T * lever = B * (CoB - CoM) * sin
tilt). **Cube rows marked * re-measured 2026-11-06 with the 6 cm float and the
new integral rule**; the others are from before and should not have changed
(drag, thrust and mixing did not), except the mission, not re-run:

                                     cube                 triangle
    one corner thruster, no assist   * 27-29 deg rocking,  47.2 deg (hand 47.2)
                                     hand 27.9 (was 8.0)
    full forward / sideways          0.59 m/s             0.70 / 0.64 m/s
    full rise                        0.85 m/s             0.69 m/s
    turn                             60 deg/s             60 deg/s
    full tilt, nose down             * -35 deg in 1.9 s,  -35 deg in 2.6 s,
                                     0.2 over (was 16,    0.4 over
                                     the most it held)
    level + full tilt + forward      * 0.0 deg            within 1.0 deg
    hands off 20 s                   * still, level       still, level
    crab mission, all 5              completes (20 cm)    completes

**The triangle's vertical thrusters sit just OUTSIDE its corners** since
2026-11-05 (`CORNER_OUT`, 35.4 cm from center, 5 mm clear of the corner
posts). History, because each step was a real constraint:

    85% of the way out, inside   tube overlapped the edge bars by 2.3 cm, and
                                 its end caps shared a plane with the bars'
                                 faces -- z-fighting flicker
    55%, inside (the most that   fit, but the short lever lost torque: full
    fits -- corners narrow)      nose-down tilt only reached 29.9 of 35 deg
    123%, outside                full tilt again; one corner thruster alone
                                 now tips it 65 deg (the longer lever)

The claw moved 3 cm lower (`claw` y = -0.10) so its arm passes 3 cm under the
nose thruster -- touching, they would flicker the same way -- with a strut in
the drawing from the nose corner down to it. **Any two parts whose faces meet
exactly will flicker**; leave a gap.

**Stability and agility trade off, and the thruster decides where the line
falls.** With the old 20 cm float the cube could hold only ~16 deg of tilt:
its float's righting torque (up to 23.5 N m) beat four 11.7 N verticals. With
T200s it reached the full 35. The triangle's 5 cm lever lets it tilt fully --
and with T200s one corner thruster FLIPPED it (8.8 N m against 3.9), where a
U3 leaves it at 47 deg. **The cube's float moved to 6 cm on 2026-11-06**
(righting up to 7.1 N m) to match the club's real problem -- last season's
ROVs pitched 20-30 deg holding a heavy item -- so it now tilts fully and the
heavy crab pitches it (below).

**Three bugs found on the way, all worth knowing for any thruster code:**

1. The assist must work in NEWTONS and convert to a command last, stepping over
   the dead band and asking harder in reverse. Mixing straight to commands lost
   every small correction inside the 5% dead band (tilt barely moved) and made
   any move needing a thruster in reverse lopsided (the triangle spun at
   59 deg/s trying to go forward).
2. **Thruster spin-up lag acts as extra damping**: the stabilizer at speed 2 /
   damping 1 took 5.3 s to tilt, so it is tuned to 4 / 0.7 -- under-damped on
   paper, critically damped in practice.
3. **When the stabilizer asks for more than the thrusters have, scale it down
   as a whole; never clip thrusters one by one.** Clipping kept 11.7 N on the
   pushing-up side and 8.2 N on the pushing-down side, and the difference
   lifted the cube 1.4 m in 6 s at full tilt with nobody asking.

**Current draw is estimated too** (`Vehicle.current()`, shown under the
thruster panel with the peak since Start and the all-thrusters-full total).
Model: the page's 290 W / 12 A taken as full power at 24 V; power ~ thrust^1.5
(thrust ~ rpm^2, power ~ rpm^3), so with thrust ~ volts^1.5 full power goes as
volts^2.25 -- **5.6 A per thruster flat out at 13 V**, part power as (fraction
of full thrust)^1.5, the same in reverse. Plus `IDLE_CURRENT` 0.5 A for
everything with the thrusters stopped (the club's figure: two 4-in-1 ESCs and
an RP2350 idle very low) and `CLAW_HOLD_CURRENT` 1 A while the claw grips a
crab. Checked: one thruster at half thrust matched the hand calculation
exactly.

                                cube (* 6 cm)   triangle
    hands off                   * 0.5 A         0.5 A
    holding a crab, level       * 1.6 A         1.6 A
    holding the heavy crab      * 8.0 A         6.0 A (still levelling)
    full forward                11.7 A          9.7 A
    holding full tilt           * 9.1 A         3.4 A
    full tilt + full forward    * 19.5 A        16.6 A
    every thruster full + claw  46.4 A          35.2 A

**MATE requires a 15 A fuse**, so the readout turns yellow over 15 A and red
over 18 A (`CURRENT_YELLOW`, `CURRENT_RED` in rov_sim.html). Both designs can
draw two to three times that; nothing in the pilot assist limits current yet.
With the old 20 cm float the cube burned 18.3 A just HOLDING its 16 deg tilt
-- fighting its own float the whole time; at 6 cm it holds 35 deg on 9.1 A.
Stability costs current as well as agility.

**A held crab dips the nose, and the stabilizer's integral term levels it
again.** Normal crabs (0.5 N wet weight on the claw): cube 1.2 deg, level
within 0.5 in 1.3 s; triangle 3.9 deg, level in 2.7 s. **One crab is heavy:
8 N** (`HEAVY_CRAB_WET_WEIGHT`, drawn bigger and darker), because MATE tasks
have one and the club's ROVs pitched 20-30 deg with one. With depth held and
NO leveling -- a student's code before lesson 309 -- it pitches the cube
22.6 deg, swinging to 27.7 on the grab (hand 22.5; 1.8 deg for a normal
crab). The built-in pilot's level mode holds it to 14.0 deg at worst and is
level within 1 deg in 5.2 s. On the triangle the heavy crab's torque at level
(3.91 N m) equals the MOST its float can ever push back (3.92 N m, at 90
deg): unassisted it would roll onto its nose; the stabilizer catches it at
47 deg and levels it slowly (-4 deg after 12 s).

Without the integral term the triangle sat at 5.3 deg with a normal crab --
WORSE than its float's 3.6 unaided, because the stabilizer's spring is softer
than the float's. **The integral learns only a steady load**: target still
and the ROV turning slower than `integralBelowRate` (3 deg/s), capped at
`integralCap` (60%) of full pitch/roll push. Until 2026-11-06 the rule was
"within 5 deg of a still target", with a 30% cap: the heavy crab left the
cube's spring 14.3 deg short, outside 5 deg, so the integral never started
and the cube sat at 14.3 deg for good -- lesson 310's "dip that stays",
demonstrated by the sim's own stabilizer. Learning during a big deliberate
tilt is still excluded (the ROV is turning then); that once overshot the
triangle to 44 deg on the way to 35, and full tilt now overshoots 0.2-0.4.

**A thermostat-style "hold band" was tried and removed** (rest the thrusters
within 2 deg, kick on past it, to save current and make occasional kicks
visible). On the triangle it never rested: the springy float bounced it back
out of the band in a fraction of a second, and across 24 tunings the
stabilizer was still on 72-87% of the time with +-4 deg of wobble. Pulsing
suits a slow, heavily damped vehicle; this one is neither.

**Browsers cache the sim's modules.** A plain reload re-fetches
`rov_sim.html` but can keep a stale `rov_physics.js` or `rov_profiles.js` --
`python -m http.server` sends no cache rules, so Chrome guesses. One test run
here measured old code that way. After editing a module, hard-reload
(Ctrl+Shift+R), or check `sim.assist.fly.toString()` contains the change.
GitHub Pages caches for 10 minutes, so a just-pushed fix can look unfixed.
**`tools/serve.py` fixes this locally** (launch config `serve`,
`http://localhost:8770/`, the repo root): it sends `Cache-Control: no-store`,
pushes each saved file's path to pages on `/changes` for live reload, and
listens on both ::1 and 127.0.0.1 -- bound to IPv4 alone, Chrome's `localhost`
tried IPv6 first and every request took 310 ms instead of 5.

## Invariants

- **`board/` is an exact image of the board's root**, including `lib/` and
  `settings.toml`. Anything else lives outside it. That is what lets
  `sync.ps1 -Clean` mirror with robocopy `/PURGE`.
- **Stub version tracks firmware**: `circuitpython-stubs==10.3.1` in
  `requirements-dev.txt` and `$CpyVersion` in `tools/setup.ps1`. Bump together.
- **`board/settings.toml` is per board** (SEN0140 calibration) and gitignored.
- **Save = deploy.** `.vscode/settings.json` runs `tools/sync.py` on save;
  autosave is `onFocusChange` (afterDelay would push half-typed files, and also
  silently disables formatOnSave).
- **No UTF-8 BOM in board files.** CircuitPython reports a SyntaxError on line 1
  for one. PowerShell 5.1's `Set-Content -Encoding utf8` writes one -- that bit
  this project once, on `boot.py`. Both sync tools strip it.
- American spellings; f-strings; ruff format at 88 columns.

## SEN0140 drivers

`board/lib/imu.py`, `imu_calibration.py`, `itg3205.py`, `qmc5883.py` are copied
from `github.com/m5m1th/sen0140-circuitpython` 0.2.0. Fix bugs there, then copy
back. Chips on this board: ADXL345 0x53, ITG-3205 0x68, VCM5883L 0x0C, BMP280
0x77, plus the ADS1115 at **0x48** (ADDR to GND).
