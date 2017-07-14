"""Test cases for the I2CTContainer class from lpdpower.

Tim Nicholls, STFC Application Engineering Group
"""

import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, call
else:                         # pragma: no cover
    from mock import Mock, call

from nose.tools import *

sys.modules['smbus'] = Mock()
from lpdpower.i2c_device import I2CDevice, I2CException
from lpdpower.i2c_container import I2CContainer

class TestI2CContainer():

    @classmethod
    def setup_class(cls):
        cls.container = I2CContainer()
        cls.container.pre_access = Mock()

    def test_attach_new_device(self):

        device = self.container.attach_device(I2CDevice, 0x20)
        assert_true(device in self.container._attached_devices)

    def test_attach_existing_device(self):

        device = I2CDevice(0x21)
        self.container.attach_device(device)
        assert_true(device in self.container._attached_devices)

    def test_attach_bad_device(self):

        class DummyDevice(object):
            def __init__(self, *args, **kwargs):
                pass

        with assert_raises_regexp(
            I2CException, 'must be of type or an instance of I2CDevice or I2CContainer'
        ):
            self.container.attach_device(DummyDevice, 0x20)

    def test_device_callback_called(self):

        device = self.container.attach_device(I2CDevice, 0x22)
        device.write8(0, 1)
        self.container.pre_access.assert_called_with(self.container)

    def test_remove_device(self):

        device = self.container.attach_device(I2CDevice, 0x23)

        self.container.remove_device(device)
        assert_true(device not in self.container._attached_devices)

    def test_remove_missing_device(self):

        device = I2CDevice(0x24)

        with assert_raises_regexp(
            I2CException, 'Device %s was not attached to this I2CContainer' % device
        ):
            self.container.remove_device(device)
