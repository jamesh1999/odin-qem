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
from lpdpower.mcp23008 import MCP23008

class TestMCP23008():
    
    @classmethod
    def setup_class(cls):
        
        cls.address = 0x20
        cls.mcp23008 = MCP23008(cls.address)
        
        # Override the internal register buffers so that subsequent access calls have
        # sensible I2C access values, otherwise they contain references to the mocked
        # smbus calls
        cls.mcp23008._MCP23008__iodir = 0
        cls.mcp23008._MCP23008__gppu = 0
        cls.mcp23008._MCP23008__gpio = 0
        
        # Explictly mock underlying I2C byte read (called by I2CDevice.readU8) to return value
        cls.mcp23008.bus.read_byte_data.return_value = 0
        
    def test_registers_read(self):
         
        self.mcp23008.bus.read_byte_data.assert_any_call(self.address, MCP23008.IODIR)
        self.mcp23008.bus.read_byte_data.assert_any_call(self.address, MCP23008.GPPU)
        self.mcp23008.bus.read_byte_data.assert_any_call(self.address, MCP23008.GPIO)
         
    def _get_iodir_buffer(self):
         
        return self.mcp23008._MCP23008__iodir
    
    def _get_gppu_buffer(self):
        
        return self.mcp23008._MCP23008__gppu
    
    def _get_gpio_buffer(self):
        
        return self.mcp23008._MCP23008__gpio
     
    def test_setup_in(self):
         
        pin = 3
        direction = MCP23008.IN
        expected_iodir = self._get_iodir_buffer() | 1 << pin
         
        self.mcp23008.setup(pin, direction)
        
        self.mcp23008.bus.write_byte_data.assert_called_with(
          self.address, MCP23008.IODIR, expected_iodir
        )
        
    def test_setup_out(self):
        
        pin = 4
        direction = MCP23008.OUT
        expected_iodir = self._get_iodir_buffer() & ~(1 << pin)
        
        self.mcp23008.setup(pin, direction)
        
        self.mcp23008.bus.write_byte_data.assert_called_with(
             self.address, MCP23008.IODIR, expected_iodir
        )
        
    def test_setup_bad_direction(self):
        
        pin = 7
        direction = 1234
        
        with assert_raises_regexp(
            ValueError, 'expected a direction of MCP23008.IN or MCP23008.OUT'):
            self.mcp23008.setup(pin, direction)
     
            
    def test_pullup_enable(self):
        
        pin = 1
        expected_gppu = self._get_gppu_buffer() | (1 << pin)
        
        self.mcp23008.pullup(pin, 1)
        self.mcp23008.bus.write_byte_data.assert_called_with(
            self.address, MCP23008.GPPU, expected_gppu
        )
    
    def test_pullup_disable(self):
        
        pin = 1
        expected_gppu = self._get_gppu_buffer() & ~(1 << pin)
        
        self.mcp23008.pullup(pin, 0)
        self.mcp23008.bus.write_byte_data.assert_called_with(
            self.address, MCP23008.GPPU, expected_gppu
        )
        
    def test_input(self):
        
        pin = 1
        val = self.mcp23008.input(pin)
        self.mcp23008.bus.read_byte_data.assert_called_with(
            self.address, MCP23008.GPIO)
        
    def test_input_pins(self):
        
        pins = [1, 3, 5, 7]
        
        pin_vals = self.mcp23008.input_pins(pins)
        
        assert_equal(len(pins), len(pin_vals))
        self.mcp23008.bus.read_byte_data.assert_called_with(
            self.address, MCP23008.GPIO
        )
        
    def test_output_high(self):
        
        pin = 3
        val = 1
        expected_gpio = self._get_gpio_buffer() | (1 << pin)
        
        self.mcp23008.output(pin, val)
        self.mcp23008.bus.write_byte_data.assert_called_with(
            self.address, MCP23008.GPIO, expected_gpio
        )
        
    def test_output_low(self):
        
        pin = 4
        val = 0
        expected_gpio = self._get_gpio_buffer() & ~(1 << pin)
        
        self.mcp23008.output(pin, val)
        self.mcp23008.bus.write_byte_data.assert_called_with(
            self.address, MCP23008.GPIO, expected_gpio
        )
        
    def test_output_pins(self):
        
        pins = {1:0, 3:1, 2:0, 5:1}
        expected_gpio = self._get_gpio_buffer()
        
        for pin, val in pins.items():
            if val:
                expected_gpio |= (1<<pin)
            else:
                expected_gpio &= ~(1<<pin)
        
        self.mcp23008.output_pins(pins)
        self.mcp23008.bus.write_byte_data.assert_called_with(
            self.address, MCP23008.GPIO, expected_gpio
        )
        
    def test_disable_outputs(self):
        
        expected_gpio = 0
        self.mcp23008.disable_outputs()
        self.mcp23008.bus.write_byte_data.assert_called_with(
            self.address, MCP23008.GPIO, expected_gpio
        )
        
        