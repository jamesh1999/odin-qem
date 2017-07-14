"""PSCU - device class for the LPD power supply control unit.

This class implements support for the LPD power supply control unit, providing control
and monitoring functionality for the PSCU and all connected Quad output boxes and
sensors. The PSCU also handles updating the front-panel LCD and responding to the
page up/down buttons on the front panel.

James Hogge, STFC Application Engineering Group.
"""
from math import sqrt

from lpdpower.i2c_device import I2CDevice, I2CException
from lpdpower.i2c_container import I2CContainer
from lpdpower.tca9548 import TCA9548
from lpdpower.ad7998 import AD7998
from lpdpower.ad5321 import AD5321
from lpdpower.mcp23008 import MCP23008
from lpdpower.quad import Quad
from lpdpower.lcd_display import LcdDisplay, LcdDisplayError
from lpdpower.deferred_executor import DeferredExecutor

import Adafruit_BBIO.GPIO as GPIO
import logging


class PSCU(I2CContainer):
    """PSCU - device class for the LPD power supply control unit.

    The class implements support for the LPD power supply control unit.
    """

    ALL_PINS = [0, 1, 2, 3, 4, 5, 6, 7]
    DEFAULT_QUAD_ENABLE_INTERVAL = 1.0
    DEFAULT_DETECTOR_POSITION_OFFSET = 0.0
    TEMP_VREF = 3.0
    HUMIDITY_VREF = 5.0
    FAN_VREF = 5.0
    PUMP_VREF = 5.0
    POSITION_VREF = 5.0

    TEMP_SENSOR_NAMES = [
        'Vent 1',
        'Vent 2',
        'Intake 1',
        'Intake 2',
        'Rear Lower',
        'Rear Upper',
        'N/C',
        'N/C',
        'Coolant Out',
        'Coolant In',
        'N/C',
    ]

    HUMIDITY_SENSOR_NAMES = [
        'Front',
        'Rear',
    ]

    def __init__(self, quad_enable_interval=DEFAULT_QUAD_ENABLE_INTERVAL,
                 detector_position_offset=DEFAULT_DETECTOR_POSITION_OFFSET):
        """Initialise the PSCU instance.

        The constructor initialises the PSCU instance, setting up all the I2C
        devices on the PSCU, intialising and attached the quads, and setting up the
        front panel display and buttons.

        :param quad_enable_interval: time interval between quad enable commands
        """
        # Turn off exception raising in the I2C device class
        I2CDevice.disable_exceptions()

        # Set up the quad enable interval with the specified value
        self.quad_enable_interval = quad_enable_interval
        self.detector_position_offset = detector_position_offset

        # Create the TCA I2C bus multiplexer instance
        self.tca = TCA9548(0x70)

        # Attach the quads to the TCA
        self.num_quads = 4
        self.quad = []
        for i in range(self.num_quads):
            self.quad.append(self.tca.attach_device(i, Quad))

        # Attach the internal I2C bus 4 sensor and IO devices
        # Temperature monitor ADC channels
        self.adc_temp_mon = []
        self.adc_temp_mon.append(self.tca.attach_device(4, AD7998, 0x21))
        self.adc_temp_mon.append(self.tca.attach_device(4, AD7998, 0x22))
        self.adc_temp_mon.append(self.tca.attach_device(4, AD7998, 0x23))

        # Temperature monitor GPIO channels
        self.mcp_temp_mon = []
        self.mcp_temp_mon.append(self.tca.attach_device(4, MCP23008, 0x24))
        for i in range(8):
            self.mcp_temp_mon[0].setup(i, MCP23008.IN if i < 7 else MCP23008.IN)

        self.mcp_temp_mon.append(self.tca.attach_device(4, MCP23008, 0x25))
        for i in range(8):
            self.mcp_temp_mon[1].setup(i, MCP23008.IN)

        self.mcp_temp_mon.append(self.tca.attach_device(4, MCP23008, 0x26))
        for i in range(8):
            self.mcp_temp_mon[2].setup(i, MCP23008.IN)

        self.mcp_temp_mon.append(self.tca.attach_device(4, MCP23008, 0x27))
        for i in range(8):
            self.mcp_temp_mon[3].setup(i, MCP23008.IN)

        # Attach the miscellaneous I2C bus 5 devices
        # Miscellaneous ADC channels
        self.adc_misc = []
        self.adc_misc.append(self.tca.attach_device(5, AD7998, 0x21))
        self.adc_misc.append(self.tca.attach_device(5, AD7998, 0x22))

        # Miscellaneous monitor GPIO channels
        self.mcp_misc = []
        self.mcp_misc.append(self.tca.attach_device(5, MCP23008, 0x24))
        for i in range(8):
            self.mcp_misc[0].setup(i, MCP23008.OUT if i < 2 else MCP23008.IN)
        self.mcp_misc.append(self.tca.attach_device(5, MCP23008, 0x25))
        for i in range(8):
            self.mcp_misc[1].setup(i, MCP23008.IN)
        self.mcp_misc.append(self.tca.attach_device(5, MCP23008, 0x26))
        for i in range(8):
            self.mcp_misc[2].setup(i, MCP23008.IN)
        self.mcp_misc.append(self.tca.attach_device(5, MCP23008, 0x27))
        for i in range(8):
            self.mcp_misc[3].setup(i, MCP23008.IN)

        # Attach the fan speed DAC device
        self.fan_speed_dac = self.tca.attach_device(5, AD5321, 0x0c)

        # Create internal buffer variables for all sensor parameters
        # Temperature
        self.num_temperatures = 11
        self.__temperature_values = [0.0] * self.num_temperatures
        self.__temperature_values_raw = [0.0] * self.num_temperatures
        self.__temperature_set_points = [0.0] * self.num_temperatures
        self.__temperature_set_points_raw = [0.0] * self.num_temperatures
        self.__temperature_trips = [False] * self.num_temperatures
        self.__temperature_traces = [False] * self.num_temperatures
        self.__temperature_disabled = [False] * self.num_temperatures
        self.__temperature_mode = ['Over'] * 8 + ['Under'] * 3

        # Humidity
        self.num_humidities = 2
        self.__humidity_values = [0.0] * self.num_humidities
        self.__humidity_values_raw = [0.0] * self.num_humidities
        self.__humidity_set_points = [0.0] * self.num_humidities
        self.__humidity_set_points_raw = [0.0] * self.num_humidities
        self.__humidity_trips = [False] * self.num_humidities
        self.__humidity_traces = [False] * self.num_humidities
        self.__humidity_disabled = [False] * self.num_humidities
        self.__humidity_mode = ['Over'] * self.num_humidities

        # Pump
        self.__pump_flow = 0.0
        self.__pump_flow_raw = 0.0
        self.__pump_set_point = 0.0
        self.__pump_set_point_raw = 0.0
        self.__pump_trip = False
        self.__pump_mode = 'Under'

        # Fan
        self.__fan_speed = 0.0
        self.__fan_speed_raw = 0.0
        self.__fan_target = 100.0
        self.__fan_set_point = 0.0
        self.__fan_set_point_raw = 0.0
        self.__fan_trip = False
        self.__fan_mode = 'Under'

        # Position
        self.__position = 0.0
        self.__position_raw = 0.0

        # Quad traces
        self.__quad_traces = [False] * self.num_quads

        # Overall
        self.__armed = False
        self.__healthy = False
        self.__sensor_states = [False] * 5  # Tmp, F, P, H, T
        self.__latched_states = [False] * 5  # Tmp, F, P, T, H

        # Initialise the front panel LCD
        try:
            self.lcd = LcdDisplay(self, "/dev/ttyACM0", 57600, rows=4, cols=20)
            self.lcd_display_error = False
        except LcdDisplayError as e:
            logging.warning(e)
            self.lcd_display_error = True

        # Intialise the front panel push buttons on GPIO pins and enable rising edge detection
        GPIO.setup("P9_11", GPIO.IN)
        GPIO.setup("P9_12", GPIO.IN)
        GPIO.add_event_detect("P9_11", GPIO.RISING)
        GPIO.add_event_detect("P9_12", GPIO.RISING)

        # Internal flag tracking state of quads 'enable all' command
        self.__all_enabled = False

        self.deferred_executor = DeferredExecutor()

    def handle_deferred(self):
        """Handle deferred commands.

        This method handles any deferred PSCU commands currently queued in the deferred
        executor. This is intended to be called periodically by e.g. an update loop that is
        updating the PSCU status.
        """
        self.deferred_executor.process()

    def get_temperature(self, sensor):
        """Get the value of a PSCU temperature sensor.

        This method returns the current temperature value of the specified sensor.

        :param sensor: temperature sensor index
        :returns: temperature value for sensor
        """
        if sensor >= self.num_temperatures or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__temperature_values[sensor]

    def get_temperature_volts(self, sensor):
        """Get the raw value of a PSCU temperature sensor.

        This method returns the current raw temperature value of the specified sensor.

        :param sensor: temperature sensor index
        :returns: raw temperature value for sensor in volts
        """
        if sensor >= self.num_temperatures or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__temperature_values_raw[sensor] * PSCU.TEMP_VREF

    def get_temperature_set_point(self, sensor):
        """Get the set point of a PSCU temperature sensor.

        This method returns the current set point for the specified temperature sensor.

        :param sensor: temperature sensor index
        :returns: value of the temperature sensor set point
        """
        if sensor >= self.num_temperatures or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__temperature_set_points[sensor]

    def get_temperature_set_point_volts(self, sensor):
        """Get the raw set point of a PSCU temperature sensor.

        This method returns the current raw set point for the specified temperature sensor.

        :param sensor: temperature sensor index
        :returns: raw value of the temperature sensor set point in volts
        """
        if sensor >= self.num_temperatures or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__temperature_set_points_raw[sensor] * PSCU.TEMP_VREF

    def get_temperature_tripped(self, sensor):
        """Get the trip status of a PSCU temperature sensor.

        This method returns the current set point for the specified temperature sensor.

        :param sensor: temperature sensor index
        :returns: temperature sensor trip status
        """
        if sensor >= self.num_temperatures or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__temperature_trips[sensor]

    def get_temperature_trace(self, sensor):
        """Get the trace status of a PSCU temperature sensor.

        This method returns the current trace status for the specified temperature sensor.

        :param sensor: temperature sensor index
        :returns: temperature sensor trace status
        """
        if sensor >= self.num_temperatures or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__temperature_traces[sensor]

    def get_temperature_disabled(self, sensor):
        """Get the disabled status of a PSCU temperature sensor.

        This method returns the current disable status for the specified temperature sensor.

        :param sensor: temperature sensor index
        :returns: temperature sensor disable status
        """
        if sensor >= self.num_temperatures or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__temperature_disabled[sensor]

    def get_temperature_name(self, sensor):
        """Get the name of a PSCU temperature sensor.

        This method returns the descriptive name for the specified PSCU temperature sensor.

        :param sensor: temperature sensor index
        :returns: temperature sensor decriptive name
        """
        if sensor >= self.num_temperatures or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return PSCU.TEMP_SENSOR_NAMES[sensor]

    def get_temperature_mode(self, sensor):
        """Get the mode of a PSCU temperature sensor.

        This method returns the descriptive mode for the specified PSCU temperature sensor, i.e.
        whether the sensor channel has an over- or under-temperature trip condition.

        :param sensor: temperature sensor index
        :returns: temperature sensor decriptive mode as string
        """
        if sensor >= self.num_temperatures or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__temperature_mode[sensor]

    def get_humidity(self, sensor):
        """Get the value of a PSCU humidity sensor.

        This method returns the current humidity value of the specified sensor.

        :param sensor: humidity sensor index
        :returns: humidity value for sensor
        """
        if sensor >= self. num_humidities or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__humidity_values[sensor]

    def get_humidity_volts(self, sensor):
        """Get the raw value of a PSCU humidity sensor.

        This method returns the current raw humidity value of the specified sensor.

        :param sensor: humidity sensor index
        :returns: raw humidity value for sensor
        """
        if sensor >= self. num_humidities or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__humidity_values_raw[sensor] * PSCU.HUMIDITY_VREF

    def get_humidity_set_point(self, sensor):
        """Get the set point of a PSCU humidity sensor.

        This method returns the current set point for the specified humidity sensor.

        :param sensor: humidity sensor index
        :returns: value of the humidity sensor set point
        """
        if sensor >= self. num_humidities or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__humidity_set_points[sensor]

    def get_humidity_set_point_volts(self, sensor):
        """Get the raw set point of a PSCU humidity sensor.

        This method returns the current set point for the specified humidity sensor.

        :param sensor: humidity sensor index
        :returns: raw value of the humidity sensor set point in volts
        """
        if sensor >= self. num_humidities or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__humidity_set_points_raw[sensor] * PSCU.HUMIDITY_VREF

    def get_humidity_tripped(self, sensor):
        """Get the trip status of a PSCU humidity sensor.

        This method returns the current trip status for the specified humidity sensor.

        :param sensor: humidity sensor index
        :returns: humidity sensor trip status
        """
        if sensor >= self. num_humidities or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__humidity_trips[sensor]

    def get_humidity_trace(self, sensor):
        """Get the trip status of a PSCU humidity sensor.

        This method returns the current trace status for the specified humidity sensor.

        :param sensor: humidity sensor index
        :returns: humidity sensor trace status
        """
        if sensor >= self. num_humidities or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__humidity_traces[sensor]

    def get_humidity_disabled(self, sensor):
        """Get the disabled status of a PSCU humidity sensor.

        This method returns the current disable status for the specified humidity sensor.

        :param sensor: humidity sensor index
        :returns: humidity sensor disable status
        """
        if sensor >= self. num_humidities or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__humidity_disabled[sensor]

    def get_humidity_name(self, sensor):
        """Get the name of a PSCU humidity sensor.

        This method returns the descriptive name for the specified PSCU humidity sensor.

        :param sensor: humidity sensor index
        :returns: humidity sensor decriptive name
        """
        if sensor >= self.num_humidities or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return PSCU.HUMIDITY_SENSOR_NAMES[sensor]

    def get_humidity_mode(self, sensor):
        """Get the mode of a PSCU humidity sensor.

        This method returns the descriptive mode for the specified PSCU humidity sensor, i.e.
        whether the sensor channel has an over- or under-humidity trip condition.

        :param sensor: humidity sensor index
        :returns: humidity sensor decriptive mode as string
        """
        if sensor >= self.num_humidities or sensor < 0:
            raise I2CException('Illegal sensor index {} specified'.format(sensor))

        return self.__humidity_mode[sensor]

    def get_pump_flow(self):
        """Get the value of the PSCU pump flow sensor.

        This method returns the current pump flow sensor value.

        :returns: pump flow in l/min
        """
        return self.__pump_flow

    def get_pump_flow_volts(self):
        """Get the raw value of the PSCU pump flow sensor.

        This method returns the current raw pump flow sensor value.

        :returns: raw pump flow in volts
        """
        return self.__pump_flow_raw * PSCU.PUMP_VREF

    def get_pump_set_point(self):
        """Get the value of the PSCU pump flow set point.

        This method returns the current pump flow sensor set point value.

        :returns: pump flow set point in l/min
        """
        return self.__pump_set_point

    def get_pump_set_point_volts(self):
        """Get the raw value of the PSCU pump flow set point.

        This method returns the current raw pump flow sensor set point value.

        :returns: raw pump flow set point in volts
        """
        return self.__pump_set_point_raw * PSCU.PUMP_VREF

    def get_pump_tripped(self):
        """Get the trip status of the PSCU pump flow meter.

        This method returns the current trip status for the specified humidity sensor.

        :returns: pump flow sensor trip status
        """
        return self.__pump_trip

    def get_pump_mode(self):
        """Get the mode of the PSCU pumpsensor.

        This method returns the descriptive mode for the  PSCU pump sensor, i.e.
        whether the sensor channel has an over- or under-flow trip condition.

        :returns: pump sensor decriptive mode as string
        """
        return self.__pump_mode

    def get_fan_speed(self):
        """Get the current fan speed.

        This method returns the current LPD fan speed in RPM.

        :returns: fan speed in RPM
        """
        return self.__fan_speed

    def get_fan_speed_volts(self):
        """Get the current raw fan speed.

        This method returns the current raw LPD fan speed in volts.

        :returns: raw fan speed in volts
        """
        return self.__fan_speed_raw * PSCU.FAN_VREF

    def get_fan_set_point(self):
        """Get the current fan speed set point.

        This method returns the current LPD fan speed set point in RPM.

        :returns: fan speed set point in RPM
        """
        return self.__fan_set_point

    def get_fan_set_point_volts(self):
        """Get the current raw fan speed set point.

        This method returns the current raw LPD fan speed set point in volts.

        :returns: raw fan speed set point in volts
        """
        return self.__fan_set_point_raw * PSCU.FAN_VREF

    def get_fan_target(self):
        """Get the current fan target speed.

        This method returns the current target LPD fan speed set point in percent of maxiumum

        :returns: target fan speed set point in percent
        """
        return self.__fan_target

    def get_fan_tripped(self):
        """Get the trip status of the LPD fan.

        This method returns the current trip status for the fan.

        :returns: fan speed trip status
        """
        return self.__fan_trip

    def get_fan_mode(self):
        """Get the mode of the PSCU fan sensor.

        This method returns the descriptive mode for the  PSCU fan sensor, i.e.
        whether the sensor channel has an over- or under-speed trip condition.

        :returns: fan sensor decriptive mode as string
        """
        return self.__fan_mode

    def get_quad_trace(self, quad_idx):
        """Get the trace status for a specified quad.

        This method returns the trace status for the specified quad.

        :param quad_idx: quad index
        :returns: quad trace status as bool
        """
        if quad_idx >= self.num_quads or quad_idx < 0:
            raise I2CException("Illegal quad index {} specified".format(quad_idx))

        return self.__quad_traces[quad_idx]

    def get_position(self):
        """Get the value of the detector position sensor.

        This method returns the value of the the potentiometer reading the position
        of the quadrant motion system. The value is returned as the transverse opening
        of the quadrant assembly (i.e. width of the beam pipe hole) in mm, and is signed
        according the which direction the quadrants are opened in.

        :returns: transverse position in mm
        """
        return self.__position

    def get_position_volts(self):
        """Get the value of the detector position sensor.

        This method returns the raw value of the the potentiometer reading the position
        of the quadrant motion system in volts.

        :returns: raw poisition in volts
        """
        return self.__position_raw * PSCU.POSITION_VREF

    def get_armed(self):
        """Get the PSCU interlock armed state.

        This method returns the current armed state of the PSCU interlock system. The
        system can be armed if all sensors are in healthy state.

        :returns: PSCU interlock armed state as bool
        """
        return self.__armed

    def get_all_enabled(self):
        """Get the status indicating all outputs are enabled.

        This method returns a status indicating if all PSCU quad outputs are enabled, which is
        primarily beneficial to clients determining the next action for an enable/disable all
        command.

        :returns: PSCU 'all enabled' status as bool
        """
        return self.__all_enabled

    def get_health(self):
        """Get the overall PSCU health status.

        This method returns the overall PSCU health status, which indicates if all
        sensor channels have healthy values and are within setpoints.

        :returns: PSCU health state as bool
        """
        return self.__healthy

    def get_temperature_state(self):
        """Get the status of the PSCU temperature interlock.

        This method returns the global status of the the temperature interlock, i.e. if
        all temperature sensors are within setpoints.

        :returns: PSCU overall temperature status as bool
        """
        return self.__sensor_states[0]

    def get_temperature_latched(self):
        """Get the status of the PSCU temperature latch.

        This method returns the status of the temperature latch condition, i.e. if a
        sensor has exceeded a setpoint and been latched. The latch state is cleared
        on a subsequent arm command.

        :returns: PSCU temperature latch state as bool
        """
        return self.__latched_states[0]

    def get_trace_state(self):
        """Get the status of the PSCU trace interlock.

        This method returns the global status of the the trace interlock, i.e. if
        all trace channels are connected.

        :returns: PSCU overall trace status as bool
        """
        return self.__sensor_states[4]

    def get_trace_latched(self):
        """Get the status of the PSCU trace latch.

        This method returns the status of the trace latch condition, i.e. if a
        trace circuit has opened and been latched. The latch state is cleared
        on a subsequent arm command.

        :returns: PSCU trace latch state as bool
        """
        return self.__latched_states[3]

    def get_fan_state(self):
        """Get the status of the PSCU fan speed interlock.

        This method returns the global status of the the fan speed interlock, i.e. if
        the fan speed value is within the setpoint.

        :returns: PSCU fan speed status as bool
        """
        return self.__sensor_states[1]

    def get_fan_latched(self):
        """Get the status of the PSCU fan speed latch.

        This method returns the status of the fan speed latch condition, i.e. if the
        fan speed has gone outside the setpoint and been latched. The latch state is cleared
        on a subsequent arm command.

        :returns: PSCU fan speed latch state as bool
        """
        return self.__latched_states[1]

    def get_pump_state(self):
        """Get the status of the PSCU pump flow rate interlock.

        This method returns the global status of the the pump flow rate interlock, i.e. if
        the pump flow rate is within the setpoint.

        :returns: PSCU pump flow rate status as bool
        """
        return self.__sensor_states[2]

    def get_pump_latched(self):
        """Get the status of the PSCU pump flow rate latch.

        This method returns the status of the pump flow rate latch condition, i.e. if the
        pump flow rate has gone outside the setpoint and been latched. The latch state is cleared
        on a subsequent arm command.

        :returns: PSCU pump flow rate latch state as bool
        """
        return self.__latched_states[2]

    def get_humidity_state(self):
        """Get the status of the PSCU humidity interlock.

        This method returns the global status of the the humidity interlock, i.e. if
        all temperature sensors are within setpoints.

        :returns: PSCU overall humidity status as bool
        """
        return self.__sensor_states[3]

    def get_humidity_latched(self):
        """Get the status of the PSCU humidity latch.

        This method returns the status of the humidity latch condition, i.e. if a
        sensor has exceeded a setpoint and been latched. The latch state is cleared
        on a subsequent arm command.

        :returns: PSCU humidity latch state as bool
        """
        return self.__latched_states[4]

    def get_all_latched(self):
        """Get the state of all latch conditions.

        This method returns the state of all PSCU latch conditions as a list, and is
        provided as a convenience for a client requested all latch states simultaneously.

        :returns: PSCU latch states as a list of bools
        """
        return self.__latched_states

    def get_enable_interval(self):
        """Get the quad output enable interval.

        This method returns the quad output enable interval, which is used to sequence
        quad outputs on at a fixed rate to avoid inrush. The enable interval is set
        as an argument at initialisation, i.e. passed in as an option.

        :returns: enable interval in seconds
        """
        return self.quad_enable_interval

    def quad_enable_channel(self, quad_idx, channel_idx):
        """Enable a quad output channel.

        This method enables the specified quad output channel. It is primarily intended
        for use within a sequenced turn on via call to enable_all().

        :param quad_idx: index of quad to control
        :param channel_idx: index of the channel to turn on
        """
        if quad_idx >= self.num_quads or quad_idx < 0:
            raise I2CException("Illegal quad index {} specified".format(quad_idx))

        if channel_idx >= Quad.NUM_CHANNELS or channel_idx < 0:
            raise I2CException("Illegal channel index {} specified".format(channel_idx))

        logging.debug("Enabling quad {} channel {} output".format(quad_idx, channel_idx))
        self.quad[quad_idx].set_enable(channel_idx, True)

    def enable_all(self, enable):
        """Enable or disable all quad output channels.

        This method enables or disables all quad output channels. To avoid excessive inrush
        current, an enable command launches a sequence of deferred calls to enable the channels
        at the interval specified as an initialisation argument. A disable command clears any
        queued enables and turns off all channels at once.

        :param enable: bool flag indicating requested enable or disable state
        """
        logging.debug("Called enable_all with value {}".format(enable))

        if enable:
            # Loop over all quads and channels in system, adding enable command to deferred
            # executor queue
            for quad_idx in range(len(self.quad)):
                for channel in range(Quad.NUM_CHANNELS):
                    self.deferred_executor.enqueue(
                        self.quad_enable_channel, self.quad_enable_interval, quad_idx, channel
                    )
            self.__all_enabled = True
        else:
            # Clear any pending turn-on command from the queue first, then turn off all channels
            # immediately.
            num_enables_pending = self.deferred_executor.pending()
            if num_enables_pending > 0:
                logging.debug("Clearing {} pending quad enable commands from queue".format(
                    num_enables_pending
                ))
                self.deferred_executor.clear()
            for quad_idx in range(len(self.quad)):
                for channel in range(Quad.NUM_CHANNELS):
                    self.quad[quad_idx].set_enable(channel, False)
            self.__all_enabled = False

    def set_armed(self, arm):
        """Arm or disarm the PSCU interlock.

        This method arms or disarms the PSCU interlock by toggling the appropriate arm/disarm
        output pin with a low-high-low transition.

        :param value: bool flag indicating arm or disarm
        """
        pin = 0 if arm else 1
        self.mcp_misc[0].output(pin, MCP23008.LOW)
        self.mcp_misc[0].output(pin, MCP23008.HIGH)
        self.mcp_misc[0].output(pin, MCP23008.LOW)

    def set_fan_target(self, target_percent):
        """Set the fan speed target value.

        This method sets the fan speed target value as a percentage of the maximum.

        :param target_percent: fan speed target in percent
        """
        self.__fan_target = target_percent
        self.fan_speed_dac.set_output_scaled(1.0 - (target_percent / 100.0))

    def get_display_error(self):
        """Get the status of the LCD error flag.

        This method returns the status of the LCD error flag, which is set if the PSCU
        instance cannot initialise the display at startup.

        :returns: LCD error status as bool
        """
        return self.lcd_display_error

    def update_lcd(self):
        """Update the front-panel LCD.

        This method updates the front-panel LCD, detecting front-panel button presses to
        change page and refreshing the content and colour of the display. This is
        intended to be called periodically as part of an update loop to keep the display
        output reflecting the PSCU state.
        """
        # Do nothing if display was not initialised OK
        if self.lcd_display_error:
            return

        # Detect front-panel button presses to cycle through the LCD pages
        if GPIO.event_detected("P9_11"):
            self.lcd.previous_page()
        elif GPIO.event_detected("P9_12"):
            self.lcd.next_page()

        # Set the LCD backlight colour depending on the overall system health
        if self.__healthy:
            self.lcd.set_colour(LcdDisplay.GREEN)
        else:
            self.lcd.set_colour(LcdDisplay.RED)

        # Update the LCD content
        self.lcd.update()

    def convert_ad7998_temp(self, scaled_adc_val):
        """Convert a scaled ADC reading into temperature.

        This method takes a scaled ADC channel reading, i.e. as returned by the
        read_input_scaled() method and converts it into temperature in Celsius.

        :input scaled_adc_val ADC channel reading as fraction of full-scale
        :returns: temperature value in Celsius.
        """
        temp_scale_v_kelvin = 0.005
        temp_celsius = ((scaled_adc_val * PSCU.TEMP_VREF) / temp_scale_v_kelvin) - 273.15

        return temp_celsius

    def convert_ad7998_humidity(self, scaled_adc_val):
        """Convert a scaled ADC reading into humidity.

        This method takes a scaled ADC channel reading, i.e. as returned by the
        read_input_scaled() method and converts it into temperature in percent.

        :input scaled_adc_val ADC channel reading as fraction of full-scale
        :returns: humidity value in percent.
        """
        humidity_scale = 0.031
        humidity_offset = 0.8

        humidity_percent = ((scaled_adc_val * PSCU.HUMIDITY_VREF) - humidity_offset) / humidity_scale

        return humidity_percent

    def convert_ad7998_fan(self, scaled_adc_val):
        """Convert a scaled ADC reading into fan speed.

        This method takes a scaled ADC channel reading, i.e. as returned by the
        read_input_scaled() method and converts it into fan speed in RPM.

        :input scaled_adc_val ADC channel reading as fraction of full-scale
        :returns: fan speed value in RPM.
        """
        fan_scale = 4.5
        fan_max = 3000.0

        fan_rpm = ((scaled_adc_val * PSCU.FAN_VREF) / fan_scale) * fan_max

        return fan_rpm

    def convert_ad7998_pump(self, scaled_adc_val):
        """Convert a scaled ADC reading into pump flow rate.

        This method takes a scaled ADC channel reading, i.e. as returned by the
        read_input_scaled() method and converts it into pump flow rate in litres/min.

        :input scaled_adc_val ADC channel reading as fraction of full-scale
        :returns: pump flow rate in litre/min
        """
        pump_scale = 4.32
        pump_max = 35.0

        pump_lpermin = ((scaled_adc_val * PSCU.PUMP_VREF) / pump_scale) * pump_max

        return pump_lpermin

    def convert_ad7998_position(self, scaled_adc_val):
        """Convert a scaled ADC reading into a transverse detector position.

        This method takes a scaled ADC channel reading, i.e. as returned by the read_input_scaled()
        method and converts it into a transverse detector position. The detector position offset
        specified as an initalisation option is taken into account.

        :input scaled_adc_val ADC channel reading as fraction of full scale
        :returns: transverse detector position in mm.
        """
        position_scale = 0.1

        linear_position = ((scaled_adc_val * PSCU.POSITION_VREF) / position_scale)
        transverse_position = ((2.0 * linear_position) / sqrt(2.0)) - self.detector_position_offset

        return transverse_position

    def poll_all_sensors(self):
        """Poll all sensor channels and update their values in the internal buffers.

        This method polls all PSCU sensor channels, converts to the appropriate values and stores
        them in the internal buffer variables for future access by the appropriate get_xxxx methods.
        This is intended to be called periodically by an update loop and avoids a client access
        dependent load being placed on the hardware.
        """
        # Read input pin state of the monitor MCPs
        mcp_mon_0 = self.mcp_temp_mon[0].input_pins([0, 1, 2, 3, 4, 5, 7])
        mcp_mon_1 = self.mcp_temp_mon[1].input_pins(self.ALL_PINS)
        mcp_mon_2 = self.mcp_temp_mon[2].input_pins(self.ALL_PINS)
        mcp_mon_3 = self.mcp_temp_mon[3].input_pins([0, 1, 2, 3, 4, 5])

        # Read input pin state of the misc MPCs
        mcp_misc_0 = self.mcp_misc[0].input_pins([2, 3, 4, 5, 6, 7])
        mcp_misc_1 = self.mcp_misc[1].input_pins([0, 1, 2, 3])
        mcp_misc_2 = self.mcp_misc[2].input_pins([1, 2, 4, 5, 6, 7])
        mcp_misc_3 = self.mcp_misc[3].input_pins([0, 1, 2, 3, 4])

        # Read, convert and store all temperature values and setpoints from the ADCs and
        # extract and store all trip, trace and disabled states from the MCPs

        for i in range(4):
            self.__temperature_disabled[i + 4] = mcp_mon_0[i]

        self.__temperature_disabled[10] = mcp_mon_0[4]

        for i in range(8):
            self.__temperature_set_points_raw[i] = self.adc_temp_mon[0].read_input_scaled(i)
            self.__temperature_set_points[i] = self.convert_ad7998_temp(
                self.__temperature_set_points_raw[i]
            )
            self.__temperature_values_raw[i] = self.adc_temp_mon[1].read_input_scaled(i)
            if not self.__temperature_disabled[i]:
                self.__temperature_values[i] = self.convert_ad7998_temp(
                    self.__temperature_values_raw[i]
                )
            self.__temperature_trips[i] = not bool(mcp_mon_1[i])
            self.__temperature_traces[i] = bool(mcp_mon_2[i])

        for i in range(3):
            self.__temperature_values_raw[i + 8] = self.adc_temp_mon[2].read_input_scaled(i)
            if not self.__temperature_disabled[i + 8]:
                self.__temperature_values[i + 8] = self.convert_ad7998_temp(
                    self.__temperature_values_raw[i + 8]
                )
            self.__temperature_set_points_raw[i + 8] = self.adc_temp_mon[2].read_input_scaled(i+4)
            self.__temperature_set_points[i + 8] = self.convert_ad7998_temp(
                self.__temperature_set_points_raw[i + 8]
            )
            self.__temperature_trips[i + 8] = not bool(mcp_mon_3[i])
            self.__temperature_traces[i + 8] = bool(mcp_mon_3[i+3])

        # Read, convert and store all humidity values and setpoints from the ADCs and
        # extract and store all trip, trace and disabled states from the MCPs

        self.__humidity_disabled[1] = mcp_mon_0[5]

        for i in range(self.num_humidities):

            self.__humidity_set_points_raw[i] = self.adc_misc[0].read_input_scaled(i+1)
            self.__humidity_set_points[i] = self.convert_ad7998_humidity(
                self.__humidity_set_points_raw[i]
            )
            self.__humidity_values_raw[i] = self.adc_misc[1].read_input_scaled(i+1)
            if not self.__humidity_disabled[i]:
                self.__humidity_values[i] = self.convert_ad7998_humidity(
                    self.__humidity_values_raw[i]
                )

            self.__humidity_trips[i] = not bool(mcp_misc_1[i+1])
            self.__humidity_traces[i] = bool(mcp_misc_2[i])

        # Read, convert and store fan speed and setpoint ADC values and extract and store
        # the fan trip status
        self.__fan_speed_raw = self.adc_misc[1].read_input_scaled(0)
        self.__fan_speed = self.convert_ad7998_fan(self.__fan_speed_raw)
        self.__fan_set_point_raw = self.adc_misc[0].read_input_scaled(0)
        self.__fan_set_point = self.convert_ad7998_fan(self.__fan_set_point_raw)
        self.__fan_trip = not bool(mcp_misc_1[0])

        # Read, convert and store pump flow speed and setpoint ADC values and extract and store
        # the pump trip status
        self.__pump_flow_raw = self.adc_misc[1].read_input_scaled(3)
        self.__pump_flow = self.convert_ad7998_pump(self.__pump_flow_raw)
        self.__pump_set_point_raw = self.adc_misc[0].read_input_scaled(3)
        self.__pump_set_point = self.convert_ad7998_pump(self.__pump_set_point_raw)
        self.__pump_trip = not bool(mcp_misc_1[3])

        # Read, convert and save the detector position
        self.__position_raw = self.adc_misc[1].read_input_scaled(4)
        self.__position = self.convert_ad7998_position(self.__position_raw)

        # Extract and save global armed and health states
        self.__armed = bool(mcp_misc_0[0])
        self.__healthy = bool(mcp_misc_0[5])

        # Extract and save the quad trace states
        for i in range(2, 6):
            self.__quad_traces[i - 2] = bool(mcp_misc_2[i])

        # Extract and save the global sensor channel states
        self.__sensor_states[0] = mcp_mon_0[6]
        for i in range(1, 5):
            self.__sensor_states[i] = bool(mcp_misc_0[i])

        # Extract and save the global latch states
        self.__latched_states = [bool(i) for i in mcp_misc_3]

        # Update internal all_enabled state based on current armed state since being disarmed
        # automatically turns off all quad outputs
        if not self.__armed:
            self.__all_enabled = False

        # Poll sensors for all quads also
        for quad in self.quad:
            quad.poll_all_sensors()

    def cleanup(self):
        """Clean up the PSCU server state.

        This method cleans up the state of the PSCU at shutdown, when called by the adapter.
        This is simply a case of setting an appropriate message on the PSCU LCD to indicate
        that the server is no longer running.
        """
        logging.debug("PSCU cleanup: setting display message")

        if not self.lcd_display_error:
            self.lcd.set_colour(LcdDisplay.YELLOW)
            self.lcd.set_content('\r   PSCU server is\r    NOT running\r\r')
