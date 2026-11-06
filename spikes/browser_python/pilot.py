"""Spike: tank drive, run by MicroPython inside the browser."""

import cube


def pilot(pad, rov):
    # Pushing a stick away from you reads -1; a thruster wants +1 for forward.
    left_power = -pad.left_y
    right_power = -pad.right_y
    rov.thrust(cube.FORWARD_LEFT, left_power)
    rov.thrust(cube.FORWARD_RIGHT, right_power)
