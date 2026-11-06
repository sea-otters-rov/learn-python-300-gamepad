"""Drive the cube ROV with tank controls.

Each stick runs the thruster on its own side, the way the club's ROVs were driven
last season: both sticks forward goes forward, one forward and one back turns on
the spot.

This file runs inside the ROV sim, not on your board. The sim calls pilot() 60
times a second with the controller (pad) and the ROV (rov). Save, and the sim
picks up your change straight away.
"""

import cube
from sim import Pad, Rov


def pilot(pad: Pad, rov: Rov):
    left_power = pad.left_y
    right_power = pad.right_y
    rov.thrust(cube.FORWARD_LEFT, left_power)
    rov.thrust(cube.FORWARD_RIGHT, right_power)
