"""UsbLcd - driver class for LCD module with Adafruit USB backpack.

This module provides a simple driver class for an LCD module interfaced via
an Adafruit USB LCD backpack, as documented here:

https://learn.adafruit.com/usb-plus-serial-backpack

This class requires the python serial module to communicate with the USB
serial device created by the host operating system,
"""
import serial


class UsbLcd(object):
    """UsbLcd - driver class for a LCD module with Adafruit USB backpack.

    This module provides a simple driver class for an LCD module interfaced via
    an Adafruit USB LCD backpack.
    """

    # Define RGB value tuples for common colours
    RED = (0xFF, 0x00, 0x00)
    GREEN = (0x00, 0xFF, 0x00)
    BLUE = (0x00, 0x00, 0xFF)
    WHITE = (0xFF, 0xFF, 0xFF)
    YELLOW = (0xFF, 0x22, 0x00)

    # Define backpack command bytes
    CMD_START = 0xFE
    CMD_LCD_SIZE = 0xD1
    CMD_HOME = 0x48
    CMD_CLEAR = 0x58
    CMD_SET_SPLASH = 0x40
    CMD_RGB_BACKLIGHT = 0xD0
    CMD_AUTOSCROLL_ON = 0x51
    CMD_AUTOSCROLL_OFF = 0x52
    CMD_BRIGHTNESS = 0x99
    CMD_CONTRAST = 0x50

    def __init__(self, serial_dev, baud=57600, rows=2, cols=16):
        """Initialise the USB LCD device.

        This constructor opens the serial device and sets up the LCD size by
        sending the appopriate command.

        :param serial_dev: serial device to open, e.g. /dev/ttyUSB0
        :param baud: serial port baud rate
        :param rows: number of LCD rows
        :param cols: number of LCD columns
        """
        self.ser = serial.Serial(serial_dev, baud)
        self.rows = rows
        self.cols = cols

        self.write_cmd([UsbLcd.CMD_LCD_SIZE, self.cols, self.rows])

    def write_cmd(self, cmd_list):
        """Write a command to the display.

        This method writes a variable length command to the display, prefixing the
        command with a START byte and converting the command to the appropriate character
        list.

        :param cmd_list list of commands to send
        """
        cmd_list.insert(0, UsbLcd.CMD_START)
        for i in range(0, len(cmd_list)):
            self.ser.write(chr(cmd_list[i]))

    def home(self):
        """Set the display cursor to the home position.

        This method tells the display to set the cursor to the home position, i.e. top left.
        """
        self.write_cmd([UsbLcd.CMD_HOME])

    def clear(self):
        """Clear the display.

        This method sends a command to clear the display.
        """
        self.write_cmd([UsbLcd.CMD_CLEAR])

    def write(self, text):
        """Write text to the display.

        This method writes the specified text string to the display.

        :param text: text string to write to the display
        """
        self.ser.write(text)

    def set_splash_text(self, text):
        """Set the splash text for the display.

        This method sets the splash text for the display, i.e. the persistent
        text that is temporarily shwon on the display at power-up.

        :param text: splash text to save to the display
        """
        splash_data = [ord(' ')]*(self.rows * self.cols)
        splash_data.insert(0, UsbLcd.CMD_SET_SPLASH)

        for i in range(len(text)):
            splash_data[i+1] = ord(text[i])

        self.write_cmd(splash_data)

    def set_backlight_colour(self, rgb_val):
        """Set the LCD backlight colour.

        This method sets the LCD backlight colour to a RGB value specified as a 3-tuple
        of bytes, e.g. (0xFF, 0x00, 0x00). The class specifies some commonly-used helper
        values, for instance UsbLcd.RED, that may be used.

        :param rgb_val: RGB byte values as tuple
        """
        # TODO validate rgb_val is tuple
        rgb_data = [UsbLcd.CMD_RGB_BACKLIGHT]
        rgb_data.extend(rgb_val)

        self.write_cmd(rgb_data)

    def set_autoscroll_mode(self, enabled=True):
        """Set the LCD autoscroll mode.

        Thie method sets the LCD autoscroll mode to on or off depending on the argument.

        :param enabled: boolean flag for autoscroll mode enable
        """
        if enabled:
            cmd = UsbLcd.CMD_AUTOSCROLL_ON
        else:
            cmd = UsbLcd.CMD_AUTOSCROLL_OFF

        self.write_cmd([cmd])

    def set_brightness(self, brightness):
        """Set the LCD display brightness.

        This method set the LCD display brightness to the specified byte value, i.e. a
        value between 0 and 255.

        :param brightness: value to set
        """
        self.write_cmd([UsbLcd.CMD_BRIGHTNESS, brightness])

    def set_contrast(self, contrast):
        """Set the LCD display brightness.

        This method set the LCD display brightness to the specified byte value, i.e. a
        value between 0 and 255.

        :param contrast: value to set
        """
        self.write_cmd([UsbLcd.CMD_CONTRAST, contrast])

    def close(self):
        """Close connection to device.

        This method closes the connection to the display serial device.
        """
        self.ser.close()
