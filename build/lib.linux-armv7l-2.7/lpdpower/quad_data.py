"""quad_data - Quad data container classes.

This module implements QuadData and associated classes needed to represent the
parameter data for the LPD power supply Quad boxes.

James Hogge, STFC Application Engineering Group.
"""
from odin.adapters.parameter_tree import ParameterTree
from lpdpower.quad import Quad


class ChannelData(object):
    """Data container for a Quad output channel.

    This class implements a data container and parameter tree for a single
    output channel of an LPD Quad box, allowing all channel parameters to be
    read and the output enable to be controlled.
    """

    def __init__(self, quad, channel_idx):
        """Initialise the data container for a Quad channel.

        This constructor initialises the data container for a LPD Quad output
        channel, creating the parameter tree and associating it with a specified
        quad and channel.

        :param quad: the quad box for this channel
        :param channel_idx: channel index on the specified quad.
        """
        self.quad = quad
        self.channel_idx = channel_idx

        self.param_tree = ParameterTree({
            "voltage": (self.get_voltage, None),
            "current": (self.get_current, None),
            "fusevoltage": (self.get_fuse, None),
            "fuseblown": (self.get_fuse_blown, None),
            "fetfailed": (self.get_fet_failed, None),
            "enabled": (self.get_enable, self.set_enable),
            })

    def get_voltage(self):
        """Get the quad channel output voltage.

        This method returns the quad output channel voltage.

        :returns: channel output voltage in Volts
        """
        return self.quad.get_channel_voltage(self.channel_idx)

    def get_current(self):
        """Get the quad channel output current.

        This method returns the quad output channel current.

        :returns: output channel current in Amps
        """
        return self.quad.get_channel_current(self.channel_idx)

    def get_fuse(self):
        """Get the quad channel fuse voltage.

        This method returns the quad channel fuse voltage.

        :returns:  channel fuse voltage in Volts
        """
        return self.quad.get_fuse_voltage(self.channel_idx)

    def get_fuse_blown(self):
        """Get the quad channel fuse blown status.

        This method returns the quad output fuse blown status.

        :returns: quad output channel fuse blown status as bool
        """
        return self.quad.get_fuse_blown(self.channel_idx)

    def get_fet_failed(self):
        """Get the quad channel FET failure status.

        This method returns the quad output FET failure status.

        :returns: quad output channel FET failure status as bool
        """
        return self.quad.get_fet_failed(self.channel_idx)

    def get_enable(self):
        """Get the quad channel enable status.

        This method returns the quad output enable status.

        :returns: quad output channel enable status as bool
        """
        return self.quad.get_enable(self.channel_idx)

    def set_enable(self, enable):
        """Set the quad channel output enable.

        This method sets the quad channel output enable to the specified value.

        :param enable: bool enable value
        """
        self.quad.set_enable(self.channel_idx, enable)


class QuadData(object):
    """Data container for a LPD Quad box.

    This class omplements a data container for an LPD Quad box and its associated
    output channels, allowing the channel parameters to be read and the output of
    each channel to be controlled.
    """

    def __init__(self, *args, **kwargs):
        """Initilise the QuadData instance.

        This constructor initialises the QuadData instance. If an existing Quad instance
        is passed in as a keyword argument, that is used for accessing data, otherwise
        a new instance is created.

        :param args: positional arguments to be passed if creating a new Quad
        :param kwargs: keyword arguments to be passed if creating a new Quad, or if
        a quad key is present, that is used as an existing quad object instance
        """
        # Is a quad has been passed in keyword arguments use that, otherwise create a new one
        if 'quad' in kwargs:
            self.quad = kwargs['quad']
        else:
            self.quad = Quad(*args, **kwargs)

        # Create data containers for all channels on the quad
        self.channels = [ChannelData(self.quad, i) for i in range(self.quad.num_channels)]

        # Build the parameter tree
        self.param_tree = ParameterTree({
            "channels": [
                self.channels[0].param_tree,
                self.channels[1].param_tree,
                self.channels[2].param_tree,
                self.channels[3].param_tree
                ],
            "supply": (self.get_supply_voltage, None),
            })

    def get_supply_voltage(self):
        """Get the current value of the supply voltage to the Quad.

        This method returns the current supply voltage value for the Quad box.

        :returns: supply voltage in volts
        """
        return self.quad.get_supply_voltage()
