"""pscu_data - PSCU data container classes.

This module implements PSCUData and associated classes needed to represent the
parameter data from the LPD power supply control unit. PSCUData acts as a bridge
between the API adapter and the underlying PSCU object instance. Other classes
provide data containers for sensors on the PSCU, such as temperature and humidity.

James Hogge, STFC Application Engineering Group.
"""
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from lpdpower.quad_data import QuadData
from lpdpower.pscu import PSCU


class TempData(object):
    """Data container for a PSCU temperature sensor.

    This class implements a data container and parameter tree for a PSCU
    temperature sensor, which, in addition to having a readable value, also
    has parameters indicated set point, trace, trip state, and disable.
    """

    def __init__(self, pscu, sensor_idx):
        """Initialise the temperature data container for a sensor.

        This constructor initalises the data container for a temperature
        sensor, creating the parameter tree and associating it with a
        particular sensor on the PSCU.

        :param pscu: PSCU object to use to access the sensor
        :param sensor_idx: sensor index on PSCU
        """
        self.param_tree = ParameterTree({
            "temperature": (self.get_temperature, None),
            "temperature_volts": (self.get_temperature_volts, None),
            "setpoint": (self.get_set_point, None),
            "setpoint_volts": (self.get_set_point_volts, None),
            "tripped": (self.get_tripped, None),
            "trace": (self.get_trace, None),
            "disabled": (self.get_disabled, None),
            "name": (self.get_name, None),
            'mode': (self.get_mode, None),
        })

        self.pscu = pscu
        self.sensor_idx = sensor_idx

    def get_temperature(self):
        """Get the current temperature read by the sensor.

        This method returns the temperature read by the sensor from the PSCU.

        :returns: temperature in Celsius
        """
        return self.pscu.get_temperature(self.sensor_idx)

    def get_temperature_volts(self):
        """Get the current raw temperature read by the sensor.

        This method returns the raw temperature read by the sensor from the PSCU.

        :returns: temperature in volts
        """
        return self.pscu.get_temperature_volts(self.sensor_idx)

    def get_set_point(self):
        """Get the setpoint value of the temperature sensor.

        This method returns the set point value of the temperature sensor from the PSCU.

        :returns: set point value in Celsius
        """
        return self.pscu.get_temperature_set_point(self.sensor_idx)

    def get_set_point_volts(self):
        """Get the raw setpoint value of the temperature sensor.

        This method returns the raw set point value of the temperature sensor from the PSCU.

        :returns: raw set point value in voltage
        """
        return self.pscu.get_temperature_set_point_volts(self.sensor_idx)

    def get_tripped(self):
        """Get the trip status of the temperature sensor.

        This method returns the trip status of the sensor from the PSCU, i.e. if it has
        exceeded the specified set point.

        :returns: trip status as boolean.
        """
        return self.pscu.get_temperature_tripped(self.sensor_idx)

    def get_trace(self):
        """Get the trace status of the temperature sensor.

        This method returns the trace status (signal connection) of the sensor from the PSCU.

        :returns: trace status as boolean.
        """
        return self.pscu.get_temperature_trace(self.sensor_idx)

    def get_disabled(self):
        """Get the disabled status of the temperature sensor.

        This method returns the disabled status of the temperature sensor, i.e. if it
        has been disabled from the overall interlock state by a jumper connection.

        :returns: disabled status as boolean.
        """
        return self.pscu.get_temperature_disabled(self.sensor_idx)

    def get_name(self):
        """Get the name of the temperature sensor.

        This method returns the descriptive name of the temperature sensor.

        :returns: sensor name as a string
        """
        return self.pscu.get_temperature_name(self.sensor_idx)

    def get_mode(self):
        """Get the mode of the temperature sensor.

        This method returns the descriptive mode of the temperature sensor.

        :returns: sensor mode as a string
        """
        return self.pscu.get_temperature_mode(self.sensor_idx)


class HumidityData(object):
    """Data container for a PSCU humidity sensor.

    This class implements a data container and parameter tree for a PSCU
    humidity sensor, which, in addition to having a readable value, also
    has parameters indicated set point, trace, trip state, and disable.
    """

    def __init__(self, pscu, sensor_idx):
        """Initialise the temperature data container for a sensor.

        This constructor initalises the data container for a humidity
        sensor, creating the parameter tree and associating it with a
        particular sensor on the PSCU.

        :param pscu: PSCU object to use to access the sensor
        :param sensor_idx: sensor index on PSCU
        """
        self.param_tree = ParameterTree({
            "humidity": (self.get_humidity, None),
            "humidity_volts": (self.get_humidity_volts, None),
            "setpoint": (self.get_set_point, None),
            "setpoint_volts": (self.get_set_point_volts, None),
            "tripped": (self.get_tripped, None),
            "trace": (self.get_trace, None),
            "disabled": (self.get_disabled, None),
            "name": (self.get_name, None),
            "mode": (self.get_mode, None),
        })

        self.pscu = pscu
        self.sensor_idx = sensor_idx

    def get_humidity(self):
        """Get the current humidity read by the sensor.

        This method returns the humidity read by the sensor from the PSCU.

        :returns: humidity in percent
        """
        return self.pscu.get_humidity(self.sensor_idx)

    def get_humidity_volts(self):
        """Get the current raw humidity read by the sensor.

        This method returns the raw humidity read by the sensor from the PSCU.

        :returns: raw humidity in volts
        """
        return self.pscu.get_humidity_volts(self.sensor_idx)

    def get_set_point(self):
        """Get the setpoint value of the humidity sensor.

        This method returns the set point value of the humidity sensor from the PSCU.

        :returns: set point value in percent
        """
        return self.pscu.get_humidity_set_point(self.sensor_idx)

    def get_set_point_volts(self):
        """Get the raw setpoint value of the humidity sensor.

        This method returns the raw set point value of the humidity sensor from the PSCU.

        :returns: set raw point value in volts
        """
        return self.pscu.get_humidity_set_point_volts(self.sensor_idx)

    def get_tripped(self):
        """Get the trip status of the humidity sensor.

        This method returns the trip status of the sensor from the PSCU, i.e. if it has
        exceeded the specified set point.

        :returns: trip status as boolean.
        """
        return self.pscu.get_humidity_tripped(self.sensor_idx)

    def get_trace(self):
        """Get the trace status of the humidity sensor.

        This method returns the trace status (signal connection) of the sensor from the PSCU.

        :returns: trace status as boolean.
        """
        return self.pscu.get_humidity_trace(self.sensor_idx)

    def get_disabled(self):
        """Get the disabled status of the humidity sensor.

        This method returns the disabled status of the humidity sensor, i.e. if it
        has been disabled from the overall interlock state by a jumper connection.

        :returns: disabled status as boolean.
        """
        return self.pscu.get_humidity_disabled(self.sensor_idx)

    def get_name(self):
        """Get the name of the humidity sensor.

        This method returns the descriptive name of the humidity sensor.

        :returns: sensor name as a string
        """
        return self.pscu.get_humidity_name(self.sensor_idx)

    def get_mode(self):
        """Get the mode of the humidity sensor.

        This method returns the descriptive mode of the humidity sensor.

        :returns: sensor mode as a string
        """
        return self.pscu.get_humidity_mode(self.sensor_idx)


class PSCUDataError(Exception):
    """Simple exception class for PSCUData to wrap lower-level exceptions."""

    pass


class PSCUData(object):
    """Data container for a PSCU and associated quads.

    This class implements a data container and parameter tree of a PSCU,
    its assocated quad boxes and all sensors contained therein. A PSCUData
    object, asociated with a PSCU instance, forms the primary interface between,
    and data model for, the adapter and the underlying devices.
    """

    def __init__(self, *args, **kwargs):
        """Initialise the PSCUData instance.

        This constructor initialises the PSCUData instance. If an existing PSCU instance
        is passed in as a keyword argument, that is used for accessing data, otherwise
        a new instance is created.

        :param args: positional arguments to be passed if creating a new PSCU
        :param kwargs: keyword arguments to be passed if creating a new PSCU, or if
        a pscu key is present, that is used as an existing PSCU object instance
        """
        # If a PSCU has been passed in keyword arguments use that, otherwise create a new one
        if 'pscu' in kwargs:
            self.pscu = kwargs['pscu']
        else:
            self.pscu = PSCU(*args, **kwargs)

        # Get the QuadData containers associated with the PSCU
        self.quad_data = [QuadData(quad=q) for q in self.pscu.quad]

        # Get the temperature and humidity containers associated with the PSCU
        self.temperature_data = [
            TempData(self.pscu, i) for i in range(self.pscu.num_temperatures)
        ]
        self.humidity_data = [
            HumidityData(self.pscu, i) for i in range(self.pscu.num_humidities)
        ]

        # Build the parameter tree of the PSCU
        self.param_tree = ParameterTree({
            "quad": {
                "quads": [q.param_tree for q in self.quad_data],
                'trace': (self.get_quad_traces, None),
            },
            "temperature": {
                "sensors": [t.param_tree for t in self.temperature_data],
                "overall": (self.pscu.get_temperature_state,  None),
                "latched": (self.pscu.get_temperature_latched,  None),
            },
            "humidity": {
                "sensors": [h.param_tree for h in self.humidity_data],
                "overall": (self.pscu.get_humidity_state, None),
                "latched": (self.pscu.get_humidity_latched, None),
            },
            "fan": {
                "target": (self.pscu.get_fan_target, self.pscu.set_fan_target),
                "currentspeed_volts": (self.pscu.get_fan_speed_volts, None),
                "currentspeed": (self.pscu.get_fan_speed, None),
                "setpoint": (self.pscu.get_fan_set_point, None),
                "setpoint_volts": (self.pscu.get_fan_set_point_volts, None),
                "tripped": (self.pscu.get_fan_tripped, None),
                "overall": (self.pscu.get_fan_state, None),
                "latched": (self.pscu.get_fan_latched, None),
                "mode": (self.pscu.get_fan_mode, None),
            },
            "pump": {
                "flow": (self.pscu.get_pump_flow, None),
                "flow_volts": (self.pscu.get_pump_flow_volts, None),
                "setpoint": (self.pscu.get_pump_set_point, None),
                "setpoint_volts": (self.pscu.get_pump_set_point_volts, None),
                "tripped": (self.pscu.get_pump_tripped, None),
                "overall": (self.pscu.get_pump_state, None),
                "latched": (self.pscu.get_pump_latched, None),
                "mode": (self.pscu.get_pump_mode, None),
            },
            "trace": {
                 "overall": (self.pscu.get_trace_state, None),
                 "latched": (self.pscu.get_trace_latched,  None),
            },
            "position": (self.pscu.get_position, None),
            "position_volts": (self.pscu.get_position_volts, None),
            "overall": (self.pscu.get_health,  None),
            "latched": (self.get_all_latched, None),
            "armed": (self.pscu.get_armed, self.pscu.set_armed),
            "allEnabled": (self.pscu.get_all_enabled, self.pscu.enable_all),
            "enableInterval": (self.pscu.get_enable_interval, None),
            "displayError": (self.pscu.get_display_error, None),
        })

    def get(self, path):
        """Get parameters from the underlying parameter tree.

        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate PSCUDataError.

        :param path: path of parameter tree to get
        :returns: parameter tree at that path as a dictionary
        """
        try:
            return self.param_tree.get(path)
        except ParameterTreeError as e:
            raise PSCUDataError(e)

    def set(self, path, data):
        """Set parameters in underlying parameter tree.

        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate PSCUDataError.

        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise PSCUDataError(e)

    def get_all_latched(self):
        """Return the global latch status of the PSCU.

        This method returns the global latch status for the PSCU, which is the logical AND of
        PSCU latch channels

        :returns: global latch status as bool
        """
        return all(self.pscu.get_all_latched())

    def get_quad_traces(self):
        """Return the trace status for the quads in the PSCU.

        This method returns a dictionary of the quad trace status values for the PSCU.

        :returns: dictionary of the quad trace status
        """
        return {str(q): self.pscu.get_quad_trace(q) for q in range(self.pscu.num_quads)}
