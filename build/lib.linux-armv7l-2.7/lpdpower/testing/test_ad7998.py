"""Test cases for the AD7998 class from lpdpower.

Tim Nicholls, STFC Application Engineering
"""
 
import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock
else:                         # pragma: no cover
    from mock import Mock

from nose.tools import *

sys.modules['smbus'] = Mock()
from lpdpower.ad7998 import AD7998
from lpdpower.i2c_device import I2CException

class TestAD7998():
    
    @classmethod
    def setup_class(cls):
        
        cls.address = 0x20
        cls.ad7998 = AD7998(cls.address)
        
    def set_read_return_value(self, value):
        
        self.ad7998.bus.read_word_data.return_value = value
        
    def test_init_sets_cycle_register(self):
    
        self.ad7998.bus.write_byte_data.assert_called_with(self.address, 3, 1)
        
    def test_read_raw(self):
        
        channel = 1
        self.set_read_return_value(0x3412)
        
        val = self.ad7998.read_input_raw(channel)
        assert_equal(val, 0x1234)
        
    def test_read_raw_illegal_channel(self):
        
        channel = 12
        with assert_raises_regexp(I2CException, "Illegal channel {} requested".format(channel)):
            val = self.ad7998.read_input_raw(channel)
            
            
    def test_read_input_scaled_fs(self):
        
        channel = 1
        self.set_read_return_value(0xff1f)
        
        val = self.ad7998.read_input_scaled(channel)
        assert_equal(val, 1.0)
        
    def test_read_input_scaled_zero(self):
        
        channel = 2
        self.set_read_return_value(0x0020)
        
        val = self.ad7998.read_input_scaled(channel)
        assert_equal(val, 0.0)
        
    def test_read_input_scaled_midscale(self):
        
        channel = 7
        self.set_read_return_value(0x0078)
        
        val = self.ad7998.read_input_scaled(channel)
        assert_equal(val, 2048.0/4095.0)