"""Tilt your controller to pitch and roll the ROV.

Tip your controller's far edge down and the ROV dips its nose; tip the right
edge down and it rolls right. All four up thrusters now do three jobs at once --
rising, pitching and rolling -- and each one's power is the three added up.
That adding is called mixing, and it is how every ROV is flown.
"""

import cube
from sim import Pad, Rov

heave_power = 0.5
# How much of each up thruster tilting may use, at full tilt.
pitch_power = 0.5
roll_power = 0.5

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

    left_power = -pad.left_y  # a stick pushed away reads -1; forward needs +1
    right_power = -pad.right_y
    rov.thrust(cube.FORWARD_LEFT, left_power)
    rov.thrust(cube.FORWARD_RIGHT, right_power)

    up_power = 0.0
    if pad.right_bumper:
        up_power = heave_power
    if pad.left_bumper:
        up_power = -heave_power

    # Far edge down reads -1 on tilt_y: the front thrusters push down, the back
    # ones up, and the nose dips. Right edge down reads +1 on tilt_x: the right
    # thrusters push down and the left ones up.
    pitch = pad.tilt_y * pitch_power
    roll = pad.tilt_x * roll_power

    front_left = up_power + pitch + roll
    front_right = up_power + pitch - roll
    back_left = up_power - pitch + roll
    back_right = up_power - pitch - roll

    rov.thrust(cube.UP_FRONT_LEFT, clamp(front_left))
    rov.thrust(cube.UP_FRONT_RIGHT, clamp(front_right))
    rov.thrust(cube.UP_BACK_LEFT, clamp(back_left))
    rov.thrust(cube.UP_BACK_RIGHT, clamp(back_right))

    side_power = pad.right_x
    rov.thrust(cube.SIDE_FRONT, side_power)
    rov.thrust(cube.SIDE_BACK, side_power)

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


# Try these:
#   - Hold the controller tipped all the way forward. How far does the ROV's
#     nose go down (the pitch in the top-left panel)? Why does it stop there,
#     not keep going?
#   - Keep holding it tipped and watch the depth, and the newtons each up
#     thruster is making. Two push up and two push down: why does the ROV
#     neither rise nor sink? Many thrusters push less in reverse than forward.
#     What would this ROV do then?
#   - Change clamp(back_left) to just back_left. Tip forward and right at once
#     and hold the right bumper to rise. What does the thruster panel say in red? What
#     was clamp() doing?
#   - Swap the + and - in front of roll on all four lines. Tip right: which way
#     does the ROV roll now?
#   - Is roll actually useful? Try setting roll_power to 0.0 and compare.
#   - Pick up the heavy crab and hold the controller level. Is the ROV level?
#     How far back do you have to tip the controller to hold it level by hand?
#     Could you keep that up for a whole mission?
