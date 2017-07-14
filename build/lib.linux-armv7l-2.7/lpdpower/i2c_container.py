"""I2CContainer - container class for I2CDevice instances.

This class allows I2CDevice instances to be group together into logical units, e.g.
to associate devices belonging to a particular bus or unit together. A callback
mechanism allows a pre-access method to be called for all devices in the container, for
instance to allow a bus multiplexer channel to be selected.

James Hogge, STFC Application Engineering Group
"""
from lpdpower.i2c_device import I2CDevice, I2CException


class I2CContainer(object):
    """I2CContainer class.

    This class implements an I2C container object, allowing other I2CDevice and I2CContainer
    instances to be grouped together, allowing the appropriate pre-access callback to be
    used.
    """

    def __init__(self):
        """Initialise the I2CContainer."""
        self._attached_devices = []
        self.pre_access = None

    def _device_callback(self, device):
        """Internal device callback method.

        This method calls the pre-access function associated with this instance.

        :param device: device callback is being accessed from.
        """
        if self.pre_access is not None:
            self.pre_access(self)

    def attach_device(self, device, *args, **kwargs):
        """Attach an I2C device to the container.

        This method attaches a device to the container. The device must be an instance of,
        or type, derived from I2CDevice or I2CContainer. If a class is passed, a device of the
        appropriate type is initialised and returned.

        :param device: class or instance to attach to the TCA
        :param args: positional arguments to pass to device initialisation
        :param kwargs: keyword arguments to pass to device initialisation
        """
        # If passed a callable type for a device, initialise it with the appropriate arguments
        if callable(device):
            if self.pre_access is not None:
                self.pre_access(self)
            device = device(*args, **kwargs)

        # Raise an exception if the device is not and I2CDevice or I2CContainer instance
        if not isinstance(device, I2CDevice) and not isinstance(device, I2CContainer):
            raise I2CException(
                'Device %s must be of type or an instance of I2CDevice or I2CContainer' % device)

        # Append device to attached devices, set its callback and return
        self._attached_devices.append(device)
        device.pre_access = self._device_callback
        return device

    def remove_device(self, device):
        """Remove an I2C device from the container.

        This method removes an attached device from the container and clears the
        device callback to prevent it being called for that device.

        :param device: Device to remove from the device.
        """
        if device in self._attached_devices:
            self._attached_devices.remove(device)
            device.pre_access = None
        else:
            raise I2CException('Device %s was not attached to this I2CContainer' % device)
