"""adapter.py - ODIN API adapter for the LpdPower plugin.

This module implements the LPDPowerAdapter API adapter plugin for the ODIN server.

James Hogge, STFC Application Engineering Group.
"""
from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from tornado.escape import json_decode
from tornado.ioloop import IOLoop
from lpdpower.pscu_data import PSCUData, PSCUDataError


class LPDPowerAdapter(ApiAdapter):
    """LPDPowerAdapter - ODIN API adapter class for the lpdpower plugin.

    This class implements an API adapter for the lpdpower plugin to be used in the ODIN
    server to control the LPD Power Supply Control Unit (PSCU). The adapter transforms the
    appropriate HTTP GET and PUT requests into accesses to the underlying PSCUData
    representation of the parameters of the PSCU.
    """

    def __init__(self, **kwargs):
        """Initialise the LPDPowerAdapter instance.

        This constructor initialises the adapter instance, extracting the appropriate
        configuration options passed in by the server, creating a PSCUData object to
        interact with the PSCU hardware and starting a period update loop within
        the tornado IOLoop instance to handle background update tasks.

        :param kwargs: keyword argument list supplied by the calling server
        """
        # Initialise the superclass ApiAdapter - this parses the keyword arguments
        # into the options used below.
        super(LPDPowerAdapter, self).__init__(**kwargs)

        # Retrieve adapter options from incoming argument list
        self.update_interval = float(self.options.get('update_interval', 0.05))
        pscu_data_options = {
            'quad_enable_interval': float(self.options.get('quad_enable_interval', 1.0)),
            'detector_position_offset': float(self.options.get('detector_position_offset', 0.0)),
        }

        # Create a PSCUData instance
        self.pscuData = PSCUData(**pscu_data_options)

        # Start the update loop
        self.update_loop()

    @request_types('application/json')
    @response_types('application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request routed to the adapter. This passes
        the path of the request to the underlying PSCUData instance, where it is interpreted
        and returned as a dictionary containing the appropriate parameter tree.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response from the PSCU
        """
        try:
            response = self.pscuData.get(path)
            status_code = 200
        except PSCUDataError as e:
            response = {'error': str(e)}
            status_code = 400
        return ApiAdapterResponse(response, status_code=status_code)

    @request_types('application/json')
    @response_types('application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request routed to the adapter. This decodes the
        JSON body of the request into a dict, and passes the result with the request path, to
        the underlying PSCUData instance set method, where it is parsed and the appropriate
        actions performed on the PSCU.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response from the PSCU.
        """
        try:
            data = json_decode(request.body)
            self.pscuData.set(path, data)
            response = self.pscuData.get(path)
            status_code = 200
        except PSCUDataError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400
        return ApiAdapterResponse(response, status_code=status_code)

    def update_loop(self):
        """Handle background update loop tasks.

        This method handles background update tasks executed periodically in the tornado
        IOLoop instance. This included handling deferred PSCU commands, updating the front-panel
        LCD and polling all sensors.
        """
        # Handle background tasks
        self.pscuData.pscu.handle_deferred()
        self.pscuData.pscu.update_lcd()
        self.pscuData.pscu.poll_all_sensors()

        # Schedule the update loop to run in the IOLoop instance again after appropriate
        # interval
        IOLoop.instance().call_later(self.update_interval, self.update_loop)

    def cleanup(self):
        """Clean up the state of the adapter at shutdown.

        This method is called by the ODIN server at shutdown to allow the adapter to
        clean up its internal state and that of any connected hardware.
        """
        self.pscuData.pscu.cleanup()
