"""Test cases for the Quad class from lpdpower.

Tim Nicholls, STFC Application Engineering
"""

import sys
if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch, call
else:                         # pragma: no cover
    from mock import Mock, patch, call

from nose.tools import *

sys.modules['serial'] = Mock()
from lpdpower.lcd_display import LcdDisplay, LcdDisplayError


class TestLcdDisplay():

    @classmethod
    def setup_class(cls):

        cls.pscu = Mock()
        cls.pscu.num_quads = 4
        cls.pscu.num_temperatures = 11
        cls.pscu.num_humidities = 2
        cls.pscu.get_all_latched.return_value = [True]*4
        cls.pscu.get_temperature.return_value = 20.0
        cls.pscu.get_temperature_name.return_value = 'Temp Sensor X'
        cls.pscu.get_temperature_disabled.return_value = False
        cls.pscu.get_humidity.return_value = 56.7
        cls.pscu.get_humidity_name.return_value = 'Humidity Sensor Y'
        cls.pscu.get_humidity_disabled.return_value = False
        cls.pscu.get_fan_speed.return_value = 45.0
        cls.pscu.get_fan_target.return_value = 90
        cls.pscu.get_pump_flow.return_value = 4.2
        cls.pscu.get_position.return_value = 11.36

        cls.pscu.quad = [Mock()]*4
        quad_fuse_blown = [True, False, False, False] * cls.pscu.num_quads
        quad_fet_failed = [False, True, False, False] * cls.pscu.num_quads
        for q in range(cls.pscu.num_quads):
            cls.pscu.quad[q].get_supply_voltage.return_value = 48.1
            cls.pscu.quad[q].get_channel_voltage.return_value = 48.0
            cls.pscu.quad[q].get_fuse_voltage = cls.fuse_voltage
            cls.pscu.quad[q].get_channel_current.return_value = 16.0
            cls.pscu.quad[q].get_fuse_blown.side_effect = quad_fuse_blown
            cls.pscu.quad[q].get_fet_failed.side_effect = quad_fet_failed

        cls.serial_dev = '/dev/null'
        cls.baud = 57600
        cls.rows = 4
        cls.cols = 20
        cls.display = LcdDisplay(cls.pscu, cls.serial_dev, baud=cls.baud, rows=cls.rows, cols=cls.cols)

    @classmethod
    def fuse_voltage(cls, quad_chan):
        if quad_chan < 2:
            fuse_voltage = 47.9
        else:
            fuse_voltage = 44.9
        return fuse_voltage

    def test_basic_init(self):
        assert_true(len(self.display.registered_pages) > 0)

    @patch('lpdpower.lcd_display.UsbLcd')
    def test_usb_init_exception(self, mock_usblcd):

        exception_str = 'UsbLcd exception'
        mock_usblcd.side_effect = Exception(exception_str)
        with assert_raises_regexp(
            LcdDisplayError, 'Failed to initialise LCD: {}'.format(exception_str)
        ):
            LcdDisplay(self.pscu, self.serial_dev)

    def test_set_colour(self):

        if self.display.lcd_colour == LcdDisplay.GREEN:
            colour = LcdDisplay.RED
        else:
            colour = LcdDisplay.GREEN

        self.display.set_colour(colour)
        assert_equal(colour, self.display.lcd_colour)

    def test_next_page(self):

        current_page = self.display.current_page
        next_page = (current_page + 1) % len(self.display.registered_pages)
        self.display.next_page()
        assert_equal(next_page, self.display.current_page)

    def test_next_page_loops(self):

        current_page = self.display.current_page
        num_pages = len(self.display.registered_pages)

        for i in range(num_pages * 2):
            self.display.next_page()

        assert_equal(current_page, self.display.current_page)

    def test_previous_page(self):

        current_page = self.display.current_page
        previous_page = (current_page - 1) % len(self.display.registered_pages)
        self.display.previous_page()
        assert_equal(previous_page, self.display.current_page)

    def test_previous_page_loops(self):

        current_page =self.display.current_page
        num_pages = len(self.display.registered_pages)

        for i in range(num_pages * 3):
            self.display.previous_page()

        assert_equal(current_page, self.display.current_page)

    def test_update(self):

        self.display.update()
        self.display.lcd.ser.write.assert_any_call(self.display.lcd_buffer)

    def test_format_state_str(self):

        assert_equal(self.display.format_state_str(True, True), 'OK')
        assert_equal(self.display.format_state_str(True, False), 'OK/Latch')
        assert_equal(self.display.format_state_str(False, True), "TRIPPED")

    def test_temperature_pages(self):

        self.pscu.get_temperature_disabled.return_value = False
        for page in range(self.display.num_temp_pages):
            content = self.display.temperature_page(page)
            for call in [
                    'get_temperature', 'get_temperature_latched', 'get_temperature_state',
                    'get_temperature_tripped', 'get_temperature_disabled']:
                assert_true(getattr(self.pscu, call).called, 'PSCU method {} not called'.format(call))
            assert_equal(type(content), str)
            assert_true(len(content) > 0)
            assert_true('Temp' in content)

    def test_temperature_page_sensor_disabled(self):

        self.pscu.get_temperature_disabled.return_value = True
        content = self.display.temperature_page(0)
        assert_equal(type(content), str)
        assert_true(len(content) > 0)
        assert_true('N/C' in content)

    def test_humidity_page(self):

        self.pscu.get_humidity_disabled.return_value = False
        content = self.display.humidity_page()
        for call in [
                'get_humidity', 'get_humidity_latched', 'get_humidity_state',
                'get_humidity_tripped', 'get_humidity_disabled']:
            assert_true(getattr(self.pscu, call).called, 'PSCU method {} not called'.format(call))
        assert_equal(type(content), str)
        assert_true(len(content) > 0)
        assert_true('Humidity' in content)

    def test_humidity_page_disabled(self):

        self.pscu.get_humidity_disabled.return_value = True
        content = self.display.humidity_page()
        assert_equal(type(content), str)
        assert_true(len(content) > 0)
        assert_true('N/C' in content)

    def test_fan_page(self):

        content = self.display.fan_page()
        for call in ['get_fan_speed', 'get_fan_target', 'get_fan_latched']:
            assert_true(getattr(self.pscu, call).called, 'PSCU method {} not called'.format(call))
        assert_true
        assert_equal(type(content), str)
        assert_true(len(content) > 0)
        for item in ['Fan', 'Target', 'Speed']:
            assert_true(item in content)

    def test_pump_page(self):

        content = self.display.pump_page()
        for call in ['get_pump_flow', 'get_pump_state', 'get_pump_latched']:
            assert_true(getattr(self.pscu, call).called, 'PSCU method {} not called'.format(call))
        assert_equal(type(content), str)
        assert_true(len(content) > 0)
        for item in ['Pump', 'Flow']:
            assert_true(item in content)

    def test_position_page(self):

        content = self.display.position_page()
        for call in ['get_position']:
            assert_true(getattr(self.pscu, call).called, 'PSCU method {} not called'.format(call))
        assert_equal(type(content), str)
        assert_true(len(content) > 0)
        for item in ['Position']:
            assert_true(item in content)

    def test_trace_page(self):

        content = self.display.trace_page()
        for call in [
            'get_trace_state', 'get_trace_latched', 'get_temperature_trace', 'get_humidity_trace', 'get_quad_trace'
        ]:
            assert_true(getattr(self.pscu, call).called, 'PSCU method {} not called'.format(call))
        assert_equal(type(content), str)
        assert_true(len(content) > 0)
        for item in ['Trace', 'Temp', 'Hum', 'Quad']:
            assert_true(item in content)

    def test_quad_supply_page(self):

        content = self.display.quad_supply_page()
        for q in range(self.pscu.num_quads):
            for call in ['get_supply_voltage']:
                assert_true(getattr(self.pscu.quad[q], call).called, 'PSCU method {} not called'.format(call))
            assert_equal(type(content), str)
            assert_true(len(content) > 0)
            assert_true('Quad supplies' in content)

    def test_quad_page(self):

        fuse_blown_seen = False
        fet_failed_seen = False
        for quad in range(4):
            for chan in range(2):
                content = self.display.quad_page(quad, chan*2)
                for call in [
                    'get_enable', 'get_channel_voltage', 'get_channel_current',
                    'get_fuse_blown', 'get_fet_failed',
                ]:
                    assert_true(getattr(self.pscu.quad[quad], call).called, 'PSCU method {} not called'.format(call))
                assert_equal(type(content), str)
                assert_true(len(content) > 0)
                assert_true('Quad' in content)
                assert_true('Chans' in content)
                if 'Fuse blown' in content:
                    fuse_blown_seen = True
                if 'FET failed' in content:
                    fet_failed_seen = True

        assert_true(fuse_blown_seen)
        assert_true(fet_failed_seen)

    def test_system_page(self):

        content = self.display.system_page()
        assert_equal(type(content), str)
        assert_true(len(content) > 0)
        assert_true('System Info' in content)
