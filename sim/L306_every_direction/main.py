"""Add up, down and sideways.

Tank drive from lesson 305 still uses both sticks pushed up and down. That
leaves the bumpers for rising and diving, and the right stick's side-to-side
for sliding sideways -- the cube has two thrusters for that, at its nose and
tail.
"""

import cube
from sim import Pad, Rov

# A bumper is a button: on or off, nothing in between. So it runs the up
# thrusters at one fixed power, chosen here.
heave_power = 0.5


def pilot(pad: Pad, rov: Rov):
    left_power = -pad.left_y  # a stick pushed away reads -1; forward needs +1
    right_power = -pad.right_y
    rov.thrust(cube.FORWARD_LEFT, left_power)
    rov.thrust(cube.FORWARD_RIGHT, right_power)

    # Right bumper rises, left bumper dives.
    up_power = 0.0
    if pad.right_bumper:
        up_power = heave_power
    if pad.left_bumper:
        up_power = -heave_power
    rov.thrust(cube.UP_FRONT_LEFT, up_power)
    rov.thrust(cube.UP_FRONT_RIGHT, up_power)
    rov.thrust(cube.UP_BACK_LEFT, up_power)
    rov.thrust(cube.UP_BACK_RIGHT, up_power)

    # Both side thrusters push the same way, so the ROV slides without turning.
    side_power = pad.right_x
    rov.thrust(cube.SIDE_FRONT, side_power)
    rov.thrust(cube.SIDE_BACK, side_power)


# Try these:
#   - Hold both bumpers at once. Which one wins? Which line decides that?
#   - Let go of the bumpers halfway down. Does the ROV stay at that depth, sink
#     or float up? What does that tell you about how it was built?
#   - Run only cube.SIDE_FRONT for sliding. What does the ROV do instead?
#   - Set heave_power to 1.0 and dive. How many amps does it draw and how fast does it
#     move, compared with driving full speed forward?
