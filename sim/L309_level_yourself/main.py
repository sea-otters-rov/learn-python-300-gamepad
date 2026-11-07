"""Make the ROV hold itself level with its own accelerometer.

In lesson 308 your tilt pushed the thrusters, and the ROV went wherever that
push and its float agreed on. Now the ROV measures itself: rov.acceleration
works like your controller's tilt sensor, bolted to the ROV. Your tilt says what
you WANT; the ROV compares that with what it HAS and pushes to close the gap.
Measure, compare, correct -- 60 times a second. That loop is called feedback.

Pick up the heavy crab with the controller held level and watch the nose.
"""

import cube
from sim import Pad, Rov

heave_power = 0.5
# Full controller tilt asks for this much tip, in m/s^2 -- about 30 degrees,
# like full_tilt in lesson 303.
max_tip = 5.0
# Thruster power for each m/s^2 the ROV is off from what you asked for.
level_gain = 0.3

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

    # What you want: your controller's tilt, as m/s^2 of tip. Level is 0, 0.
    target_x = pad.tilt_x * max_tip
    target_y = pad.tilt_y * max_tip

    # What the ROV has: its own accelerometer, signed like your controller's --
    # right side down makes x go up, nose down makes y go down. If you're perfectly
    # level, rov.acceleration is 0, 0, 9.8.
    rov_x, rov_y, rov_z = rov.acceleration

    # How far off it is, and a push to match.
    error_x = target_x - rov_x
    error_y = target_y - rov_y
    pitch = error_y * level_gain
    roll = error_x * level_gain

    # The same mixing as lesson 308.
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
#   - Pick up the heavy crab, controller level, holding your depth with the
#     bumpers. Compare the nose with lesson 308's. Is it perfectly level now?
#   - Tip the controller all the way forward. Does the ROV reach the same tilt
#     as your hand? Why would it stop short?
#   - Make level_gain 0.1, then 1.0. With the heavy crab, how big is the dip
#     each time? And what is the ROV doing at 1.0 -- does it ever settle?
#     (Watch the current too.) Why not just make the gain as big as you can?
#   - Try setting max_tip to 0. Tilting the controller does nothing, but what
#     happens now if you pick up the heavy crab? Is this easier to control?
