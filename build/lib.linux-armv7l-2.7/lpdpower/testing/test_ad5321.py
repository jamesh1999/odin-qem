"""Test cases for the AD5321 class from lpdpower.

Tim Nicholls, STFC Application Engineering
"""
 
import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, call
else:                         # pragma: no cover
    from mock import Mock, call

from nose.tools import *

sys.modules['smbus'] = Mock()
from lpdpower.ad5321 import AD5321
from lpdpower.i2c_device import I2CDevice, I2CException

class TestAD5321():
    
    @classmethod
    def setup_class(cls):
        
        cls.address = 0xc
        cls.ad5321 = AD5321(cls.address)
        
    
    def test_set_output(self):
        
        # Output = 0.75 FS = 3072 ADU, = MSB 0xC, LSB 0x0
        
        output = 0.75
        msb = 0xc
        lsb = 0
        self.ad5321.set_output_scaled(output)
        self.ad5321.bus.write_byte_data.assert_called_with(self.address, msb, lsb)
        
    def test_set_output_full_scale(self):
        
        output = 1.0
        msb = 0xF
        lsb = 0xFF
        
        self.ad5321.set_output_scaled(output)
        self.ad5321.bus.write_byte_data.assert_called_with(self.address, msb, lsb)
        
    def test_set_output_lt_zero(self):
        
        output = -0.75
        
        with assert_raises_regexp(I2CException, 'Illegal output value {} specified'.format(output)):
            self.ad5321.set_output_scaled(output)
            
            
    def test_set_output_gt_one(self):
        
        output = 1.1
        
        with assert_raises_regexp(I2CException, 'Illegal output value {} specified'.format(output)):
            self.ad5321.set_output_scaled(output)

    def test_read_value(self):
        
        # Patch to return value of 0.5 = 2048 ADU = 0x0800, byte swapped to 0x0008
        self.ad5321.bus.read_word_data.return_value = 0x0008
        
        value = self.ad5321.read_value_scaled()
        assert_equals(value, 0.5)
            