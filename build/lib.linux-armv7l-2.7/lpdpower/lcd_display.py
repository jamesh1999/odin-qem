"""LcdDisplay - display driver class for LPD PSCU front-panel LCD.

This class implements control of the LPD PSCU fonrt-panel LCD, which is interfaced
via the UsbLcd class and an Adafruit USB LCD backpack. This class implements a number
of display pages, which can be cycled through via next/previous methods. The page
list is easy to extend via a page registration mechanism and standardised rendering


Tim Nicholls, STFC Application Engineering Group.
"""

from lpdpower.usblcd import UsbLcd

from functools import partial
import time


class LcdDisplayError(Exception):
    """LCDDisplayError provides a simple exception class for LCDDisplay."""

    pass


class LcdDisplay(object):
    """LCDDisplay class.

    This class implements support for the PSCU front-panel LCD.
    """

    # Definition of backlight colours imported from the UsbLcd class
    GREEN = UsbLcd.GREEN
    RED = UsbLcd.RED
    YELLOW = UsbLcd.YELLOW
    BLUE = UsbLcd.BLUE
    WHITE = UsbLcd.WHITE

    def __init__(self, pscu, serial_dev, baud=57600, rows=4, cols=20):
        """Initialise the LcdDisplay device.

        This initialises the LcdDisplay object, opening the USB device and
        creating a list of registered pages, which are methods that return the
        text of display pages to render.

        :param pscu: PSCU device to retrieve data from.
        :param serial_dev: serial device for the USB interface, e.g. dev/ttyUSB0
        :param baud: baud rate for the USB serial device
        :oaram rows: number of LCD rows
        :param cols: number of LCD columns
        """
        # Store the PSCU object for subsequent access
        self.pscu = pscu

        # Initialse the UsvLcd device
        try:
            self.lcd = UsbLcd(serial_dev, baud, rows, cols)
        except Exception as e:
            raise LcdDisplayError("Failed to initialise LCD: {}".format(e))

        # Clear the display
        self.lcd.clear()

        # Set up list of registered pages and append appopriate methods
        self.current_page = 0
        self.registered_pages = []

        self.registered_pages.append(self.overview_page)

        self.temps_per_page = 2
        self.num_temp_pages = int(round(float(self.pscu.num_temperatures) / self.temps_per_page))

        for page in range(self.num_temp_pages):
            self.registered_pages.append(partial(self.temperature_page, page))

        self.registered_pages.append(self.humidity_page)
        self.registered_pages.append(self.fan_page)
        self.registered_pages.append(self.pump_page)
        self.registered_pages.append(self.position_page)
        self.registered_pages.append(self.trace_page)

        self.registered_pages.append(self.quad_supply_page)

        for quad in range(4):
            for chan in range(2):
                self.registered_pages.append(partial(self.quad_page, quad, chan*2))

        # self.registered_pages.append(self.system_page)

        # Set up LCD display buffer, colour, time format
        self.lcd_buffer = ""
        self.lcd_colour = 0

        self.time_format = '%H:%M:%S'   # %d-%b-%y'

    def set_colour(self, colour):
        """Set the backlight colour of the LCD.

        This method sets the backlight colour of the LCD to the specified value,
        which is typically a class-level definition imported from UsbLcd, where
        the colour is described as tuple of byte-wide RGB values.

        :param colour; byte-width RGB tuple of colour, e.g. LcdDisplay.RED
        """
        if colour != self.lcd_colour:
            self.lcd.set_backlight_colour(colour)
            self.lcd_colour = colour

    def next_page(self):
        """Move the LCD display to the next registered page.

        This method updates the current LCD page to the next registered page. Note that the
        display will not change until the update() method is called. The pages are cycled
        through modulo the number of registered pages.
        """
        self.current_page += 1
        self.current_page %= len(self.registered_pages)

    def previous_page(self):
        """Move the LCD display to the previous registered page.

        This method updates the current LCD page to the previous registered page. Note that the
        display will not change until the update() method is called. The pages are cycled
        through modulo the number of registered pages.
        """
        self.current_page -= 1
        self.current_page %= len(self.registered_pages)

    def update(self):
        """Update the displayed content on the LCD.

        This method updates the display with the content from the current registered page.
        """
        content = self.registered_pages[self.current_page]()
        self.set_content(content)

    def set_content(self, content):
        """Set the displayed content on the LCD.

        This method sets the displayed content on the LCD. The content is compared with the
        internal buffer and the display only updated on change to avoid excessive updates or
        display flicker.
        """
        if content != self.lcd_buffer:
            self.lcd_buffer = content
            self.lcd.home()
            self.lcd.write(self.lcd_buffer)

    def page_header(self):
        """Render the page header in a standard format.

        This method returns a string containing a standardised page header, which can be used
        by all registered page methods. The header typically contains the current time and a
        m/n of the current page.

        :return: rendered page header as a string
        """
        header = '{:9s}      {:2d}/{:2d}'.format(
            time.strftime(self.time_format), self.current_page+1, len(self.registered_pages)
        )

        return header

    def overview_page(self):
        """Render the PSCU overview status page.

        This method renders an overview page, showing the general state of the PSCU.

        :return: rendered page as a string
        """
        healthy = self.pscu.get_health()
        all_latched = all(self.pscu.get_all_latched())
        armed = self.pscu.get_armed()

        content = self.page_header()
        content += 'System  : {}\r'.format('Healthy' if healthy else 'ERROR')
        content += 'Latched : {}\r'.format('No' if all_latched else 'YES')
        content += 'Armed   : {}\r'.format('Yes' if armed else 'No')

        return content

    def format_state_str(self, output, latched):
        """Format a standard state string for a PSCU parameter.

        This method is used to format a standard state string for a PSCU parameter where it
        may have OK, latched and tripped states.

        :output output: bool state of a given PSCU output parameter
        :param latched: latched state of the PSCU output parameter
        :return: formatted state as a string
        """
        state_str = ''
        if output:
            state_str = 'OK{}'.format('' if latched else '/Latch')
        else:
            state_str = 'TRIPPED'

        return state_str

    def temperature_page(self, page):
        """Render a PSCU temperature sensor status page.

        This method renders a temperature page, showing the state of a set of the PSCU
        temperature sensors. The page argument is used to determine which set of sensors to
        display.

        :param page: which page of sesnors to display
        :return: rendered page as a string
        """
        content = self.page_header()

        num_temp_vals = self.pscu.num_temperatures

        start_chan = page * self.temps_per_page
        end_chan = start_chan + self.temps_per_page

        state_str = self.format_state_str(
            self.pscu.get_temperature_state(), self.pscu.get_temperature_latched()
        )

        content += 'Temp {}/{}: {}\r'.format(page+1, self.num_temp_pages, state_str)

        for chan in range(start_chan, end_chan):
            if chan < num_temp_vals:
                chan_disabled = self.pscu.get_temperature_disabled(chan)
                if chan_disabled:
                    temp_disp = '{:2d}:{:17s}'.format(chan+1, 'N/C')
                else:
                    chan_name = ''.join(self.pscu.get_temperature_name(chan).split(' '))
                    chan_temp = self.pscu.get_temperature(chan)
                    chan_trip = '*' if self.pscu.get_temperature_tripped(chan) else ' '
                    temp_disp = '{:2d}:{: <10.10s}:{:4.1f}C{:1s}'.format(
                        chan+1, chan_name, chan_temp, chan_trip
                    )
            else:
                temp_disp = '\r'

            content += temp_disp

        return content

    def humidity_page(self):
        """Render the PSCU humidity status page.

        This method renders a humidity page, showing the state of the PSCU humidity sensors.

        :return: rendered page as a string
        """
        content = self.page_header()

        state_str = self.format_state_str(
            self.pscu.get_humidity_state(), self.pscu.get_humidity_latched())

        content += 'Humidity: {}\r'.format(state_str)

        for chan in range(self.pscu.num_humidities):
            chan_disabled = self.pscu.get_humidity_disabled(chan)
            if chan_disabled:
                content += '{:2d}:{:17s}'.format(chan+1, 'N/C')
            else:
                chan_name = ''.join(self.pscu.get_humidity_name(chan).split(' '))
                chan_humid = self.pscu.get_humidity(chan)
                chan_trip = '*' if self.pscu.get_humidity_tripped(chan) else ' '
                content += '{:2d}:{: <10.10s}:{:4.1f}%{:1s}'.format(
                    chan+1, chan_name, chan_humid, chan_trip
                )

        return content

    def fan_page(self):
        """Render the PSCU fan status page.

        This method renders a fan page, showing the state of the LPD cooling fan system.

        :return: rendered page as a string
        """
        content = self.page_header()

        state_str = self.format_state_str(self.pscu.get_fan_state(), self.pscu.get_fan_latched())

        content += 'Fan: {}\r'.format(state_str)
        content += 'Target: {:6.1f}%\r'.format(self.pscu.get_fan_target())
        content += 'Speed : {:6.1f}rpm\r'.format(self.pscu.get_fan_speed())
        content += time.strftime(self.time_format)

        return content

    def pump_page(self):
        """Render the PSCU pump status page.

        This method renders an overview page, showing the state of the LPD pump system.

        :return: rendered page as a string
        """
        content = self.page_header()

        state_str = self.format_state_str(self.pscu.get_pump_state(), self.pscu.get_pump_latched())

        content += 'Pump: {}\r'.format(state_str)
        content += 'Flow: {:.1f}l/min\r'.format(self.pscu.get_pump_flow())
        content += '\r'

        return content

    def position_page(self):
        """Render the PSCU detector position page.

        This method renders a page showing the state of the detector position readout.

        :return: rendered page as a string
        """
        content = self.page_header()

        content += 'Position: {:.2f}mm\r'.format(self.pscu.get_position())
        content += '** DO NOT EXCEED ** '
        content += '**  +/-35.5mm!   ** '

        return content

    def format_trace_str(self, traces):
        """Format a trace status output string.

        This method is used to format a simple trace status string, showing a '*' or '_' for
        trace good or trace missing respectively of each of a list of trace status values.

        :return: rendered trace output string
        """
        trace_str = ''.join(['*' if trace else '_' for trace in traces])
        return trace_str

    def trace_page(self):
        """Render the PSCU trace status page.

        This method renders a trace page, showing the the state of the various trace parameters
        monitored by the PSCU system.

        :return: rendered page as a string
        """
        content = self.page_header()

        state_str = self.format_state_str(
            self.pscu.get_trace_state(), self.pscu.get_trace_latched()
        )

        temp_traces = [
            self.pscu.get_temperature_trace(chan) for chan in range(self.pscu.num_temperatures)
        ]
        humidity_traces = [
            self.pscu.get_humidity_trace(chan) for chan in range(self.pscu.num_humidities)
        ]
        quad_traces = [
            self.pscu.get_quad_trace(chan) for chan in range(self.pscu.num_quads)
        ]

        content += 'Trace: {}\r'.format(state_str)
        content += 'Temp: {}\r'.format(self.format_trace_str(temp_traces))
        content += 'Hum: {} Quad: {}\r'.format(
            self.format_trace_str(humidity_traces),
            self.format_trace_str(quad_traces)
        )

        return content

    def quad_supply_page(self):
        """Render the PSCU quad supply page.

        The method renders a quad supply page, showing the measured 48V supplies to each of the
        LPD quad boxes.

        :return: rendered page as a string
        """
        content = self.page_header()

        content += 'Quad supplies\r'

        quad_supply_volts = [self.pscu.quad[quad].get_supply_voltage() for quad in range(4)]

        content += 'A: {:4.1f}V B:{:4.1f}V\r'.format(quad_supply_volts[0], quad_supply_volts[1])
        content += 'C: {:4.1f}V D:{:4.1f}V\r'.format(quad_supply_volts[2], quad_supply_volts[3])

        return content

    def quad_page(self, quad, start_chan):
        """Render the PSCU quad status page.

        This method renders a PSCU quad satus page, showing voltage, current, fuse and enable
        status values for a given quad and channel pair. There are two such pages per quad.

        :param quad: which quad to display
        :param start_chan: which channel pair to start the display at
        :return: rendered page as a string
        """
        content = self.page_header()

        quad_chans = [start_chan, start_chan+1]
        quad_name = ['A', 'B', 'C', 'D'][quad]
        content += 'Quad: {} Chans: {}/{} \r'.format(quad_name, *[chan+1 for chan in quad_chans])

        for quad_chan in quad_chans:
            quad_enable = ('ON ' if self.pscu.quad[quad].get_enable(quad_chan) else 'OFF')
            quad_volts = self.pscu.quad[quad].get_channel_voltage(quad_chan)
            quad_fuse_volts = self.pscu.quad[quad].get_fuse_voltage(quad_chan)
            quad_current = self.pscu.quad[quad].get_channel_current(quad_chan)

            # If either of the FET failed or fuse blown flags are true, display an error message,
            # otherwise show the channel ouptut voltage and current.
            if self.pscu.quad[quad].get_fet_failed(quad_chan):
                content += '{}:FET failed?({:4.1f}V)'.format(
                    quad_chan+1, quad_fuse_volts)
            elif self.pscu.quad[quad].get_fuse_blown(quad_chan):
                content += '{}:Fuse blown?({:4.1f}V)'.format(
                    quad_chan+1, quad_fuse_volts)
            else:
                content += '{}:{} {:4.1f}V {:4.1f}A OK'.format(
                    quad_chan+1, quad_enable, quad_volts, quad_current)

        return content

    def system_page(self):
        """Render the PSCU system status page.

        This method renders a system-level information status page.
        """
        content = self.page_header()
        content += 'System Info\r'
        content += 'TODO'
        content += '\r\r'

        return content
