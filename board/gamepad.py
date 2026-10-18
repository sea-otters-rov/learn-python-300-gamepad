"""Send the board's sticks, tilt and buttons to the computer as a USB gamepad.

    import gamepad

    pad = gamepad.Gamepad()
    pad.left_x = 0.5  # -1.0 .. 1.0: exactly the number a game will see
    pad.set_button(gamepad.A, True)
    pad.send()

Buttons have the browser's names AND its numbers, counting from 0, so gamepad.A
here is buttons[0] in a game and "0 A" on the Controller check page.

Needs the gamepad that boot.py declares, which only happens after the reset
button is pressed or the board is unplugged -- never after a save.
"""

import usb_hid

# Buttons, in the browser's "standard" gamepad order.
A, B, X, Y = 0, 1, 2, 3
LB, RB, LT, RT = 4, 5, 6, 7
BACK, START = 8, 9
LEFT_CLICK, RIGHT_CLICK = 10, 11
DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT = 12, 13, 14, 15


def _find_gamepad():
    for device in usb_hid.devices:
        if device.usage_page == 0x01 and device.usage == 0x05:
            return device
    raise RuntimeError(
        "No gamepad. boot.py declares it, and boot.py only runs after the "
        "reset button is pressed or the board is unplugged."
    )


def _report_byte(value):
    """-1.0 .. 1.0 into the -127 .. 127 a USB gamepad report carries."""
    value = max(-1.0, min(1.0, value))
    return round(value * 127) & 0xFF


class Gamepad:
    def __init__(self):
        self._device = _find_gamepad()
        self._report = bytearray(8)
        self._last = bytearray(8)
        self.buttons = 0  # one bit per button, bit 0 is A
        self.left_x = self.left_y = 0.0
        self.right_x = self.right_y = 0.0
        self.tilt_x = self.tilt_y = 0.0

    def press(self, button):
        self.buttons |= 1 << button

    def release(self, button):
        self.buttons &= ~(1 << button)

    def set_button(self, button, pressed):
        """Press or release, whichever `pressed` says."""
        if pressed:
            self.press(button)
        else:
            self.release(button)

    def send(self):
        """Send everything to the computer, if anything changed."""
        report = self._report
        report[0] = self.buttons & 0xFF
        report[1] = self.buttons >> 8 & 0xFF
        # This order is boot.py's X, Y, Z, Rx, Ry, Rz -- browser axes 0 to 5.
        axes = (
            self.left_x,
            self.left_y,
            self.right_x,
            self.right_y,
            self.tilt_x,
            self.tilt_y,
        )
        for i, value in enumerate(axes):
            report[2 + i] = _report_byte(value)
        if report != self._last:
            self._device.send_report(report)
            self._last[:] = report
