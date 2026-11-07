"""Drive the cube ROV with tank controls.
http://localhost:8770/games/rov_sim.html

Each stick runs the thruster on its own side, the way the club's ROVs were driven
last season: both sticks forward goes forward, one forward and one back turns on
the spot.

This file runs inside the ROV sim, not on your board -- your board stays your
controller. The sim calls pilot() 60 times a second with the controller (pad)
and the ROV (rov). Save, and the sim picks up your change immediately. There
is no going up or down and no claw (yet).
"""

import cube
from sim import Pad, Rov


def pilot(pad: Pad, rov: Rov):
    # A stick pushed away from you reads -1, but a thruster needs +1 to push
    # forward. The minus sign turns one into the other.
    left_power = -pad.left_y
    right_power = -pad.right_y

    rov.thrust(cube.FORWARD_LEFT, left_power)
    rov.thrust(cube.FORWARD_RIGHT, right_power)


# Try these:
#   - Take out both minus signs and push both sticks forward. What does the ROV
#     do? Which part of the sim tells you what each thruster was asked for?
#   - Make the thrusters run at most half power, and give that number a name.
#     Is half power half speed? Watch the speed in the top-left panel.
