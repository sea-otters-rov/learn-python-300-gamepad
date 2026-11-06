// rov_profiles.js -- the ROVs the sim can fly, as numbers.
//
// Every number here is a GUESS until the real ROV is built and measured. Each
// one says where it came from, so it is clear which to replace first. The
// physics in rov_physics.js uses nothing else: change a profile and the ROV
// flies differently, with no other code to touch.
//
// Units are metres, kilograms, newtons, seconds and radians. Positions are in
// the ROV's own frame, measured from the CENTER OF ITS SHAPE:
//
//     x  right        y  up        z  backwards  (so forward is -z)
//
// That matches the 3D library the sim uses. "Forward" being -z is the one
// surprise; every forward-facing thing below has a negative z.
//
// Things assumed for BOTH profiles, because nothing else was known yet:
//
//   - APISQUEEN U3 thrusters (the club's), run at VOLTS below -- see
//     apisqueenU3() for how much of that is a guess. Thrust is taken as
//     proportional to the command past a small dead band.
//   - Fresh water (a pool), no current, no tether pulling on the ROV.
//   - Drag and "added mass" are rough estimates for an open frame. They are
//     the least certain numbers here, and the easiest to MEASURE once the ROV
//     exists: time it across the pool at full power -- at top speed, thrust
//     equals drag, so drag = thrust / speed^2.

const g = 9.81; // m/s^2

const VOLTS = 13; // the club runs the thrusters at 12-14 V

// APISQUEEN U3, sold as "6S 24V ... 3kg thrust". Its product page gives
// 3-6S (12-24 V), 12 A, 290 W, "Maximum thrust: 3Kg", 173 g -- and nothing
// else: no thrust curve, no reverse figure, nothing below 24 V. So:
//
//   - "3Kg" is taken to be at 24 V, forward.
//   - Thrust at lower voltage: a propeller's thrust goes as its speed squared
//     and a motor's speed roughly as its voltage, so ideally thrust ~ volts^2.
//     Real motors under load fall short of that -- Blue Robotics' measured T200
//     curve behaves more like volts^1.3. Assumed in between: volts^1.5.
//     At 13 V that is (13/24)^1.5 * 3 kg = 1.2 kg, about 12 N.
//   - Reverse: these come as CW and CCW, so the propellers are shaped for one
//     direction and will push less backwards. Assumed 70%. Reverse at all
//     needs a bidirectional ESC.
//
// THE NUMBER TO MEASURE FIRST: hang one thruster in a bucket from a luggage
// scale and run it at full, both ways, at the ROV's real voltage. Put the two
// readings (in kg, times 9.81) into `forward` and `reverse` below and delete
// the guessing.
//
// CURRENT, also estimated -- the page's only electrical numbers are "12A" and
// "290W", taken as full power at 24 V. A propeller's power grows faster than
// its thrust: power ~ thrust^1.5 (from thrust ~ rpm^2 and power ~ rpm^3). With
// thrust ~ volts^1.5 above, full power goes as volts^2.25: at 13 V that is
// 290 W * (13/24)^2.25 = 73 W, so 5.6 A per thruster flat out. Part power
// draws (fraction of full thrust)^1.5 of that, backwards as well as forwards
// -- the propeller spins as fast either way; it just pushes less in reverse.
// To check it: put a clamp meter (or the supply's own meter) on one thruster
// during the luggage-scale test.
function apisqueenU3(volts) {
  const RATED_VOLTS = 24;
  const RATED_THRUST = 3 * g; // N, "3Kg"
  const RATED_POWER = 290; // W, "290W"
  const forward = RATED_THRUST * (volts / RATED_VOLTS) ** 1.5;
  const fullPower = RATED_POWER * (volts / RATED_VOLTS) ** 2.25;
  return {
    forward, // N at full power, command +1 -- 11.7 N at 13 V
    reverse: forward * 0.7, // N at full power, command -1
    deadBand: 0.05, // commands smaller than this make no thrust
    spinUp: 0.15, // s for the thrust to get most of the way to a new command
    volts,
    fullCurrent: fullPower / volts, // A at full power -- 5.6 A at 13 V
    // The club drives them from two 4-in-1 ESCs, whose idle draw is tiny and
    // is counted in IDLE_CURRENT below rather than per thruster.
    perThrusterIdle: 0, // A
    // Its size, for drawing it and for bumping into things. The page lists
    // "108mm*112mm" without saying which is which; drawn as a 9 cm wide,
    // 10 cm long tube.
    radius: 0.045, // m
    length: 0.1, // m
  };
}

// Everything drawn with every thruster stopped: the two 4-in-1 ESCs at idle,
// the RP2350 controller, camera and the rest. Assumed by the club, 2026-10-25.
// A multimeter on the supply with the thrusters stopped gives the real number.
const IDLE_CURRENT = 0.5; // A

// The claw's servo holding a crab -- it keeps pushing to stay closed around
// something. Closed on nothing, it reaches its position and draws ~nothing.
const CLAW_HOLD_CURRENT = 1.0; // A

const THRUSTER = apisqueenU3(VOLTS);

// ---------------------------------------------------------------------------
// Profile 1: the cube. Everything lines up with an axis, so the mixing is easy
// to work out by hand: each thruster pushes straight along x, y or z.
// ---------------------------------------------------------------------------

const CUBE_SIZE = 0.5; // m along every edge
const CUBE_MASS = 12; // kg -- assumed; typical of a small MATE ROV
const h = CUBE_SIZE / 2;

const cube = {
  name: "Cube",
  about: "Eight thrusters, each pushing straight along one axis. Very stable.",
  shape: { kind: "cube", size: CUBE_SIZE },

  mass: CUBE_MASS,
  centerOfMass: [0, 0, 0], // given: the middle
  // given: neutral, so it neither sinks nor floats
  buoyancy: CUBE_MASS * g,
  // given: "near the top" -- assumed 5 cm below the top face. The 20 cm between
  // this and the center of mass is what makes the cube hard to tip over.
  centerOfBuoyancy: [0, h - 0.05, 0],

  // How hard it is to start it spinning about x, y, z (kg m^2). Assumed: a
  // solid 12 kg cube, m * size^2 / 6. An open frame with heavy corners would
  // be a little higher.
  inertia: [0.5, 0.5, 0.5],

  // Water that moves with the ROV makes it act heavier: 0.5 means "50% more".
  // Assumed for an open frame. The same idea applies to turning.
  addedMass: [0.5, 0.5, 0.5],
  addedInertia: [0.5, 0.5, 0.5],

  // Drag along x, y, z: force = linear * speed + quadratic * speed^2.
  // Quadratic assumed from 1/2 * water density * Cd * area, with an open frame
  // blocking about half of each 0.25 m^2 face (Cd * area ~ 0.12 m^2) -> 60.
  // Top speed forward with two 11.7 N thrusters: sqrt(23.4 / 60) ~ 0.6 m/s.
  drag: { linear: [4, 4, 4], quadratic: [60, 60, 60] },
  // Drag on turning about x, y, z, in the same form (N m per rad/s).
  turnDrag: { linear: [0.5, 0.5, 0.5], quadratic: [3, 3, 3] },

  thruster: THRUSTER,
  idleCurrent: IDLE_CURRENT,
  clawHoldCurrent: CLAW_HOLD_CURRENT,
  // A positive command pushes the ROV along `direction`.
  thrusters: [
    // four vertical, one near each corner of the middle of the cube
    { name: "up FL", position: [-0.2, 0, -0.2], direction: [0, 1, 0] },
    { name: "up FR", position: [0.2, 0, -0.2], direction: [0, 1, 0] },
    { name: "up BL", position: [-0.2, 0, 0.2], direction: [0, 1, 0] },
    { name: "up BR", position: [0.2, 0, 0.2], direction: [0, 1, 0] },
    // two forward, on the left and right faces -- pushing unevenly turns it
    { name: "fwd L", position: [-h, 0, 0], direction: [0, 0, -1] },
    { name: "fwd R", position: [h, 0, 0], direction: [0, 0, -1] },
    // two sideways, on the front and back faces -- these can turn it too
    { name: "side F", position: [0, 0, -h], direction: [1, 0, 0] },
    { name: "side B", position: [0, 0, h], direction: [1, 0, 0] },
  ],

  claw: [0, -h + 0.05, -h - 0.2], // where the claw closes: low, 20 cm ahead
  camera: [0, 0, -h + 0.02], // just inside the front face, looking forward
  // Points that can touch the floor, walls and basket: the eight corners.
  hull: corners([-h, h], [-h, h], [-h, h]),
};

// ---------------------------------------------------------------------------
// Profile 2: the triangle. Three vertical thrusters in the corners, and three
// horizontal ones angled along the edges -- three thrusters do the work of
// four, but every move needs all three working together.
// ---------------------------------------------------------------------------

const EDGE = 0.5; // m, each side of the triangle
const THICK = 0.1; // m, top to bottom
const TRIANGLE_MASS = 8; // kg -- assumed
const R = EDGE / Math.sqrt(3); // center to corner, 0.289 m
const r = EDGE / (2 * Math.sqrt(3)); // center to the middle of an edge, 0.144 m

// The corners, as seen from above, with the nose corner pointing forward
// (assumed: a pointed end makes a natural front, and a place for the claw).
const nose = [0, -R];
const rearRight = [EDGE / 2, r];
const rearLeft = [-EDGE / 2, r];

const triangle = {
  name: "Triangle",
  about: "Six thrusters in threes. Agile, and much easier to tip.",
  shape: { kind: "triangle", edge: EDGE, height: THICK },

  mass: TRIANGLE_MASS,
  // given: both in the middle, CoB 2.5 cm below the top, CoM 2.5 cm above the
  // bottom -- 5 cm apart, a quarter of the cube's 20 cm. Expect it to tip
  // easily and need its stabilizer.
  centerOfMass: [0, -THICK / 2 + 0.025, 0],
  buoyancy: TRIANGLE_MASS * g, // assumed neutral, like the cube
  centerOfBuoyancy: [0, THICK / 2 - 0.025, 0],

  // Assumed: a solid triangular slab. Turning flat (y) is m * edge^2 / 12;
  // tipping (x, z) is m * edge^2 / 24 + m * thickness^2 / 12.
  inertia: [0.09, 0.17, 0.09],
  // A flat plate drags a lot of water with it when it moves up and down, and
  // little when it slides edge-on. Assumed.
  addedMass: [0.3, 1.0, 0.3],
  addedInertia: [0.8, 0.3, 0.8],

  // Edge-on it is only 0.5 x 0.1 m (Cd * area ~ 0.05 -> 25); face-on it is a
  // 0.11 m^2 plate (Cd ~ 1.2 -> 65).
  drag: { linear: [3, 6, 3], quadratic: [25, 65, 25] },
  turnDrag: { linear: [0.3, 0.3, 0.3], quadratic: [1.0, 0.6, 1.0] },

  thruster: THRUSTER,
  idleCurrent: IDLE_CURRENT,
  clawHoldCurrent: CLAW_HOLD_CURRENT,
  thrusters: [
    // vertical, one in each corner (assumed 85% of the way out, so they fit)
    ...[
      ["up nose", nose],
      ["up rear R", rearRight],
      ["up rear L", rearLeft],
    ].map(([name, [x, z]]) => ({
      name,
      position: [x * 0.85, 0, z * 0.85],
      direction: [0, 1, 0],
    })),
    // horizontal, on the bottom outside edge, each pushing along its edge
    edgeThruster("edge R", nose, rearRight),
    edgeThruster("edge back", rearRight, rearLeft),
    edgeThruster("edge L", rearLeft, nose),
  ],

  claw: [0, -THICK / 2 - 0.02, -R - 0.2], // under the nose, 20 cm ahead
  camera: [0, 0.02, -R + 0.06], // just behind the nose
  hull: [nose, rearRight, rearLeft].flatMap(([x, z]) => [
    [x, THICK / 2, z],
    [x, -THICK / 2, z],
  ]),
};

// A horizontal thruster mounted just outside the middle of the edge from
// corner a to corner b, low on the frame, pushing in the a -> b direction.
// Going a -> b around all three edges makes every one push the same way
// round, so all three at +1 spins the ROV on the spot.
function edgeThruster(name, a, b) {
  const middle = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const out = Math.hypot(middle[0], middle[1]);
  const outward = [middle[0] / out, middle[1] / out];
  const along = [b[0] - a[0], b[1] - a[1]];
  const length = Math.hypot(along[0], along[1]);
  const MOUNT_OUT = 0.05; // m outside the edge -- assumed thruster radius
  return {
    name,
    position: [
      middle[0] + outward[0] * MOUNT_OUT,
      -THICK / 2,
      middle[1] + outward[1] * MOUNT_OUT,
    ],
    direction: [along[0] / length, 0, along[1] / length],
  };
}

function corners(xs, ys, zs) {
  const points = [];
  for (const x of xs) for (const y of ys) for (const z of zs) points.push([x, y, z]);
  return points;
}

export const PROFILES = { cube, triangle };
export const GRAVITY = g;
