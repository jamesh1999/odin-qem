"""Test cases for the I2CTContainer class from lpdpower.

Tim Nicholls, STFC Application Engineering Group
"""

import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, MagicMock, call
else:                         # pragma: no cover
    from mock import Mock, MagicMock, call

from nose.tools import *
from functools import partial

smbus_mock = MagicMock()
sys.modules['smbus'] = smbus_mock

from lpdpower.i2c_device import I2CDevice, I2CException

class dummy_cm():
    def __enter__(self):
        return None
    def __exit__(self, exc_type, exc_value, traceback):
        return False

class TestI2CDevice(object):

    EXC_MODE_NONE, EXC_MODE_TRAP, EXC_MODE_RAISE = range(3)
    EXC_MODES = [EXC_MODE_NONE, EXC_MODE_TRAP, EXC_MODE_RAISE]
    EXC_MODE_NAME = ['exception_mode_none', 'exception_mode_trap', 'exception_mode_raise']

    @classmethod
    def setup_class(cls):

        cls.device_busnum = 1
        cls.device_address = 0x70
        cls.device_debug = True
        cls.device = I2CDevice(cls.device_address, cls.device_busnum, cls.device_debug)
        cls.device.pre_access = Mock()

    def test_device_init(self):

        assert_equal(self.device_address, self.device.address)
        assert_equal(self.device_debug, self.device.debug)

    def test_pre_access_called(self):

        self.device.write8(1, 20)
        self.device.pre_access.assert_called_with(self.device)

    def test_enable_exceptions(self):

        self.device.enable_exceptions()
        assert_true(self.device._enable_exceptions)

    def test_disable_exceptions(self):

        self.device.disable_exceptions()
        assert_false(self.device._enable_exceptions)

    def test_generator(self):

        for (method, smbus_method, args, rc) in [
            ('write8', 'write_byte_data', (1, 0x70), None),
            ('write16', 'write_word_data', (2, 0x12), None),
            ('writeList', 'write_i2c_block_data', (3, [1, 2, 3, 4]), None),
            ('readU8', 'read_byte_data', (4,), 0xab),
            ('readS8', 'read_byte_data', (5,), -127),
            ('readU16', 'read_word_data', (6,), 0x1234),
            ('readS16', 'read_word_data', (7,), 0x4567),
            ('readList', 'read_i2c_block_data', (8, 4), [1000, 1001, 1002, 1003])
        ]:
            for exc_mode in self.EXC_MODES:
                test_func = partial(self._test_device_access, method, smbus_method, exc_mode, args, rc)
                test_func.description = '{}.{}.test_{}_{}'.format(
                    __name__, type(self).__name__, method, self.EXC_MODE_NAME[exc_mode]
                )
                yield (test_func, )

    def _test_device_access(self, method, smbus_method, exc_mode, args, exp_rc):

        cached_side_effect = getattr(self.device.bus, smbus_method).side_effect

        if exc_mode == self.EXC_MODE_NONE:
            side_effect = None
            exc_enable = False
            getattr(self.device.bus, smbus_method).return_value = exp_rc
        elif exc_mode == self.EXC_MODE_TRAP:
            side_effect = IOError('mocked error')
            exc_enable = False
            exp_rc = I2CDevice.ERROR
        elif exc_mode == self.EXC_MODE_RAISE:
            side_effect = IOError('mocked error')
            exc_enable = True
        else:
            raise Exception('Illegal exception test mode {}'.format(exc_mode))

        getattr(self.device.bus, smbus_method).side_effect = side_effect
        self.device.enable_exceptions() if exc_enable else self.device.disable_exceptions()

        rc = None

        with assert_raises_regexp(I2CException, 'error from device') if exc_enable else dummy_cm():
            rc = getattr(self.device, method)(*args)
            assert_equal(rc, exp_rc)

        getattr(self.device.bus, smbus_method).side_effect = cached_side_effect
