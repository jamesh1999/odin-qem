"""Test cases for the Quad class from lpdpower.

Tim Nicholls, STFC Application Engineering
"""

import sys
if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch, call
else:                         # pragma: no cover
    from mock import Mock, patch, call

from nose.tools import *

sys.modules['smbus'] = Mock()
from lpdpower.quad import Quad
from lpdpower.i2c_device import I2CException


class TestQuad():

    @classmethod
    @patch('lpdpower.i2c_device.smbus.SMBus')
    def setup_class(cls, mock_bus):

        cls.mock_bus = mock_bus

        cls.quad = Quad()
        cls.bus = cls.quad.mcp.bus
        cls.bus.read_word_data.return_value = 0

    def test_init(self):

        assert_equal(self.quad.mcp.bus, self.quad.adc_power.bus)
        assert_equal(self.quad.mcp.bus, self.quad.adc_fuse.bus)

    def test_poll(self):

        self.mock_bus.reset_mock()

        self.quad.poll_all_sensors()

        #Build a list of method calls to underlying I2C bus to compare with mocked bus
        method_calls = []

        # Check reads channel enables from GPIO register of MCP
        method_calls.append(call.read_byte_data(0x20, 0x9))

        # Check for each channel, the voltage, current and fuse voltages are read
        for channel in range(self.quad.NUM_CHANNELS):

            method_calls.append(call.write_byte_data(0x22, (0x70 + ((channel + 1) << 4)), 0))
            method_calls.append(call.read_word_data(0x22, 0))

            method_calls.append(call.write_byte_data(0x22, (0x70 + ((channel + 4 + 1) << 4)), 0))
            method_calls.append(call.read_word_data(0x22, 0))

            method_calls.append(call.write_byte_data(0x21, (0x70 + ((channel + 1) << 4)), 0))
            method_calls.append(call.read_word_data(0x21, 0))

        # Check correct calls to read supply voltage ADC channel made
        method_calls.append(call.write_byte_data(0x21, 192, 0))
        method_calls.append(call.read_word_data(0x21, 0))

        # Test method calls equal
        assert_equal(self.bus.method_calls, method_calls)

    def test_get_channel_voltage(self):

        assert_equal(type(self.quad.get_channel_voltage(0)), float)

    def test_get_channel_voltage_bad_channel(self):

        bad_channel = 4
        with assert_raises_regexp(I2CException,
            "{} is not a channel on the Quad. Must be between 0 & 3".format(bad_channel)):
            self.quad.get_channel_voltage(bad_channel)

    def test_get_channel_current(self):

        assert_equal(type(self.quad.get_channel_current(0)), float)

    def test_get_channel_current_bad_channel(self):

        bad_channel = 4
        with assert_raises_regexp(I2CException,
            "{} is not a channel on the Quad. Must be between 0 & 3".format(bad_channel)):
            self.quad.get_channel_current(bad_channel)

    def test_get_channel_fuse_voltage(self):

        assert_equal(type(self.quad.get_fuse_voltage(0)), float)

    def test_get_channel_fuse_voltage_bad_channel(self):

        bad_channel = 4
        with assert_raises_regexp(I2CException,
            "{} is not a channel on the Quad. Must be between 0 & 3".format(bad_channel)):
            self.quad.get_fuse_voltage(bad_channel)

    def test_get_channel_fuse_blown(self):

        assert_equal(type(self.quad.get_fuse_blown(0)), bool)

    def test_get_channel_fuse_blown_bad_channel(self):

        bad_channel = 4
        with assert_raises_regexp(I2CException,
            "{} is not a channel on the Quad. Must be between 0 & 3".format(bad_channel)):
            self.quad.get_fuse_blown(bad_channel)

    def test_get_channel_fet_failed(self):

        assert_equal(type(self.quad.get_fet_failed(0)), bool)

    def test_get_channel_fet_failed_bad_channel(self):

        bad_channel = 4
        with assert_raises_regexp(I2CException,
            "{} is not a channel on the Quad. Must be between 0 & 3".format(bad_channel)):
            self.quad.get_fet_failed(bad_channel)

    def test_get_channel_enable(self):

        assert_equal(type(self.quad.get_enable(0)), bool)

    def test_get_channel_enable_bad_channel(self):

        bad_channel = 4
        with assert_raises_regexp(I2CException,
            "{} is not a channel on the Quad. Must be between 0 & 3".format(bad_channel)):
            self.quad.get_enable(bad_channel)

    def test_get_supply_voltage(self):

        assert_equal(type(self.quad.get_supply_voltage()), float)

    def test_set_enable_with_change(self):

        channel = 3
        enabled = not self.quad.get_enable(channel)

        self.mock_bus.reset_mock()
        self.quad.set_enable(channel, enabled)

        method_calls = []

        # Check MCP has appropriate enable toggled low-high-low
        method_calls.append(call.write_byte_data(0x20, 9, 0))
        method_calls.append(call.write_byte_data(0x20, 9, 1 << channel))
        method_calls.append(call.write_byte_data(0x20, 9, 0))

        assert_equal(self.bus.method_calls, method_calls)

    def test_set_enable_no_change(self):

        channel = 2
        enabled = self.quad.get_enable(channel)

        self.mock_bus.reset_mock()
        self.quad.set_enable(channel, enabled)

        assert_equal(len(self.bus.method_calls), 0)

    def test_enable_bad_channel(self):

        bad_channel = 4
        with assert_raises_regexp(I2CException,
            "{} is not a channel on the Quad. Must be between 0 & 3".format(bad_channel)):
            self.quad.set_enable(bad_channel, False)

    def test_fuse_blown(self):

        read_scaled_inputs = [0.0, 0.0, 0.0125] * self.quad.NUM_CHANNELS + [0.6]
        fuse_blown = self._read_fuse_blown(read_scaled_inputs)
        assert_equal(fuse_blown, [True] * self.quad.NUM_CHANNELS)

    def test_fuse_not_blown(self):

        read_scaled_inputs = [0.0, 0.0, 0.576] * self.quad.NUM_CHANNELS + [0.6]
        fuse_blown = self._read_fuse_blown(read_scaled_inputs)
        assert_equal(fuse_blown, [False] * self.quad.NUM_CHANNELS)

    def _read_fuse_blown(self, read_scaled_inputs):
        with patch('lpdpower.quad.AD7998.read_input_scaled', side_effect=read_scaled_inputs):
            self.quad.poll_all_sensors()
            fuse_blown = [
                self.quad.get_fuse_blown(chan) for chan in range(self.quad.NUM_CHANNELS)
            ]
        return fuse_blown

    def test_fet_failed(self):

        read_scaled_inputs = [0.6, 0.0, 0.576] * self.quad.NUM_CHANNELS + [0.6]
        channel_enables = [True, False, True, False]
        fet_failed = self._read_fet_failed(read_scaled_inputs, channel_enables)
        assert_equal(fet_failed, [not enable for enable in channel_enables])

    def test_fet_not_failed(self):

        read_scaled_inputs = [0.05625, 0.0, 0.6] + [0.6, 0.0, 0.6]*3 + [0.6]
        channel_enables = [False, True, True, True]
        fet_failed = self._read_fet_failed(read_scaled_inputs, channel_enables)
        assert_equal(fet_failed, [False]*self.quad.NUM_CHANNELS)

    def _read_fet_failed(self, read_scaled_inputs, channel_enables):

        with patch('lpdpower.quad.AD7998.read_input_scaled', side_effect=read_scaled_inputs):
            with patch('lpdpower.quad.MCP23008.input_pins',  return_value=channel_enables):
                self.quad.poll_all_sensors()
                fet_failed = [
                    self.quad.get_fet_failed(chan) for chan in range(self.quad.NUM_CHANNELS)
                ]

        return fet_failed
