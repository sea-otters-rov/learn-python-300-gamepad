// rov_profiles.js -- the ROVs the sim can fly, as numbers.
//
// Every number here is a GUESS until the real ROV is built and measured. Each
// one says where it came from, so it is clear which to replace first. The
// physics in rov_physics.js uses nothing else: change a profile and the ROV
// flies differently, with no other code to touch.
//
// Units are meters, kilograms, newtons, seconds and radians. Positions are in
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

// APISQUEEN U3: the maker's "thrust data at different voltages" table (from
// the club, 2026-11-07), full throttle. Thrust in kg, current in A.
//
//   volts   forward kg   A    reverse kg   A
const U3_TABLE = [
  [12, 0.9, 3, 0.9, 3],
  [14, 1.2, 3.5, 1.2, 3.5],
  [16, 1.5, 4, 1.5, 4],
  [18, 1.8, 5, 1.6, 5],
  [20, 2.1, 8, 1.9, 8],
  [22, 2.4, 9, 2.0, 9],
  [24, 2.7, 12, 2.4, 11],
  [26, 3.0, 14, 2.6, 13],
];
//
// Reverse pushes as hard as forward up to 16 V, so the club's 12-14 V gets
// the same thrust both ways. At 13 V, halfway between the 12 and 14 V rows:
// 1.05 kg = 10.3 N each way, 3.25 A. (Before the table this file guessed from
// the product page alone -- "3Kg", 12 A, 290 W -- and got 11.7 N forward, 70%
// of that in reverse, and 5.6 A: too much thrust forward, too little in
// reverse, and nearly twice the current.)
//
// Part throttle draws (fraction of full thrust)^1.5 of the full current: a
// propeller's thrust goes as its speed squared and its power as its speed
// cubed. That curve is still a guess -- the table only has full throttle.
//
// The table is "bollard pull": the thruster held still. Moving, water already
// flows into the propeller, so each blade bites less -- thrust AND current
// fall as the ROV speeds up, the most current being drawn from a standstill.
// Modeled as a straight line (thrustFor, current in rov_physics.js): all of
// the table at a standstill, none at ZERO_THRUST_SPEED of water flowing in.
// That speed is the propeller's pitch times its revolutions per second, and
// the U3's are not published: 4 m/s is a GUESS, typical of small ROV
// thrusters (3-6 m/s). The torque, and so the current, falls a little slower
// than the thrust -- reaching zero at about 1.2x the speed, as on published
// propeller curves. At the cube's top speed (~0.5 m/s) that is ~13% less
// thrust and ~10% less current than at a standstill.
const ZERO_THRUST_SPEED = 4.0; // m/s, a guess
const ZERO_CURRENT_SPEED = 1.2 * ZERO_THRUST_SPEED;
//
// STILL WORTH MEASURING: hang one thruster in a bucket from a luggage scale,
// with a clamp meter on its wire, at the ROV's real voltage, both ways, and
// at half throttle too. The maker's table is better than a guess but is not
// this thruster, this ESC, this water. And in the pool, the supply's current
// with the ROV tied to the wall at full forward, then at full speed: the
// second over the first is 1 - speed / ZERO_CURRENT_SPEED. Time the same run
// for the drag (below) -- measured apart, a wrong drag and a wrong
// ZERO_THRUST_SPEED can cancel and look right.
function apisqueenU3(volts) {
  // Straight lines between the table's rows; outside it, the nearest row.
  const v = Math.min(Math.max(volts, U3_TABLE[0][0]), U3_TABLE.at(-1)[0]);
  let i = 0;
  while (i < U3_TABLE.length - 2 && U3_TABLE[i + 1][0] < v) i++;
  const [v0, ...low] = U3_TABLE[i];
  const [v1, ...high] = U3_TABLE[i + 1];
  const [forwardKg, forwardAmps, reverseKg, reverseAmps] = low.map(
    (n, k) => n + ((high[k] - n) * (v - v0)) / (v1 - v0),
  );
  return {
    forward: forwardKg * g, // N at full throttle, command +1 -- 10.3 N at 13 V
    reverse: reverseKg * g, // N at full throttle, command -1 -- 10.3 N at 13 V
    deadBand: 0.05, // commands smaller than this make no thrust
    spinUp: 0.15, // s for the thrust to get most of the way to a new command
    volts,
    fullCurrent: forwardAmps, // A at full throttle forward -- 3.25 A at 13 V
    reverseCurrent: reverseAmps, // A at full throttle in reverse
    zeroThrustSpeed: ZERO_THRUST_SPEED, // m/s of inflow that leaves no thrust
    zeroCurrentSpeed: ZERO_CURRENT_SPEED, // ...and no current
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
  about: "Eight thrusters, each pushing straight along one axis.",
  shape: { kind: "cube", size: CUBE_SIZE },

  mass: CUBE_MASS,
  centerOfMass: [0, 0, 0], // given: the middle
  // given: neutral, so it neither sinks nor floats
  buoyancy: CUBE_MASS * g,
  // 10 cm above the center of mass -- assumed. Last season's ROVs pitched
  // about 20-30 deg nose-down holding a heavy item (user, 2026-11-06), which
  // points to a few cm here, not the 20 cm of a float "near the top" (used
  // until 2026-11-06): with 20 cm the cube barely noticed a crab. 6 cm was
  // tried next (heavy crab: 22.6 deg); 10 cm makes the heavy crab (8 N) pitch
  // it 15 deg -- still plain to see, while the triangle (5 cm) stays the tippy
  // one. Measure the real ROV and replace this.
  centerOfBuoyancy: [0, 0.1, 0],

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
  // Top speed forward with two 10.3 N thrusters: sqrt(20.6 / 60) ~ 0.6 m/s
  // (0.51 measured -- the linear term takes some, and so does the thrusters'
  // loss with water flowing in).
  drag: { linear: [4, 4, 4], quadratic: [60, 60, 60] },
  // Drag on turning about x, y, z, in the same form (N m per rad/s).
  //
  // Pitch and roll (x, z) linear: 3, a guess -- it decides how the ROV rocks
  // back after it is tipped. At 0.5 (until 2026-11-06) the cube rocked for
  // ~8 s, and a student's P-only leveler at gain 0.3 never settled at any
  // float height; at 3 the cube, tipped 15 deg and let go, settles in ~1 s
  // with no swing back, and P-only settles in ~1.5 s. MEASURE IT: tip the real
  // ROV ~15 deg in the pool, let go, and count the swings back and forth.
  turnDrag: { linear: [3, 0.5, 3], quadratic: [3, 3, 3] },

  thruster: THRUSTER,
  idleCurrent: IDLE_CURRENT,
  clawHoldCurrent: CLAW_HOLD_CURRENT,
  // A positive command pushes the ROV along `direction`. `id` is the
  // thruster's name in the students' sim/cube.py, which must hold the same
  // number as its place here -- the sim checks on every load.
  thrusters: [
    // four vertical, one near each corner of the middle of the cube
    { name: "up FL", id: "UP_FRONT_LEFT", position: [-0.2, 0, -0.2], direction: [0, 1, 0] },
    { name: "up FR", id: "UP_FRONT_RIGHT", position: [0.2, 0, -0.2], direction: [0, 1, 0] },
    { name: "up BL", id: "UP_BACK_LEFT", position: [-0.2, 0, 0.2], direction: [0, 1, 0] },
    { name: "up BR", id: "UP_BACK_RIGHT", position: [0.2, 0, 0.2], direction: [0, 1, 0] },
    // two forward, on the left and right faces -- pushing unevenly turns it
    { name: "fwd L", id: "FORWARD_LEFT", position: [-h, 0, 0], direction: [0, 0, -1] },
    { name: "fwd R", id: "FORWARD_RIGHT", position: [h, 0, 0], direction: [0, 0, -1] },
    // two sideways, on the front and back faces -- these can turn it too
    { name: "side F", id: "SIDE_FRONT", position: [0, 0, -h], direction: [1, 0, 0] },
    { name: "side B", id: "SIDE_BACK", position: [0, 0, h], direction: [1, 0, 0] },
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
// Where the vertical thrusters sit, as a fraction of center-to-corner: just
// OUTSIDE each corner, beyond the frame's corner post. The tube's edge must
// clear the post by its radius plus 2 cm for half a bar and a gap, so
// 1 + (0.045 + 0.02) / R -- about 1.23, 35 cm from the center.
//
// Inside the corners was tried first: corners narrow, so a tube only fits
// 55% of the way out, and that short lever left the triangle unable to reach
// a full nose-down tilt (29.9 of 35 deg). Before that, 85% overlapped the
// frame bars and flickered.
const CORNER_OUT = 1 + (THRUSTER.radius + 0.02) / R;

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
  // `id`: the thruster's name in sim/triangle.py, checked like the cube's
  thrusters: [
    // vertical, one just outside each corner (CORNER_OUT)
    ...[
      ["up nose", "UP_NOSE", nose],
      ["up rear R", "UP_REAR_RIGHT", rearRight],
      ["up rear L", "UP_REAR_LEFT", rearLeft],
    ].map(([name, id, [x, z]]) => ({
      name,
      id,
      position: [x * CORNER_OUT, 0, z * CORNER_OUT],
      direction: [0, 1, 0],
    })),
    // horizontal, on the bottom outside edge, each pushing along its edge
    edgeThruster("edge R", "EDGE_RIGHT", nose, rearRight),
    edgeThruster("edge back", "EDGE_BACK", rearRight, rearLeft),
    edgeThruster("edge L", "EDGE_LEFT", rearLeft, nose),
  ],

  // under the nose, 20 cm ahead -- and 5 cm below the frame, so the claw's
  // arm passes clear under the nose thruster (just touching, they flickered)
  claw: [0, -THICK / 2 - 0.05, -R - 0.2],
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
function edgeThruster(name, id, a, b) {
  const middle = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const out = Math.hypot(middle[0], middle[1]);
  const outward = [middle[0] / out, middle[1] / out];
  const along = [b[0] - a[0], b[1] - a[1]];
  const length = Math.hypot(along[0], along[1]);
  const MOUNT_OUT = 0.05; // m outside the edge -- assumed thruster radius
  return {
    name,
    id,
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
