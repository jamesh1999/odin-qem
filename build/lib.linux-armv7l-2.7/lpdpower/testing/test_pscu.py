"""Test cases for the PSCU class from lpdpower.

Tim Nicholls, STFC Application Engineering
"""

import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch, call
else:                         # pragma: no cover
    from mock import Mock, patch, call

from nose.tools import *
from functools import partial

sys.modules['smbus'] = Mock()
sys.modules['serial'] = Mock()
sys.modules['Adafruit_BBIO'] = Mock()
sys.modules['Adafruit_BBIO.GPIO'] = Mock()
from lpdpower.pscu import PSCU
from lpdpower.i2c_device import I2CException

class TestPSCU():

    @classmethod
    @patch('lpdpower.i2c_device.smbus.SMBus')
    def setup_class(cls, mock_bus):

        cls.mock_bus = mock_bus

        cls.pscu_options = {
            'quad_enable_interval': 0.9,
            'detector_position_offset': 35.355,
        }

        cls.pscu = PSCU(**cls.pscu_options)
        cls.bus = cls.pscu.tca.bus
        cls.bus.read_word_data.return_value = 0

    def test_init(self):

        assert_equal(self.bus, self.pscu.tca.bus)
        assert_equal(self.pscu.quad_enable_interval, self.pscu_options['quad_enable_interval'])
        assert_equal(self.pscu.detector_position_offset, self.pscu_options['detector_position_offset'])

    def test_init_default_options(self):

        pscu = PSCU()
        assert_equal(pscu.quad_enable_interval, PSCU.DEFAULT_QUAD_ENABLE_INTERVAL)
        assert_equal(pscu.detector_position_offset, PSCU.DEFAULT_DETECTOR_POSITION_OFFSET)

    @patch('lpdpower.lcd_display.UsbLcd')
    @patch('lpdpower.i2c_device.smbus.SMBus')
    def test_init_display_error(self, mock_bus, mock_usblcd):

        exception_str = 'LcdDisplay exception'
        mock_usblcd.side_effect = Exception(exception_str)
        pscu = PSCU()
        assert_true(pscu.lcd_display_error)

    def test_deferred_executor(self):

        num_tasks = 10
        self.task_count = 0

        def deferred_task():
            self.task_count += 1

        for i in range(num_tasks):
            self.pscu.deferred_executor.enqueue(deferred_task, 0)

        while self.pscu.deferred_executor.pending():
            self.pscu.handle_deferred()

        assert_equal(self.task_count, num_tasks)

    def test_generate_indexed_getter_tests(self):

        for (method, return_type) in [
            ('get_temperature', float),
            ('get_temperature_volts', float),
            ('get_temperature_set_point', float),
            ('get_temperature_set_point_volts', float),
            ('get_temperature_tripped', bool),
            ('get_temperature_trace', bool),
            ('get_temperature_disabled', bool),
            ('get_temperature_name', str),
            ('get_temperature_mode', str),
            ('get_humidity', float),
            ('get_humidity_volts', float),
            ('get_humidity_set_point', float),
            ('get_humidity_set_point_volts', float),
            ('get_humidity_tripped', bool),
            ('get_humidity_trace', bool),
            ('get_humidity_disabled', bool),
            ('get_humidity_name', str),
            ('get_humidity_mode', str),
        ]:
            for (legal_sensor, label) in [(True, 'legal'), (False, 'illegal')]:
                test_func = partial(self._test_pscu_indexed_getter, method, legal_sensor, return_type)
                test_func.description = '{}.{}.test_{}_{}_sensor'.format(
                    __name__, self.__class__.__name__, method, label
                )
                yield (test_func, )

    def _test_pscu_indexed_getter(self, method, is_legal, return_type):

        legal_sensor = 1
        illegal_sensor = 12

        if is_legal:
            val = getattr(self.pscu, method)(legal_sensor)
            assert_equal(type(val), return_type)
        else:
            with assert_raises_regexp(I2CException,
                'Illegal sensor index {} specified'.format(illegal_sensor)
            ):
                getattr(self.pscu, method)(illegal_sensor)

    def test_generate_simple_getter_tests(self):

        for (method, return_type) in [
          ('get_pump_flow', float),
          ('get_pump_flow_volts', float),
          ('get_pump_set_point', float),
          ('get_pump_set_point_volts', float),
          ('get_pump_tripped', bool),
          ('get_pump_mode', str),
          ('get_fan_speed', float),
          ('get_fan_speed_volts', float),
          ('get_fan_set_point', float),
          ('get_fan_set_point_volts', float),
          ('get_fan_target', float),
          ('get_fan_tripped', bool),
          ('get_fan_mode', str),
          ('get_position', float),
          ('get_position_volts', float),
          ('get_armed', bool),
          ('get_temperature_state', bool),
          ('get_temperature_latched', bool),
          ('get_trace_state', bool),
          ('get_trace_latched', bool),
          ('get_fan_state', bool),
          ('get_fan_latched', bool),
          ('get_pump_state', bool),
          ('get_pump_latched', bool),
          ('get_humidity_state', bool),
          ('get_humidity_latched', bool),
          ('get_all_latched', list),
          ('get_enable_interval', float),
          ('get_all_enabled', bool),
          ('get_health', bool),
        ]:
            test_func = partial(self._test_pscu_simple_getter, method, return_type)
            test_func.description = '{}.{}.test_{}'.format(
                __name__, self.__class__.__name__, method
            )
            yield (test_func, )

    def _test_pscu_simple_getter(self, method, return_type):

        val = getattr(self.pscu, method)()
        assert_equal(type(val), return_type)

    def test_get_quad_trace(self):

        val = self.pscu.get_quad_trace(0)
        assert_equal(type(val), bool)

    def test_get_quad_trace_illegal_quad(self):

        for illegal_quad in [-1, 4]:
            with assert_raises_regexp(I2CException, 'Illegal quad index {} specified'.format(illegal_quad)):
                self.pscu.get_quad_trace(illegal_quad)


    def test_quad_enable_channel(self):

        with patch('lpdpower.pscu.Quad.set_enable') as mock_enable:
            self.pscu.quad_enable_channel(2, 3)
            mock_enable.assert_called_with(3, True)

    def test_quad_enable_channel_illegal_quad(self):

        illegal_quad = 4
        with assert_raises_regexp(I2CException, 'Illegal quad index {} specified'.format(illegal_quad)):
            self.pscu.quad_enable_channel(illegal_quad, 0)

    def test_quad_enable_channel_illegal_channel(self):

        illegal_channel = 4
        with assert_raises_regexp(I2CException, 'Illegal channel index {} specified'.format(illegal_channel)):
            self.pscu.quad_enable_channel(2, illegal_channel)

    def test_enable_all(self):

        enable_interval = self.pscu.get_enable_interval()
        self.pscu.quad_enable_interval = 0.0

        enable_calls = []
        for _ in range(4):
            for chan in range(4):
                enable_calls.append(call(chan, True))

        with patch('lpdpower.pscu.Quad.set_enable') as mock_enable:
            self.pscu.enable_all(True)
            while self.pscu.deferred_executor.pending():
                self.pscu.handle_deferred()
            mock_enable.assert_has_calls(enable_calls)
            assert_equal(len(mock_enable.mock_calls), len(enable_calls))

        self.pscu.quad_enable_interval = enable_interval

    def test_disable_all(self):

        enable_interval = self.pscu.get_enable_interval()
        self.pscu.quad_enable_interval = 0.0

        enable_calls = []
        for _ in range(4):
            for chan in range(4):
                enable_calls.append(call(chan, False))

        with patch('lpdpower.pscu.Quad.set_enable') as mock_enable:
            # Enable all to push pending enables onto deferred executor queue
            self.pscu.enable_all(True)
            self.pscu.enable_all(False)
            while self.pscu.deferred_executor.pending():
                self.pscu.handle_deferred()
            mock_enable.assert_has_calls(enable_calls)
            assert_equal(len(mock_enable.mock_calls), len(enable_calls))

        self.pscu.quad_enable_interval = enable_interval

    def test_set_armed(self):

        arm_pin = 0
        arm_calls = [call(arm_pin, 0), call(arm_pin, 1), call(arm_pin, 0)]

        with patch('lpdpower.pscu.MCP23008.output') as mock_output:
            self.pscu.set_armed(True)
            mock_output.assert_has_calls(arm_calls)
            assert_equal(len(mock_output.mock_calls), len(arm_calls))

    def test_set_fan_target(self):

        with patch('lpdpower.pscu.AD5321.set_output_scaled') as mock_output:

            for target in [0.0, 50.0, 100.0]:
                output_value = (1.0 - (target / 100.0))
                self.pscu.set_fan_target(target)
                mock_output.assert_called_with(output_value)

    def test_get_display_error(self):

        assert_equal(self.pscu.get_display_error(), False)

    def test_udpate_lcd_no_event(self):

        with patch('lpdpower.pscu.LcdDisplay.update') as mock_update:
            with patch('lpdpower.pscu.GPIO.event_detected', return_value=False) as mock_event:
                current_page = self.pscu.lcd.current_page
                self.pscu.update_lcd()
                assert_equal(self.pscu.lcd.current_page, current_page)
                mock_update.assert_called_once_with()

    def test_update_lcd_btn_previous(self):

        with patch('lpdpower.pscu.GPIO.event_detected', side_effect=[True, False]) as mock_event:
            expected_page = self.pscu.lcd.current_page - 1
            expected_page %= len(self.pscu.lcd.registered_pages)
            self.pscu.update_lcd()
            assert_equal(self.pscu.lcd.current_page, expected_page)

    def test_update_lcd_btn_next(self):

        with patch('lpdpower.pscu.GPIO.event_detected', side_effect=[False, True]) as mock_event:
            expected_page = self.pscu.lcd.current_page + 1
            expected_page %= len(self.pscu.lcd.registered_pages)
            self.pscu.update_lcd()
            assert_equal(self.pscu.lcd.current_page, expected_page)

    def test_update_lcd_healthy(self):

        current_health = self.pscu._PSCU__healthy
        self.pscu._PSCU__healthy = True
        self.pscu.update_lcd()
        assert_equal(self.pscu.lcd.lcd_colour, self.pscu.lcd.GREEN)
        self.pscu._PSCU__healthy = current_health

    def test_update_lcd_unhealthy(self):

        current_health = self.pscu._PSCU__healthy
        self.pscu._PSCU__healthy = False
        self.pscu.update_lcd()
        assert_equal(self.pscu.lcd.lcd_colour, self.pscu.lcd.RED)
        self.pscu._PSCU__healthy = current_health

    def test_update_lcd_with_error(self):

        current_error = self.pscu.get_display_error()
        self.pscu.lcd_display_error = True

        with patch('lpdpower.pscu.LcdDisplay.update') as mock_update:
            self.pscu.update_lcd()
            mock_update.assert_not_called()

        self.pscu.lcd_display_error = current_error

    def test_convert_ad7998_temp(self):

        expected_results = [
            (0.0, -273.15),
            (0.488583, 20.0),
            (0.5, 26.85),
            (1.0, 326.85),
        ]

        for (scaled_adc_val, expected_temp) in expected_results:
            converted_temp = self.pscu.convert_ad7998_temp(scaled_adc_val)
            assert_almost_equal(converted_temp, expected_temp, places=3)

    def test_convert_ad7998_humidity(self):

        expected_results = [
            (0.00, -25.806),
            (0.50, 54.839),
            (0.78, 100.0),
            (1.00, 135.484),
        ]
        for (scaled_adc_val, expected_humidity) in expected_results:
            converted_humidity = self.pscu.convert_ad7998_humidity(scaled_adc_val)
            assert_almost_equal(converted_humidity, expected_humidity, places=3)

    def test_convert_ad7998_fan(self):

        expected_results = [
            (0.0, 0.0),
            (0.5, 1666.667),
            (0.9, 3000.0),
            (1.0, 3333.333),
        ]
        for (scaled_adc_val, expected_speed) in expected_results:
            converted_speed = self.pscu.convert_ad7998_fan(scaled_adc_val)
            assert_almost_equal(converted_speed, expected_speed, places=3)

    def test_convert_ad7998_pump(self):

        expected_results = [
            (0.000, 0.0),
            (0.500, 20.255),
            (0.864, 35.0),
            (1.000, 40.509),
        ]
        for (scaled_adc_val, expected_flow) in expected_results:
            converted_flow = self.pscu.convert_ad7998_pump(scaled_adc_val)
            assert_almost_equal(converted_flow, expected_flow, places=3)

    def test_convert_ad7998_position(self):

        expected_results = [
            (0.000, -1.0 * self.pscu_options['detector_position_offset']),
            (0.5, 0.0),
            (1.000, 70.711 - self.pscu_options['detector_position_offset']),
        ]
        for (scaled_adc_val, expected_posn) in expected_results:
            converted_posn = self.pscu.convert_ad7998_position(scaled_adc_val)
            assert_almost_equal(converted_posn, expected_posn, places=3)

    def test_poll_all_sensors(self):

        self.bus.reset_mock()
        self.bus.read_byte_data.return_value = 0

        self.pscu.poll_all_sensors()

        assert_true(len(self.bus.mock_calls) > 0)
        i2c_methods_called = set()
        i2c_addrs_called = set()
        for name, args, _ in self.bus.mock_calls:
            i2c_methods_called.add(name)
            if len(args):
                i2c_addrs_called.add(args[0])

        expected_i2c_methods = set(['read_word_data', 'read_byte_data', 'write_byte_data'])
        expected_i2c_addrs = set([0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x70])
        assert_equal(i2c_methods_called, expected_i2c_methods)
        assert_equal(i2c_addrs_called, expected_i2c_addrs)

    def test_poll_all_sensors_disables_when_not_armed(self):

        with patch('lpdpower.pscu.MCP23008.input_pins', return_value=[0]*8) as mock_mcp:
            self.pscu.enable_all(True)
            self.pscu.set_armed(False)
            self.pscu.poll_all_sensors()
            assert_equal(self.pscu.get_all_enabled(), False)

    def test_cleanup(self):

        with patch('lpdpower.pscu.LcdDisplay.set_content') as mock_set_content:
            self.pscu.cleanup()
            assert_true(len(mock_set_content.mock_calls) > 0)
            assert_equal(self.pscu.lcd.lcd_colour, self.pscu.lcd.YELLOW)
