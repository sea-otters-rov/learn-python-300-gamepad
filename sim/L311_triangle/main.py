"""Stretch: map the controls to the triangle ROV.

Press 2 in the sim to fly the triangle, 1 to go back to the cube. The triangle
has six thrusters where the cube has eight: three pushing up, just outside its
corners, and three along its bottom edges, each pushing along its edge. It is
lighter, quicker -- and much easier to tip: the heavy crab pitches it about 40
degrees nose-down. This starts you off with up and down, the claw and the
camera. See if you can get it to drive!
"""

import triangle
from sim import Pad, Rov

heave_power = 0.5

claw_was_pressed = False
camera_was_pressed = False


def pilot(pad: Pad, rov: Rov):
    global claw_was_pressed, camera_was_pressed

    up_power = 0.0
    if pad.right_bumper:
        up_power = heave_power
    if pad.left_bumper:
        up_power = -heave_power
    rov.thrust(triangle.UP_NOSE, up_power)
    rov.thrust(triangle.UP_REAR_RIGHT, up_power)
    rov.thrust(triangle.UP_REAR_LEFT, up_power)

    # TODO -- driving. Each EDGE thruster at +1 pushes the ROV (measured):
    #
    #     EDGE_LEFT    forward 0.87, right 0.5
    #     EDGE_RIGHT   forward -0.87 (backwards), right 0.5
    #     EDGE_BACK    right -1 (to the left)
    #
    # and all three at +1 spin it clockwise on the spot. So no thruster pushes
    # straight forward: going forward takes EDGE_LEFT forward AND EDGE_RIGHT in
    # reverse, so their sideways pushes cancel. Start there. Then watch the
    # pitch: the nose lifts as it goes, and it climbs. The edge thrusters sit
    # low on the frame, below the center of mass -- which other thrusters
    # could hold the nose down?

    # TODO -- leveling, as in lesson 309. UP_NOSE is at the front, the two
    # UP_REAR thrusters at the back corners. Which ones lift the nose? Which
    # pair rolls it? How much of each, when there is one at the front and two
    # at the back?

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


# Things to find out:
#   - Run only triangle.EDGE_BACK. Which way does the ROV go, and does it turn?
#   - Hold the right bumper to rise with no leveling at all. Does the triangle stay
#     level? Now pick up the heavy crab. Compare with the cube.
#   - Would you build the triangle for the club? What would you need the
#     control code to do that the cube does not?
