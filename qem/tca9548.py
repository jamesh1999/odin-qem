"""TCA9548 - device access class for the TCA9548 I2C bus multiplexer.

This class implements support for the TCA9548 I2C bus multiplexer. Designed to
be used in conjunction with the the I2CDevice and I2CContainer classes, it allows
the TCA output channel to be transpartently selected for any access to a device
attached to an instance of this class, through a callback mechanism.

James Hogge, STFC Application Engineering Group.
"""

from i2c_device import I2CDevice, I2CException
from i2c_container import I2CContainer


class TCA9548(I2CDevice):
    """TCA9548 class.

    This class implements support for the ICA9548 I2C device, allowing other
    instances of I2CDevice or I2CContainer classes to be attached to TCA instance,
    allowing the appropriate output bus to be selected transparently for each access.
    """

    def __init__(self, address=0x70, allowMultiple=True, **kwargs):
        """Initialise the the TCA9548 device.

        :param address: address of TCA9548 on the I2C bus
        :param kwargs: keyword arguments to be passed to underlying I2CDevice
        """
        # Initialise the I2CDevice superclass instance
        I2CDevice.__init__(self, address, **kwargs)

        # Clear attached devices and currently enabled channel
        self._attached_devices = {}
        self._selected_channel = None

        # Disable any already enabled devices by clearing output bus selection
        self.write8(0, 0)

    def __device_callback(self, device):
        """Internal device callback method.

        This method is called internally to allow attached devices to transparently
        select the appropriate TCA multiplexer channel. The TCA is accessed only if the
        device being accessed is not on the currently selected channel.

        :param device: the device for which the callback is being called.
        """
        # Check the device is attached, otherwise raise an exception
        if device not in self._attached_devices:
            raise I2CException('Device %s was not properly detached from the TCA' % device)

        # Call own callback (for chained TCAs)
        if self.pre_access is not None:
            self.pre_access(self)

        # Skip accessing the TCA if the current channel is already selected
        if self._attached_devices[device] == self._selected_channel:
            return

        self._selected_channel = self._attached_devices[device]

        # Write to the TCA to select the correct channel
        self.write8(0, 1 << self._attached_devices[device])

    def attach_device(self, channel, device, *args, **kwargs):
        """Attach an I2C device to the TCA multiplexer.

        This method attaches a device to the TCA multiplexer on a specified TCA
        channel. The device must be an instance of, or type, derived from I2CDevice or
        I2CContainer. If a class is passed, a device of the appropriate type is
        initialised and returned.

        :param channel: TCA channel on which the device is present
        :param device: class or instance to attach to the TCA
        :param args: positional arguments to pass to device initialisation
        :param kwargs: keyword arguments to pass to device initialisation
        """
        # If passed a callable type for a device, initialise it having selected the appropriate
        # TCA channel
        if callable(device):
            self.write8(0, 1 << channel)
            self._selected_channel = channel
            device = device(*args, **kwargs)

        # Raise an exception if the device is not and I2CDevice or I2CContainer instance
        if not isinstance(device, I2CDevice) and not isinstance(device, I2CContainer):
            raise I2CException(
                'Device %s must be a type or an instance of I2CDevice or I2CContainer' % device)

        # Add device to attached devices and set its pre-access callback
        self._attached_devices[device] = channel
        device.pre_access = self.__device_callback
        return device

    def remove_device(self, device):
        """Remove an I2C device from the TCA multiplexer.

        This method removes an attached device from the TCA multiplexer and clears the
        device callback to prevent TCA access for that device.

        :param device: Device to remove from the TCA.
        """
        if device not in self._attached_devices:
            raise I2CException('Device %s is not attached to this TCA' % device)

        self._attached_devices.pop(device)
        device.pre_access = None
