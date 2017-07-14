"""Test cases for the UsbLcd class from lpdpower.

Tim Nicholls, STFC Application Engineering
"""

import sys
if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch, call
else:                         # pragma: no cover
    from mock import Mock, patch, call

from nose.tools import *

sys.modules['serial'] = Mock()
from lpdpower.usblcd import UsbLcd

class TestUsbLcd():

    @classmethod
    @patch('lpdpower.usblcd.serial.Serial')
    def setup_class(cls, mock_serial):

        cls.mock_serial = mock_serial

        cls.serial_dev = '/dev/null'
        cls.baud = 57600
        cls.rows = 4
        cls.cols = 20
        cls.lcd = UsbLcd(cls.serial_dev, cls.baud, cls.rows, cls.cols)

        cls.serial = cls.lcd.ser

        # Save the initialisation calls so we can test the setup
        cls.init_calls = cls.serial.write.mock_calls[:]

    def setup(self):

        self.serial.reset_mock()

    def make_call_list(self, cmds):

        cmds.insert(0, UsbLcd.CMD_START)

        calls = [call(chr(cmd)) for cmd in cmds]
        return calls

    def test_00_init(self):

        self.mock_serial.assert_any_call(self.serial_dev, self.baud)

        init_calls = self.make_call_list([UsbLcd.CMD_LCD_SIZE, self.cols, self.rows])
        assert_equal(self.init_calls, init_calls)

    def test_home(self):

        self.lcd.home()
        home_calls = self.make_call_list([UsbLcd.CMD_HOME])
        self.serial.write.assert_has_calls(home_calls)

    def test_clear(self):

        self.lcd.clear()
        clear_calls = self.make_call_list([UsbLcd.CMD_CLEAR])
        self.serial.write.assert_has_calls(clear_calls)

    def test_write(self):

        write_cmd = 'text'
        self.lcd.write(write_cmd)
        self.serial.write.assert_called_with(write_cmd)

    def test_set_splash_text(self):

        splash_text = 'This is a test'
        self.lcd.set_splash_text(splash_text)

        screen_len = self.rows * self.cols
        trailing_space = screen_len - len(splash_text)
        splash_buffer = splash_text + ' ' * trailing_space
        splash_cmds = [UsbLcd.CMD_SET_SPLASH]
        splash_cmds += [ord(splash_char) for splash_char in list(splash_buffer)]
        splash_calls = self.make_call_list(splash_cmds)

        self.serial.write.assert_has_calls(splash_calls)

    def test_set_backlight_colour(self):

        rgb_val = (0x55, 0xaa, 0xff)
        self.lcd.set_backlight_colour(rgb_val)
        backlight_calls = self.make_call_list([UsbLcd.CMD_RGB_BACKLIGHT] + list(rgb_val))
        self.serial.write.assert_has_calls(backlight_calls)

    def test_set_autoscroll_mode_on(self):

        self.lcd.set_autoscroll_mode(True)
        mode_calls = self.make_call_list([UsbLcd.CMD_AUTOSCROLL_ON])
        self.serial.write.assert_has_calls(mode_calls)

    def test_set_autoscroll_mode_off(self):

        self.lcd.set_autoscroll_mode(False)
        mode_calls = self.make_call_list([UsbLcd.CMD_AUTOSCROLL_OFF])
        self.serial.write.assert_has_calls(mode_calls)

    def test_set_brightness(self):

        brightness = 123
        self.lcd.set_brightness(brightness)
        brightness_calls = self.make_call_list([UsbLcd.CMD_BRIGHTNESS, brightness])
        self.serial.write.assert_has_calls(brightness_calls)

    def test_set_contrast(self):

        constrast = 37
        self.lcd.set_contrast(constrast)
        contrast_calls = self.make_call_list([UsbLcd.CMD_CONTRAST, constrast])
        self.serial.write.assert_has_calls(contrast_calls)

    def test_close(self):

        self.lcd.close()
        self.serial.close.assert_called_once_with()
