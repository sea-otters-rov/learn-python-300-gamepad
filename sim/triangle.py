"""The triangle ROV's six thrusters, by name.

    rov.thrust(triangle.UP_NOSE, 0.5)

Seen from above, the triangle points its nose forward. The three UP thrusters sit
just outside its corners and push up. The three EDGE thrusters sit along its
bottom edges, each pushing along its edge, all the same way round: all three at
+1 spins the ROV on the spot (clockwise from above). Going straight takes two or
three of them at once -- working out how much of each is the puzzle.

The numbers are each thruster's place in games/rov_profiles.js, and the sim
checks them every time it loads your code.
"""

UP_NOSE = 0
UP_REAR_RIGHT = 1
UP_REAR_LEFT = 2

EDGE_RIGHT = 3  # nose to rear right corner: pushes back and to the right
EDGE_BACK = 4  # rear right to rear left corner: pushes left
EDGE_LEFT = 5  # rear left corner to nose: pushes forward and to the right
