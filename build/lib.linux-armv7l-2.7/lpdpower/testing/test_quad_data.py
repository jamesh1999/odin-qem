"""Test QuadData and ChannelData classes from lpdpower.

Tim Nicholls, STFC Application Engineering Group
"""

import sys
if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch, call
else:                         # pragma: no cover
    from mock import Mock, patch, call

from nose.tools import *

sys.modules['smbus'] = Mock()
from lpdpower.quad import Quad
from lpdpower.quad_data import ChannelData, QuadData

class TestChannelData():

    @classmethod
    @patch('lpdpower.i2c_device.smbus.SMBus')
    def setup_class(cls, mock_bus):
        cls.quad = Quad()
        cls.channel = 1
        cls.channel_data = ChannelData(cls.quad, cls.channel)

    def test_channel_voltage_get(self):
        response = self.channel_data.param_tree.get('voltage')
        assert_equal(type(response['voltage']), float)

    def test_channel_current_get(self):
        response = self.channel_data.param_tree.get('current')
        assert_equal(type(response['current']), float)

    def test_channel_fuse_get(self):
        response = self.channel_data.param_tree.get('fusevoltage')
        assert_equal(type(response['fusevoltage']), float)

    def test_channel_fuse_blown(self):
        response = self.channel_data.param_tree.get('fuseblown')
        assert_equal(type(response['fuseblown']), bool)

    def test_channel_fet_failed(self):
        response = self.channel_data.param_tree.get('fetfailed')
        assert_equal(type(response['fetfailed']), bool)

    def test_channel_enable_get(self):
        response = self.channel_data.param_tree.get('enabled')
        assert_equal(type(response['enabled']), bool)

    def test_channel_enable_set(self):
        enable = True
        # Force underlying Quad enable value so test can validate call tree
        self.quad._Quad__channel_enable[self.channel] = enable
        self.channel_data.param_tree.set('enabled', enable)
        response = self.channel_data.param_tree.get('enabled')
        assert_equal(response['enabled'], enable)

class TestQuadData():

    @classmethod
    @patch('lpdpower.i2c_device.smbus.SMBus')
    def setup_class(cls, mock_bus):
        cls.quad = Quad()
        cls.quad_data = QuadData(quad=cls.quad)

    @patch('lpdpower.i2c_device.smbus.SMBus')
    def test_quad_data_no_quad_arg(self, mock_bus):
        qd = QuadData()
        assert(qd.quad is not None)

    def test_quad_supply_voltage_get(self):
        response = self.quad_data.param_tree.get('supply')
        assert_equal(type(response['supply']), float)
