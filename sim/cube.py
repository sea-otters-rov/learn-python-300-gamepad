"""The cube ROV's eight thrusters, by name.

    rov.thrust(cube.FORWARD_LEFT, 0.5)

Seen from above with the nose forward. A positive power pushes the way each name
says: UP thrusters push up, FORWARD push forward, SIDE push to the right.

The numbers are each thruster's place in games/rov_profiles.js, and the sim
checks them every time it loads your code. A misspelled name is an
AttributeError on the line that used it -- and VS Code underlines it first.
"""

# Four pushing up, one near each corner.
UP_FRONT_LEFT = 0
UP_FRONT_RIGHT = 1
UP_BACK_LEFT = 2
UP_BACK_RIGHT = 3

# Two pushing forward, on the left and right sides: tank drive.
FORWARD_LEFT = 4
FORWARD_RIGHT = 5

# Two pushing right, at the nose and the tail.
SIDE_FRONT = 6
SIDE_BACK = 7
