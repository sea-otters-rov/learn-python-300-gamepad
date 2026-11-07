"""Work the claw and collect your first crab.

One press of A closes the claw; the next press opens it. Fly the
claw's tip onto a crab, close it, carry the crab to the orange basket at the far
end, and open it over the basket.

The hard part: pilot() runs 60 times a second, so a press that lasts a quarter of
a second is seen 15 times. The claw must change once per PRESS, not once per call.
"""

import cube
from sim import Pad, Rov

heave_power = 0.5

# Whether the claw button was down last time pilot() ran. It lives out here,
# not inside pilot(): anything made inside pilot() is forgotten when it returns.
claw_was_pressed = False


def pilot(pad: Pad, rov: Rov):
    # global lets pilot() change claw_was_pressed outside this def
    global claw_was_pressed

    left_power = -pad.left_y  # a stick pushed away reads -1; forward needs +1
    right_power = -pad.right_y
    rov.thrust(cube.FORWARD_LEFT, left_power)
    rov.thrust(cube.FORWARD_RIGHT, right_power)

    up_power = 0.0
    if pad.right_bumper:
        up_power = heave_power
    if pad.left_bumper:
        up_power = -heave_power
    rov.thrust(cube.UP_FRONT_LEFT, up_power)
    rov.thrust(cube.UP_FRONT_RIGHT, up_power)
    rov.thrust(cube.UP_BACK_LEFT, up_power)
    rov.thrust(cube.UP_BACK_RIGHT, up_power)

    side_power = pad.right_x
    rov.thrust(cube.SIDE_FRONT, side_power)
    rov.thrust(cube.SIDE_BACK, side_power)

    # A press is the moment the button goes from up to down: down now, and not
    # down last time.
    claw_pressed = pad.a
    just_pressed = claw_pressed and not claw_was_pressed
    if just_pressed:
        rov.claw_closed = not rov.claw_closed
    claw_was_pressed = claw_pressed


# Try these:
#   - Take out "and not claw_was_pressed", then hold A down. What does
#     the claw do, and why?
#   - The real ROV has two cameras, and so does the sim: setting
#     "rov.camera_onboard = True" looks through the ROV's claw cam. Make the B button
#     switch cameras, the same way as the claw.
#   - One crab is bigger and darker: the heavy one. Pick it up. What happens to
#     the ROV's nose? Can you still get it in the basket?!
