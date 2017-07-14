"""MCP23008 - device class for the MCP23008 I2C GPIO extender.

This class implements support for the MCP23008 I2C GPIO extender device. It is derived from
the Adafruit implementation available at:

https://raw.githubusercontent.com/adafruit/Adafruit_Python_GPIO/master/Adafruit_GPIO/MCP230xx.py

This class allows the MCP23008 IO functionality to be operated, including reading/writing all input
pins, setting IO direction and enabling pullups.

James Hogge, STFC Application Engineering Group.
"""

from i2c_device import I2CDevice


class MCP23008(I2CDevice):
    """MCP23008 class.

    This class implements support for the MCP23008 I2C GPIO extender device.
    """

    # Addresses of MCP23008 registers for IO direction, pullups and r/w operations
    IODIR = 0x00
    GPPU = 0x06
    GPIO = 0x09

    # Definition of input and output modes
    IN = 0
    OUT = 1

    # Definition of low and high states
    LOW = 0
    HIGH = 1

    def __init__(self, address=0x20, **kwargs):
        """Initialise the MCP23008 device.

        :param address: address of the MCP23008 deviceon the I2C bus
        :param kwargs: keyword arguments to be passed to the underlying I2CDevice
        """
        # Initialise the I2CDevice superclass instance
        I2CDevice.__init__(self, address, **kwargs)

        # Synchronise local buffered register values with state of device
        self.__iodir = self.readU8(self.IODIR)
        self.__gppu = self.readU8(self.GPPU)
        self.__gpio = self.readU8(self.GPIO)

    def setup(self, pin, direction):
        """Set the IO direction state of a pin.

        This method sets the IO direction for a given pin, i.e. MCP23008.IN or MCP23008.OUT.

        :param pin: pin to set IO direction for
        :param direction: direction to set
        """
        # Set direction in register buffer value
        if direction == self.IN:
            self.__iodir |= 1 << pin
        elif direction == self.OUT:
            self.__iodir &= ~(1 << pin)
        else:
            raise ValueError(
                "MCP23008::setup() expected a direction of MCP23008.IN or MCP23008.OUT"
            )

        # Write the state to the IODIR register
        self.write8(self.IODIR, self.__iodir)

    def pullup(self, pin, enabled):
        """Set the pullup state of a pin.

        This method allows the pullup state of a pin on the MCP23008 to be set.

        :param pin: set to set pullup state for
        :param enabled: pullup state to set (e.g 0, 1, True or False)
        """
        # Set state in register buffer value
        if enabled:
            self.__gppu |= 1 << pin
        else:
            self.__gppu &= ~(1 << pin)

        # Write the GPPU register on the device
        self.write8(self.GPPU, self.__gppu)

    def input(self, pin):
        """Get the input value on a pin.

        This method returns the state of the input on a given pin of the MCP23008 device.

        :param pin: pin to read
        :return bool state of pin
        """
        return self.input_pins([pin])[0]

    def input_pins(self, pins):
        """Get the input state for a list of input pins.

        This method returns the state of the inputs of a list of pins on the device.

        :param pins: list of pins to return input state for
        :return list of bool states of pins requested
        """
        # Read the GPIO register
        buff = self.readU8(self.GPIO)

        # Buils and return a list of input states for the requested pins
        return [bool(buff & (1 << pin)) for pin in pins]

    def output(self, pin, value):
        """Set the output state of a pin.

        This method sets the output state of a single pin on the MCP23008 device.

        :param pin: pin to set output state for
        :param value: value to set (MCP23008.OUT or MCP23008.IN)
        """
        self.output_pins({pin: value})

    def output_pins(self, pins):
        """Set the output state of multiple pins.

        This method sets the output state for multiple pins on the MCP23008 device.

        :param pins: dict of pins and states e.g. {0:MCP23008.OUT, 1:MCP230008.IN}
        """
        # Iterate over pins and set appropriate bit in GPIO register buffer
        for pin, val in pins.items():
            if val:
                self.__gpio |= 1 << pin
            else:
                self.__gpio &= ~(1 << pin)

        # Write the state to the GPIO register
        self.write8(self.GPIO, self.__gpio)

    def disable_outputs(self):
        """Set all outputs of the MCP23008 low.

        This method sets all output pins of the MCP23008 low.
        """
        self.__gpio = 0
        self.write8(self.GPIO, self.__gpio)
