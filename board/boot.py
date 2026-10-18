"""Turn the board into a USB gamepad: 16 buttons and 6 axes.

Chrome puts each axis in a fixed slot by its name, so these land in slots 0-5:
X, Y (left stick), Z, Rx (right stick), Ry, Rz (tilt).

boot.py runs only after a hard reset (the reset button, or unplugging), never
after a save, so a change here does nothing until then.

The gamepad is the ONLY HID device. With no keyboard, nothing a program does can
type into the editor it was saved from.
"""

import usb_hid

GAMEPAD_REPORT = bytes(
    (
        0x05, 0x01,  # Usage Page (Generic Desktop)
        0x09, 0x05,  # Usage (Game Pad)
        0xA1, 0x01,  # Collection (Application)
        0x85, 0x04,  #   Report ID (4)
        0x05, 0x09,  #   Usage Page (Button)
        0x19, 0x01,  #   Usage Minimum (Button 1)
        0x29, 0x10,  #   Usage Maximum (Button 16)
        0x15, 0x00,  #   Logical Minimum (0)
        0x25, 0x01,  #   Logical Maximum (1)
        0x75, 0x01,  #   Report Size (1)
        0x95, 0x10,  #   Report Count (16)
        0x81, 0x02,  #   Input (Data, Var, Abs)
        0x05, 0x01,  #   Usage Page (Generic Desktop)
        0x15, 0x81,  #   Logical Minimum (-127)
        0x25, 0x7F,  #   Logical Maximum (127)
        0x09, 0x30,  #   Usage (X)
        0x09, 0x31,  #   Usage (Y)
        0x09, 0x32,  #   Usage (Z)
        0x09, 0x33,  #   Usage (Rx)
        0x09, 0x34,  #   Usage (Ry)
        0x09, 0x35,  #   Usage (Rz)
        0x75, 0x08,  #   Report Size (8)
        0x95, 0x06,  #   Report Count (6)
        0x81, 0x02,  #   Input (Data, Var, Abs)
        0xC0,  # End Collection
    )
)  # fmt: skip

gamepad = usb_hid.Device(
    report_descriptor=GAMEPAD_REPORT,
    usage_page=0x01,
    usage=0x05,
    report_ids=(4,),
    in_report_lengths=(8,),
    out_report_lengths=(0,),
)

usb_hid.enable((gamepad,))
