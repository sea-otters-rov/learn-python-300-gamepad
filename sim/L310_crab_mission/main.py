"""Fly the whole mission on your own controls.

Collect all five crabs -- the heavy one too -- and drop them in the basket. This
is lesson 309's pilot, arranged so every thruster's power is worked out first
and sent at the end. It flies as it is. The two TODOs are what real ROV
pilots ask for; each one uses something you have already done. Do them in any
order, and keep checking the mission still works after each.
"""

import cube
from sim import Pad, Rov

heave_power = 0.5
max_tip = 5.0  # m/s^2 at full controller tilt: about 30 degrees
level_gain = 0.3  # power per m/s^2 off level

claw_was_pressed = False
camera_was_pressed = False


def clamp(power):
    """Keep a power inside what a thruster can do: -1.0 .. 1.0."""
    if power > 1.0:
        return 1.0
    if power < -1.0:
        return -1.0
    return power


def pilot(pad: Pad, rov: Rov):
    global claw_was_pressed, camera_was_pressed

    # ---- driving -----------------------------------------------------------
    left_power = -pad.left_y  # a stick pushed away reads -1; forward needs +1
    right_power = -pad.right_y

    # ---- up and down -------------------------------------------------------
    up_power = 0.0
    if pad.right_bumper:
        up_power = heave_power
    if pad.left_bumper:
        up_power = -heave_power

    # TODO 1 -- depth hold. rov.depth is how many meters down the ROV is, like
    # the real ROV's depth sensor. While a button of your choice is held (X and
    # Y are free), set up_power so the ROV reaches a depth you pick -- the same
    # idea as leveling in lesson 309, on a different reading. Between
    # self-leveling and depth-hold, holding the heavy crab is on easy mode!

    # ---- leveling (lesson 309) ---------------------------------------------
    target_x = pad.tilt_x * max_tip
    target_y = pad.tilt_y * max_tip
    rov_x, rov_y, rov_z = rov.acceleration
    error_x = target_x - rov_x
    error_y = target_y - rov_y
    pitch = error_y * level_gain
    roll = error_x * level_gain

    front_left = up_power + pitch + roll
    front_right = up_power + pitch - roll
    back_left = up_power - pitch + roll
    back_right = up_power - pitch - roll
    side_power = pad.right_x

    # TODO 2 -- stay under the fuse. rov.amps is what the whole ROV draws right
    # now; the club's fuse is 15 A. When it is over your limit, turn EVERY
    # thruster down by the same amount -- one number, kept between calls, that
    # every power below is multiplied by -- and let it creep back up when under.
    # Why every thruster, and not just the hungriest? Try both and watch where
    # the ROV goes.

    # ---- send it all -------------------------------------------------------
    rov.thrust(cube.FORWARD_LEFT, clamp(left_power))
    rov.thrust(cube.FORWARD_RIGHT, clamp(right_power))
    rov.thrust(cube.UP_FRONT_LEFT, clamp(front_left))
    rov.thrust(cube.UP_FRONT_RIGHT, clamp(front_right))
    rov.thrust(cube.UP_BACK_LEFT, clamp(back_left))
    rov.thrust(cube.UP_BACK_RIGHT, clamp(back_right))
    rov.thrust(cube.SIDE_FRONT, clamp(side_power))
    rov.thrust(cube.SIDE_BACK, clamp(side_power))

    # ---- claw and camera ---------------------------------------------------
    claw_pressed = pad.a
    just_pressed = claw_pressed and not claw_was_pressed
    if just_pressed:
        rov.claw_closed = not rov.claw_closed
    claw_was_pressed = claw_pressed

    # B switches between the cameras, the same way A works the claw.
    camera_pressed = pad.b
    if camera_pressed and not camera_was_pressed:
        rov.camera_onboard = not rov.camera_onboard
    camera_was_pressed = camera_pressed


# Make it yours:
#   - Press R to start again. The time for all five crabs is your score -- the
#     sim keeps your best. Who in the room can beat it?
#   - The heavy crab: can you still keep the ROV level while you rise with it?
#   - Do both TODOs work at once? What happens if you hold depth while
#     holding the heavy crab and drawing near the fuse's limit?
#   - So far we've used tank steering, with the left stick controlling the left
#     thrusters and the right stick the right. Try mixing them together, so you can
#     drive and turn with just the left stick. Which do you prefer?
