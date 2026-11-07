"""What your pilot() is given: the controller, and the ROV it flies.

The sim calls your pilot(pad, rov) 60 times a second, every second the ROV is in
the water. You never make a Pad or a Rov yourself -- the sim fills both in fresh
before every call. pilot() must do its work and return: the sim is the loop, so
there is no while True in it.

You do not need to read this file to fly. It is here so VS Code knows what `pad.`
and `rov.` can be followed by, and so you can look up exactly what each one means.
"""


class Pad:
    """The controller, exactly as your board sent it. Nothing is smoothed or fixed.

    Sticks and tilt run from -1.0 to 1.0, the same numbers the Controller check
    page shows. Buttons are True while held down.
    """

    def __init__(self):
        self.left_x = 0.0  # -1 all the way left .. +1 all the way right
        self.left_y = 0.0  # -1 pushed away from you .. +1 pulled toward you
        self.right_x = 0.0
        self.right_y = 0.0
        self.tilt_x = 0.0  # +1 right edge down
        self.tilt_y = 0.0  # -1 far edge down
        self.a = False
        self.b = False
        self.x = False
        self.y = False
        self.left_bumper = False
        self.right_bumper = False
        # Not wired by default -- the lessons use only the six above. Wire
        # them (pin picture: LT D2, RT D3, Start D6) and these work too.
        self.left_trigger = False
        self.right_trigger = False
        self.start = False


class Rov:
    """The ROV: thrusters, claw and camera to command; sensors to read.

    Every thruster stops before each call, so one you do not run this call is
    off. The claw and the camera stay however you last set them.
    """

    def __init__(self, thruster_count):
        # Commands -- set these.
        self.claw_closed = False  # True grips; it stays closed until set False
        self.camera_onboard = False  # True looks through the ROV's own camera

        # Sensors -- read these.

        # m/s^2, like your controller's accelerometer if it were bolted flat on
        # the ROV with its far edge at the nose: level reads about (0, 0, 9.8),
        # right side down makes x go up, nose down makes y go down.
        self.acceleration = (0.0, 0.0, 9.8)
        self.depth = 0.0  # m below the surface
        self.heading = 0.0  # compass degrees: 0 .. 360, turning right counts up
        self.amps = 0.0  # current the whole ROV is drawing right now

        self._commands = [0.0] * thruster_count

    def thrust(self, thruster, power):
        """Run one thruster: power from -1.0 (full reverse) to 1.0 (full forward).

        thruster is a name from cube.py or triangle.py, like cube.FORWARD_LEFT.
        Asking for more than 1.0 gets you 1.0 -- the thruster panel shows what
        you asked for, so you can see when that happens.
        """
        if not 0 <= thruster < len(self._commands):
            raise ValueError(
                f"there is no thruster {thruster} on this ROV -- "
                "use a name from cube.py or triangle.py"
            )
        if not isinstance(power, (int, float)):
            raise TypeError(f"power must be a number, not {power!r}")
        self._commands[thruster] = power
