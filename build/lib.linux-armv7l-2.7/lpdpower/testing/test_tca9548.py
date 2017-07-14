"""Test TCA9548 class from lpdpower.

Tim Nicholls, STFC Application Engineering Group
"""

import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, call
else:                         # pragma: no cover
    from mock import Mock, call

from nose.tools import *

sys.modules['smbus'] = Mock()
from lpdpower.tca9548 import TCA9548
from lpdpower.i2c_device import I2CDevice, I2CException


class TestTCA9548():

    @classmethod
    def setup_class(cls):
        cls.tca = TCA9548()
        cls.tca_callback = Mock()
        cls.tca.pre_access = cls.tca_callback

    def test_tca_write(self):

        self.tca.write8(0, 123)

    def test_attach_device(self):

        line = 1
        address = 0x20
        device = self.tca.attach_device(line, I2CDevice, address)

        assert_equal(device.address, address)
        assert_true(device in self.tca._attached_devices)
        assert_equal(self.tca._attached_devices[device], line)

    def test_attach_bad_device(self):

        line = 1
        address = 0x20
        class DummyDevice(object):
            def __init__(self, *args, **kwargs):
                pass

        with assert_raises_regexp(
            I2CException, 'must be a type or an instance of I2CDevice or I2CContainer'):
            device = self.tca.attach_device(line, DummyDevice, address)

    def test_remove_device(self):

        device = self.tca.attach_device(1, I2CDevice, 0x20)

        self.tca.remove_device(device)
        assert_true(device not in self.tca._attached_devices)

    def test_remove_missing_device(self):

        device_not_attached = I2CDevice(0x20)

        with assert_raises_regexp(
            I2CException, 'Device %s is not attached to this TCA' % device_not_attached
        ):
            self.tca.remove_device(device_not_attached)

    def test_pre_access_callback_called(self):

        line = 1
        address = 0x20
        device = self.tca.attach_device(line, I2CDevice, address)

        device.write8(0, 1)

        self.tca_callback.assert_called_with(self.tca)

    def test_pre_access_callback_incomplete_detach(self):

        line = 1
        address = 0x20
        device = self.tca.attach_device(line, I2CDevice, address)

        del self.tca._attached_devices[device]

        with assert_raises_regexp(
            I2CException, 'Device %s was not properly detached from the TCA' % device
        ):
            device.write8(0, 1)

    def test_pre_access_selects_tca_line(self):

        device1_line = 1
        device1_address = 0x20
        device2_line = 2
        device2_address = 0x21

        device1 = self.tca.attach_device(device1_line, I2CDevice, device1_address)
        device2 = self.tca.attach_device(device2_line, I2CDevice, device2_address)

        device1.write8(0, 1)
        assert_equal(self.tca._selected_channel, device1_line)

        device2.write8(1, 2)
        assert_equal(self.tca._selected_channel, device2_line)
