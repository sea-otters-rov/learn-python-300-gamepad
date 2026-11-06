// rov_physics.js -- how a ROV moves, from the numbers in rov_profiles.js.
//
// Two separate jobs, deliberately in two classes:
//
//   Vehicle      the physics. It only knows forces: thrusters, weight,
//                buoyancy, drag. Tell it how hard each thruster pushes and it
//                works out what the ROV does -- including tipping over when
//                the pushes are uneven. It never reads a joystick.
//
//   PilotAssist  the "flight computer". It turns what the pilot wants (go
//                forward, turn, hold this angle) into a command for every
//                thruster. On a real ROV this is software running on board,
//                and it is the part the student's Python could one day take
//                over.
//
// Frames: "body" means the ROV's own axes (x right, y up, z back, from the
// profile); "world" means the pool's. A quaternion (`attitude`) turns one into
// the other.

import * as THREE from "three";
import { GRAVITY } from "./rov_profiles.js";

const vec = ([x, y, z]) => new THREE.Vector3(x, y, z);

// ===========================================================================
// Vehicle
// ===========================================================================

export class Vehicle {
  constructor(profile) {
    this.profile = profile;
    const centerOfMass = vec(profile.centerOfMass);
    // Everything is measured from the center of mass from here on: that is
    // the point a push through which moves the ROV without turning it.
    const fromCenterOfMass = (p) => vec(p).sub(centerOfMass);

    this.shapeOffset = centerOfMass.clone().negate(); // shape center, from CoM
    this.buoyancyOffset = fromCenterOfMass(profile.centerOfBuoyancy);
    this.clawOffset = fromCenterOfMass(profile.claw);
    this.cameraOffset = fromCenterOfMass(profile.camera);
    this.thrusterModel = profile.thruster;

    // Points that can touch the floor, walls and basket: the frame's corners,
    // the claw (its tip, and the bottom of its jaws), and the outside of every
    // thruster -- they stick out past the frame, and without them the
    // triangle's edge thrusters sank 4.5 cm into the floor.
    this.hull = profile.hull.map(fromCenterOfMass);
    this.hull.push(this.clawOffset, this.clawOffset.clone().add(new THREE.Vector3(0, -0.02, 0)));
    const { radius, length } = profile.thruster;
    for (const t of profile.thrusters) {
      const middle = fromCenterOfMass(t.position);
      const along = vec(t.direction).normalize();
      const across = new THREE.Vector3(0, 1, 0).cross(along);
      if (across.lengthSq() < 1e-6) across.set(1, 0, 0); // a vertical thruster
      across.normalize();
      const across2 = new THREE.Vector3().crossVectors(along, across);
      // eight points round the rim at each end: tipped diagonally, a tube's
      // lowest point is an end's rim, between any fewer points (17 mm deep
      // with only the four sides of its middle)
      for (const end of [length / 2, -length / 2]) {
        for (let k = 0; k < 8; k++) {
          const angle = (k * Math.PI) / 4;
          this.hull.push(
            middle
              .clone()
              .addScaledVector(along, end)
              .addScaledVector(across, radius * Math.cos(angle))
              .addScaledVector(across2, radius * Math.sin(angle)),
          );
        }
      }
    }
    this.thrusters = profile.thrusters.map((t) => ({
      name: t.name,
      offset: fromCenterOfMass(t.position),
      direction: vec(t.direction).normalize(),
      command: 0, // what it was told, -1 .. 1
      thrust: 0, // what it is doing, in newtons (lags the command)
      spin: 0, // propeller speed as a fraction of full, -1 .. 1
    }));

    this.weight = profile.mass * GRAVITY;
    this.buoyancy = profile.buoyancy;
    this.mass = profile.addedMass.map((a) => profile.mass * (1 + a));
    this.inertia = profile.inertia.map((i, k) => i * (1 + profile.addedInertia[k]));

    this.position = new THREE.Vector3(); // of the center of mass, world
    this.velocity = new THREE.Vector3(); // world, m/s
    this.attitude = new THREE.Quaternion(); // body -> world
    this.spinRate = new THREE.Vector3(); // body, rad/s about x, y, z
    this.payload = null; // { offset (body, from CoM), wetWeight (N) } or null
    this.clawCurrent = 0; // A the claw draws right now (set by whoever works it)

    // scratch vectors, reused every step so nothing is allocated in the loop
    this._force = new THREE.Vector3();
    this._torque = new THREE.Vector3();
    this._up = new THREE.Vector3();
    this._push = new THREE.Vector3();
    this._lever = new THREE.Vector3();
    this._water = new THREE.Vector3();
    this._turn = new THREE.Quaternion();
    this._lift = new THREE.Vector3(); // buoyancyTorque's own, so it can be
    this._liftTurn = new THREE.Quaternion(); // called mid-step safely
    this._inverse = new THREE.Quaternion();
    this._euler = new THREE.Euler(0, 0, 0, "YXZ");
  }

  place(position, heading) {
    this.position.copy(position);
    this.velocity.set(0, 0, 0);
    this.attitude.setFromAxisAngle(new THREE.Vector3(0, 1, 0), heading);
    this.spinRate.set(0, 0, 0);
    for (const t of this.thrusters) t.command = t.thrust = t.spin = 0;
    this.payload = null;
    this.clawCurrent = 0;
  }

  // heading (turning left is positive), pitch (nose up is positive) and roll
  // (right side up is positive), in radians
  angles() {
    this._euler.setFromQuaternion(this.attitude, "YXZ");
    return { heading: this._euler.y, pitch: this._euler.x, roll: this._euler.z };
  }

  // a point given in body coordinates from the CoM, in the world
  toWorld(offset, into = new THREE.Vector3()) {
    return into.copy(offset).applyQuaternion(this.attitude).add(this.position);
  }

  // The torque buoyancy is making right now, in body axes. The pilot assist
  // uses it to cancel the float's pull when it holds the ROV at an angle.
  buoyancyTorque(into = new THREE.Vector3()) {
    const lift = this._lift.set(0, this.buoyancy, 0);
    lift.applyQuaternion(this._liftTurn.copy(this.attitude).invert());
    return into.crossVectors(this.buoyancyOffset, lift);
  }
  // Amps the whole ROV is drawing now: idle electronics, the claw if it is
  // gripping something, and each thruster by how fast its propeller is
  // actually spinning (see apisqueenU3 for the model).
  current() {
    const m = this.thrusterModel;
    let amps = this.profile.idleCurrent + this.clawCurrent;
    for (const t of this.thrusters) {
      const size = Math.abs(t.spin);
      const fraction = size < m.deadBand ? 0 : (size - m.deadBand) / (1 - m.deadBand);
      amps += m.perThrusterIdle + m.fullCurrent * fraction ** 1.5;
    }
    return amps;
  }

  // ...and with every thruster flat out while holding a crab: the most it
  // could ever draw, to compare with the fuse
  mostCurrent() {
    const m = this.thrusterModel;
    const thrusters = this.thrusters.length * (m.perThrusterIdle + m.fullCurrent);
    return this.profile.idleCurrent + this.profile.clawHoldCurrent + thrusters;
  }

  thrustFor(spin) {
    // A propeller makes no useful thrust inside its dead band, and less going
    // backwards than forwards.
    const m = this.thrusterModel;
    const size = Math.abs(spin);
    if (size < m.deadBand) return 0;
    const fraction = (size - m.deadBand) / (1 - m.deadBand);
    return spin > 0 ? fraction * m.forward : -fraction * m.reverse;
  }

  step(dt, current) {
    const p = this.profile;
    const force = this._force.set(0, 0, 0); // body
    const torque = this._torque.set(0, 0, 0); // body

    // Thrusters: each pushes along its own direction, from where it sits, so
    // one that is not lined up with the center of mass also turns the ROV.
    const settle = 1 - Math.exp(-dt / this.thrusterModel.spinUp);
    for (const t of this.thrusters) {
      t.spin += (THREE.MathUtils.clamp(t.command, -1, 1) - t.spin) * settle;
      t.thrust = this.thrustFor(t.spin);
      const push = this._push.copy(t.direction).multiplyScalar(t.thrust);
      force.add(push);
      torque.add(this._lever.crossVectors(t.offset, push));
    }

    // Weight pulls down at the center of mass, so it never turns the ROV.
    // Buoyancy pushes up at the center of buoyancy -- when that is above the
    // center of mass, any tilt makes a torque that turns the ROV back upright.
    this._inverse.copy(this.attitude).invert();
    const up = this._up.set(0, 1, 0).applyQuaternion(this._inverse); // world up, in body axes
    force.addScaledVector(up, this.buoyancy - this.weight);
    torque.add(this.buoyancyTorque(this._lever));

    if (this.payload) {
      const sink = this._push.copy(up).multiplyScalar(-this.payload.wetWeight);
      force.add(sink);
      torque.add(this._lever.crossVectors(this.payload.offset, sink));
    }

    // Drag acts on speed THROUGH the water, in the ROV's own axes, because a
    // frame is a different shape seen from the front, side and top.
    const water = this._water.subVectors(this.velocity, current).applyQuaternion(this._inverse);
    for (const [axis, k] of [["x", 0], ["y", 1], ["z", 2]]) {
      const v = water[axis];
      force[axis] -= p.drag.linear[k] * v + p.drag.quadratic[k] * v * Math.abs(v);
      const w = this.spinRate[axis];
      torque[axis] -= p.turnDrag.linear[k] * w + p.turnDrag.quadratic[k] * w * Math.abs(w);
    }

    // Accelerate. Each body axis has its own effective mass (added mass).
    force.set(force.x / this.mass[0], force.y / this.mass[1], force.z / this.mass[2]);
    this.velocity.addScaledVector(force.applyQuaternion(this.attitude), dt);
    this.position.addScaledVector(this.velocity, dt);

    // Turn. The cross term is what makes a spinning object wobble; with
    // nearly equal inertias it is small, but it is real physics.
    const w = this.spinRate;
    const I = this.inertia;
    const gyro = this._lever.set(
      (I[2] - I[1]) * w.y * w.z,
      (I[0] - I[2]) * w.z * w.x,
      (I[1] - I[0]) * w.x * w.y,
    );
    w.x += ((torque.x - gyro.x) / I[0]) * dt;
    w.y += ((torque.y - gyro.y) / I[1]) * dt;
    w.z += ((torque.z - gyro.z) / I[2]) * dt;
    const angle = w.length() * dt;
    if (angle > 0) {
      this._turn.setFromAxisAngle(this._push.copy(w).normalize(), angle);
      this.attitude.multiply(this._turn).normalize();
    }
  }

  // Push a point of the ROV out of something solid, and stop it moving
  // further in -- an impulse at that point, so hitting the floor with one
  // corner tips the ROV instead of stopping it dead.
  contact(offset, normal, depth) {
    this.position.addScaledVector(normal, depth);
    this._inverse.copy(this.attitude).invert();
    const n = this._up.copy(normal).applyQuaternion(this._inverse); // body
    const pointVelocity = this._water
      .copy(this.velocity)
      .applyQuaternion(this._inverse)
      .add(this._push.crossVectors(this.spinRate, offset)); // body
    const into = pointVelocity.dot(n);
    if (into >= 0) return;
    const leverN = this._lever.crossVectors(offset, n);
    const m = this.mass;
    const I = this.inertia;
    const give =
      (n.x * n.x) / m[0] + (n.y * n.y) / m[1] + (n.z * n.z) / m[2] +
      (leverN.x * leverN.x) / I[0] + (leverN.y * leverN.y) / I[1] + (leverN.z * leverN.z) / I[2];
    const j = -into / give;
    const dv = this._push.set((n.x * j) / m[0], (n.y * j) / m[1], (n.z * j) / m[2]);
    this.velocity.add(dv.applyQuaternion(this.attitude));
    this.spinRate.x += (leverN.x * j) / I[0];
    this.spinRate.y += (leverN.y * j) / I[1];
    this.spinRate.z += (leverN.z * j) / I[2];
    // a little scraping friction along whatever it touched
    this.velocity.multiplyScalar(0.995);
  }
}

// ===========================================================================
// PilotAssist: wanting -> thruster commands
// ===========================================================================

// The six things a ROV can be pushed to do, in the order the mixer uses them:
// force along body x, y, z, then torque about body x, y, z.
const SURGE = 2; // force along z (negative is forward)
const SWAY = 0;
const HEAVE = 1;
const PITCH = 3; // torque about x
const YAW = 4; // torque about y
const ROLL = 5; // torque about z

export class PilotAssist {
  constructor(vehicle, settings) {
    this.vehicle = vehicle;
    this.settings = settings;
    const m = vehicle.thrusterModel;
    this.most = m.forward; // N one thruster can push forwards
    this.leastReverse = -m.reverse; // N backwards: propellers are weaker that way
    this.mix = mixingMatrix(vehicle.thrusters);
    // The most push (N, or N m for turning) the thrusters can make on each
    // axis alone, in each direction -- backwards can be less, because some
    // thrusters then have to run in reverse. A full stick asks for exactly that.
    this.fullStick = [0, 1, 2, 3, 4, 5].map((k) => ({
      up: this.reach(k, 1),
      down: this.reach(k, -1),
    }));
    this._buoyancy = new THREE.Vector3();
    this.reset();
  }

  reset() {
    this.target = { pitch: 0, roll: 0 };
    // Error added up over time (radians x seconds): the integral term. It
    // learns the steady push a constant load needs -- a crab on the claw.
    this.integral = { pitch: 0, roll: 0 };
  }

  // how big a push along axis k, in direction sign, fits every thruster's limits
  reach(k, sign) {
    let most = Infinity;
    for (const row of this.mix) {
      const perUnit = row[k] * sign; // N from this thruster per unit of push
      if (perUnit > 0) most = Math.min(most, this.most / perUnit);
      if (perUnit < 0) most = Math.min(most, this.leastReverse / perUnit);
    }
    return most;
  }

  stick(k, amount) {
    return amount * (amount >= 0 ? this.fullStick[k].up : this.fullStick[k].down);
  }

  // Newtons wanted from a thruster -> the command that makes them. The
  // inverse of Vehicle.thrustFor: step over the dead band, and ask harder
  // when going backwards.
  commandFor(newtons) {
    const m = this.vehicle.thrusterModel;
    if (Math.abs(newtons) < 1e-6) return 0;
    const fraction = newtons > 0 ? newtons / m.forward : -newtons / m.reverse;
    const size = m.deadBand + Math.min(1, fraction) * (1 - m.deadBand);
    return newtons > 0 ? size : -size;
  }

  // wants: { forward, sideways, rise, turn (each -1..1), pitch, roll (target
  // angles in radians) }. Sets every thruster's command.
  fly(wants, dt) {
    const s = this.settings;
    const v = this.vehicle;
    const angles = v.angles();
    const w = v.spinRate;

    // The target angle follows the pilot's, but no faster than a set rate, so
    // a flick of the board does not slam the ROV over.
    const most = s.attitudeRate * dt;
    this.target.pitch += THREE.MathUtils.clamp(wants.pitch - this.target.pitch, -most, most);
    this.target.roll += THREE.MathUtils.clamp(wants.roll - this.target.roll, -most, most);

    // Hold pitch and roll like a spring with a shock absorber (P and D), plus
    // an integral term that pushes harder the longer an error lasts, plus
    // exactly cancelling the float's pull at the current angle, so the ROV
    // stays where it is put rather than sagging back towards level.
    //
    // Without the integral a steady load wins: the spring alone settles where
    // its push equals the load's, short of the target. A crab on the claw left
    // the triangle 5.3 deg nose-down -- worse than the 3.6 its float manages
    // with no help at all, because the stabilizer's spring is the softer one.
    //
    // (A "hold band" that rested the thrusters near the target and kicked them
    // on past 2 deg was tried, to save current. On the triangle it never
    // rested: its springy float bounced it straight back out of the band, and
    // the stabilizer was on 72-87% of the time with +-4 deg of wobble.)
    const pitchError = this.target.pitch - angles.pitch;
    const rollError = this.target.roll - angles.roll;
    const targetMoving = this.target.pitch !== wants.pitch || this.target.roll !== wants.roll;
    const I = v.inertia;
    const omega = s.stabilizerSpeed;
    const zeta = s.stabilizerDamping;
    const ki = s.stabilizerIntegral;
    // The integral only learns when the ROV is NEAR its target and the target
    // is still. Otherwise a big deliberate tilt -- or the cube pinned at the
    // most tilt its thrusters can hold -- piles up error that is not a steady
    // load at all, and it overshoots: the triangle swung to 44 deg on its way
    // to 35. A crab's few-degree dip is well inside. It is also capped, so a
    // long-held error cannot build an enormous push ("wind-up").
    if (!targetMoving) {
      const capPitch = (0.3 * this.fullStick[PITCH].up) / (I[0] * omega * omega * ki);
      const capRoll = (0.3 * this.fullStick[ROLL].up) / (I[2] * omega * omega * ki);
      if (Math.abs(pitchError) < s.integralWithin) {
        this.integral.pitch = THREE.MathUtils.clamp(this.integral.pitch + pitchError * dt, -capPitch, capPitch);
      }
      if (Math.abs(rollError) < s.integralWithin) {
        this.integral.roll = THREE.MathUtils.clamp(this.integral.roll + rollError * dt, -capRoll, capRoll);
      }
    }
    const float = v.buoyancyTorque(this._buoyancy);
    const pitchTorque =
      I[0] * (omega * omega * (pitchError + ki * this.integral.pitch) - 2 * zeta * omega * w.x) - float.x;
    const rollTorque =
      I[2] * (omega * omega * (rollError + ki * this.integral.roll) - 2 * zeta * omega * w.z) - float.z;

    // Turning: aim for a turn RATE, so letting go of the stick stops the turn.
    const p = v.profile;
    const wantRate = -wants.turn * s.maxTurnRate;
    const turnTorque =
      I[1] * s.turnResponse * (wantRate - w.y) +
      p.turnDrag.linear[1] * wantRate +
      p.turnDrag.quadratic[1] * wantRate * Math.abs(wantRate);

    const attitude = [0, 0, 0, pitchTorque, 0, rollTorque];
    const moving = [0, 0, 0, 0, 0, 0];
    moving[SURGE] = this.stick(SURGE, -wants.forward); // forward is -z
    moving[SWAY] = this.stick(SWAY, wants.sideways);
    moving[HEAVE] = this.stick(HEAVE, wants.rise);
    moving[YAW] = THREE.MathUtils.clamp(turnTorque, -this.fullStick[YAW].down, this.fullStick[YAW].up);

    const holding = this.apply(attitude);
    const going = this.apply(moving);

    // Asking for more tilt than the thrusters can give: scale the whole
    // stabilizing push down together. Clipping each thruster separately would
    // be stronger, but with reverse weaker than forward the clipped pairs no
    // longer cancel -- the cube drifted upwards 1.4 m in 6 s at full tilt.
    let fits = 1;
    for (const h of holding) {
      if (h > this.most) fits = Math.min(fits, this.most / h);
      if (h < this.leastReverse) fits = Math.min(fits, this.leastReverse / h);
    }
    for (let i = 0; i < holding.length; i++) holding[i] *= fits;

    // If the thrusters cannot do both, staying upright wins: scale back the
    // moving part until every thruster is within its limits.
    let share = 1;
    for (let i = 0; i < holding.length; i++) {
      if (going[i] > 0) share = Math.min(share, (this.most - holding[i]) / going[i]);
      if (going[i] < 0) share = Math.min(share, (this.leastReverse - holding[i]) / going[i]);
    }
    share = Math.max(0, share);
    v.thrusters.forEach((t, i) => {
      const newtons = THREE.MathUtils.clamp(holding[i] + going[i] * share, this.leastReverse, this.most);
      t.command = this.commandFor(newtons);
    });
  }

  // forces and torques -> newtons from each thruster
  apply(wrench) {
    return this.mix.map((row) => row.reduce((sum, m, k) => sum + m * wrench[k], 0));
  }
}

// The mixer: given the push wanted on each of the six axes, how hard should
// each thruster push? Each thruster's column says what one newton from it
// does to all six; inverting that table (a least-squares "pseudo-inverse")
// answers the question backwards. Rows are thrusters, columns the six axes,
// and each entry is newtons from that thruster per newton (or newton-metre)
// wanted.
function mixingMatrix(thrusters) {
  const columns = thrusters.map((t) => {
    const turn = new THREE.Vector3().crossVectors(t.offset, t.direction);
    return [t.direction.x, t.direction.y, t.direction.z, turn.x, turn.y, turn.z];
  });
  // A = B * B^T, plus a whisker on the diagonal so a ROV that cannot push
  // along some axis at all still gives an answer (of zero) for it
  const A = [];
  for (let r = 0; r < 6; r++) {
    A.push([]);
    for (let c = 0; c < 6; c++) {
      let sum = r === c ? 1e-9 : 0;
      for (const col of columns) sum += col[r] * col[c];
      A[r].push(sum);
    }
  }
  const inverse = invert(A);
  return columns.map((col) =>
    [0, 1, 2, 3, 4, 5].map((k) => col.reduce((sum, b, r) => sum + b * inverse[r][k], 0)),
  );
}

function invert(matrix) {
  // Gauss-Jordan elimination with partial pivoting.
  const n = matrix.length;
  const a = matrix.map((row, i) => [...row, ...row.map((_, j) => (i === j ? 1 : 0))]);
  for (let col = 0; col < n; col++) {
    let pivot = col;
    for (let r = col + 1; r < n; r++) {
      if (Math.abs(a[r][col]) > Math.abs(a[pivot][col])) pivot = r;
    }
    [a[col], a[pivot]] = [a[pivot], a[col]];
    const lead = a[col][col];
    for (let c = 0; c < 2 * n; c++) a[col][c] /= lead;
    for (let r = 0; r < n; r++) {
      if (r === col) continue;
      const factor = a[r][col];
      for (let c = 0; c < 2 * n; c++) a[r][c] -= factor * a[col][c];
    }
  }
  return a.map((row) => row.slice(n));
}
