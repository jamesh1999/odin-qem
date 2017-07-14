"""I2CDevice - I2C device access class.

This class implements I2C device access primitives. Derived from the Adafruit_I2C class
available at:
https://github.com/adafruit/adafruit-beaglebone-io-python/blob/master/Adafruit_I2C.py

but refactored to allow pre-access callbacks to be called for each access and to suppress
error print calls and replace with proper exception raising.

James Hogge, Tim Nicholls, STFC Application Engineering Group.
"""

import smbus
import logging


class I2CException(Exception):
    """Simple I2C exception class for wrapping underlying access errors."""

    pass


def call_pre_access(func):
    """Call pre-access decorator for I2CDevice access methods.

    Allows pre-access attribute to be called if defined on I2C device accessors.
    """
    def wrapper(_self, *args, **kwargs):
        if _self.pre_access is not None and callable(_self.pre_access):
            _self.pre_access(_self)
        return func(_self, *args, **kwargs)
    return wrapper


class I2CDevice(object):
    """I2CDevice class.

    This class implements the I2C device access interface, providing read and write
    access primitives for a range of byte and word-level operations. A pre_access
    attribute allows an external callback to be executed on each access to, e.g. allow
    a bus multiplexer to be controlled transparently.
    """

    _enable_exceptions = False

    ERROR = -1

    @classmethod
    def enable_exceptions(cls):
        """Enable I2CDevice exceptions."""
        logging.debug("Enabling I2CDevice exceptions")
        cls._enable_exceptions = True

    @classmethod
    def disable_exceptions(cls):
        """Disable I2CDevice exceptions."""
        logging.debug("Disabling I2CDevice exceptions")
        cls._enable_exceptions = False

    def __init__(self, address, busnum=-1, debug=False):
        """Initialise the I2CDevice object.

        :param address: address of device on I2C bus
        :param busnum: number of the I2C bus on the host device
        :param debug: enable debug access logging
        """
        self.address = address
        self.bus = smbus.SMBus(busnum if busnum >= 0 else 2)
        self.debug = debug
        self.pre_access = None

    def handle_error(self, access_name, register, error):
        """Handle exception condition for I2CDevice.

        If exceptions are enabled, raise an exception based on the passed arguments,
        otherwise, log an message if debugging is turned on and return an error value.
        """
        err_msg = 'I2C {} error from device {:#x} register {:#x}: {}'.format(
             access_name, self.address, register, error
        )

        if self._enable_exceptions:
            raise I2CException(err_msg)

        if self.debug:
            logging.debug(err_msg)

        return I2CDevice.ERROR

    @call_pre_access
    def write8(self, reg, value):
        """"Write an 8-bit value to the specified register/address."""
        try:
            self.bus.write_byte_data(self.address, reg, value)
            if self.debug:
                logging.debug("I2C: Wrote 0x%02X to register 0x%02X" % (value, reg))
        except IOError as err:
            return self.handle_error('write8', reg, err)

    @call_pre_access
    def write16(self, reg, value):
        """Write a 16-bit value to the specified register/address pair."""
        try:
            self.bus.write_word_data(self.address, reg, value)
            if self.debug:
                logging.debug("I2C: Wrote 0x%02X to register pair 0x%02X,0x%02X" %
                              (value, reg, reg+1))
        except IOError as err:
            return self.handle_error('write16', value, err)

    @call_pre_access
    def writeList(self, reg, list):
        """Write an array of bytes using I2C format."""
        try:
            self.bus.write_i2c_block_data(self.address, reg, list)
            if self.debug:
                logging.debug("I2C: Wrote list to register 0x%02X:" % reg)
                logging.debug(list)
        except IOError as err:
            return self.handle_error('writeList', reg, err)

    @call_pre_access
    def readList(self, reg, length):
        """Read a list of bytes from the I2C device."""
        try:
            results = self.bus.read_i2c_block_data(self.address, reg, length)
            if self.debug:
                logging.debug("I2C: Device 0x%02X returned the following from reg 0x%02X" %
                              (self.address, reg))
                logging.debug(results)
            return results
        except IOError as err:
            return self.handle_error('readList', reg, err)

    @call_pre_access
    def readU8(self, reg):
        """Read an unsigned byte from the I2C device."""
        try:
            result = self.bus.read_byte_data(self.address, reg)
            if self.debug:
                logging.debug("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" %
                              (self.address, result & 0xFF, reg))
            return result
        except IOError as err:
            return self.handle_error('readU8', reg, err)

    @call_pre_access
    def readS8(self, reg):
        """Read a signed byte from the I2C device."""
        try:
            result = self.bus.read_byte_data(self.address, reg)
            result = (result - 256) if result > 127 else result
            if self.debug:
                logging.debug("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" %
                              (self.address, result & 0xFF, reg))
            return result
        except IOError as err:
            return self.handle_error('readS8', reg, err)

    @call_pre_access
    def readU16(self, reg):
        """Read an unsigned 16-bit value from the I2C device."""
        try:
            result = self.bus.read_word_data(self.address, reg)
            if (self.debug):
                logging.debug("I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" %
                              (self.address, result & 0xFFFF, reg))
            return result
        except IOError as err:
            return self.handle_error('readU16', reg, err)

    @call_pre_access
    def readS16(self, reg):
        """"Read a signed 16-bit value from the I2C device."""
        try:
            result = self.bus.read_word_data(self.address, reg)
            if (self.debug):
                logging.debug("I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" %
                              (self.address, result & 0xFFFF, reg))
            return result
        except IOError as err:
            return self.handle_error('readS16', reg, err)
