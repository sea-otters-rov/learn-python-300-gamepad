"""The cube ROV's eight thrusters, by name.

    rov.thrust(cube.FORWARD_LEFT, 0.5)

The numbers are each thruster's place in games/rov_profiles.js, which is where
the sim looks them up. A misspelled name is an AttributeError on the line that
used it -- and VS Code underlines it before you save.
"""

# Four pushing up, one at each corner, seen from above with the nose forward.
UP_FRONT_LEFT = 0
UP_FRONT_RIGHT = 1
UP_BACK_LEFT = 2
UP_BACK_RIGHT = 3

# Two pushing forward, one each side: the tank drive.
FORWARD_LEFT = 4
FORWARD_RIGHT = 5

# Two pushing right, one at the nose and one at the tail.
SIDE_FRONT = 6
SIDE_BACK = 7
