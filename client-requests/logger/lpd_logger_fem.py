from LpdDevice.LpdDevice import LpdDevice
from FemClient.FemClient import FemClientError
from influxdb import InfluxDBClient
import logging
import requests
import json
from datetime import datetime, timedelta
import time
import signal
from concurrent.futures import ThreadPoolExecutor

db_host='te7aegserver.te.rl.ac.uk'
db_port=8086
db_name='lpd_test_fem'

pscu_host='pscu'
pscu_port=8888

fem_mapping = [
    (0, '192.168.2.5', True),
    (1, '192.168.2.2', True),
    (2, '192.168.2.3', True),
    (3, '192.168.2.4', True),
    (4, '192.168.2.6', True),
    (5, '192.168.2.7', True),
    (6, '192.168.2.8', True),
    (7, '192.168.2.9', True),
    (8, '192.168.2.10', True),
    (9, '192.168.2.11', True),
    (10, '192.168.2.12', True),
    (11, '192.168.2.15', True),
    (12, '192.168.2.13', True),
    (13, '192.168.2.14', True),
    (14, '192.168.2.16', True),
    (15, '192.168.2.17', True),
]
fem_port=6969
fem_timeout = 1.0

update_interval = 5.0

max_error_display = 5

def shutdown_handler():
    LpdLogger.shutdown()

class LpdLogger(object):

    do_update = True

    @classmethod
    def shutdown(cls):
        cls.do_update = False
    
    def __init__(self):

        self.pscu_host = pscu_host

        logging.basicConfig(level=logging.INFO, format='%(levelname)1.1s %(asctime)s %(message)s', datefmt='%y%m%d %H:%M:%S')
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        logging.info("Opening connection to influxDB at {:s}:{:d}".format(db_host, db_port))
        self.influx_client = InfluxDBClient(host=db_host, port=db_port)

        existing_dbs =  self.influx_client.get_list_database()
        db_exists = False
        for db in existing_dbs:
            if db['name'] == db_name:
                db_exists = True
                break
        if db_exists:
            logging.info("OK, {} database exists already".format(db_name))
        else:
            logging.info("Creating {} database".format(db_name))
            self.influx_client.create_database(db_name)

        self.influx_client.switch_database(db_name)

        self.pscu_request_url = 'http://{}:{}/api/0.1/lpdpower/'.format(pscu_host, pscu_port)
        self.pscu_request_headers = {'Content-Type': 'application/json'}

        self.fem_idx = []
        self.fem_addr = []
        self.fem_devices = []
        self.fem_connected = []
        
        for (fem_idx, fem_addr, fem_active) in fem_mapping:
            
            if fem_active:
                
                self.fem_idx.append(fem_idx)
                self.fem_addr.append(fem_addr)
                
                the_device = LpdDevice()
                self.fem_devices.append(the_device)
                rc = the_device.open(fem_addr, fem_port, timeout=fem_timeout)
    
                if rc == LpdDevice.ERROR_OK:
                    logging.info("Opened connection to FEM {} device at address {}:{}".format(fem_idx, fem_addr, fem_port))
                    self.fem_connected.append(True)
                else:
                    logging.error("Failed to open FEM {} device: {}".format(fem_idx, the_device.errorStringGet()))
                    self.fem_connected.append(False)

        self.num_fems = len(self.fem_devices)

#         for fem in range(self.num_fems):
#             print self.fem_idx[fem], self.fem_addr[fem], self.fem_devices[fem], self.fem_connected[fem]
            
        signal.signal(signal.SIGINT, lambda signum, frame: shutdown_handler())

    def get_pscu_data(self):

        pscu_data = None
        
        try:
            response = requests.get(self.pscu_request_url, headers=self.pscu_request_headers)
            pscu_data = response.json()
        except Exception as e:
            logging.error('Request of data from PSCU failed: {}'.format(e))

        return pscu_data

    def create_point(self, measurement, data, fields, tags={}, extra_fields={}):
        
        point_fields = {}
        for field in fields:
            point_fields[field] = data[field]

        point_fields.update(extra_fields)
        point = {
            'measurement': measurement,
            'time': self.now,
            'fields': point_fields,
            'tags': tags,
        }
        return point

    def create_pscu_sensor_group_points(self, name, group_data, sensor_fields):

        extra_fields = {
            'latched': group_data['latched'],
            'overall': group_data['overall'],
        }

        group_data_sensors = group_data['sensors']

        group_points = []
        for sensor in range(len(group_data_sensors)):
            sensor_idx = str(sensor)
            sensor_data = group_data_sensors[sensor_idx]
            sensor_tags = {
                'sensor_idx': sensor,
                'sensor_name': sensor_data['name']
            }
            group_points.append(self.create_point(name, sensor_data, sensor_fields,
                                                  tags=sensor_tags, extra_fields=extra_fields))

        return group_points

    def create_pscu_global_point(self, pscu_data):
        
        global_fields = [
            'allEnabled', 'armed', 'displayError', 'enableInterval', 'latched', 'overall'
        ]
        
        return self.create_point('global', pscu_data, global_fields)

    def create_pscu_fan_point(self, pscu_data):

        name = 'fan'
        fan_fields = [
            'setpoint_volts', 'currentspeed_volts', 'target', 'setpoint', 'currentspeed',
            'overall', 'mode', 'latched', 'tripped'
        ]

        return self.create_point(name, pscu_data[name], fan_fields)

    def create_pscu_pump_point(self, pscu_data):

        name = 'pump'
        pump_fields = [
           'flow', 'flow_volts', 'latched', 'mode', 'overall', 'setpoint',
           'setpoint_volts', 'tripped'
        ]
        return self.create_point(name, pscu_data[name], pump_fields)

    def create_pscu_position_point(self, pscu_data):

        name = 'position'
        position_fields = ['position', 'position_volts']
        return self.create_point(name, pscu_data, position_fields)

    def create_pscu_trace_point(self, pscu_data):

        name = 'trace'
        trace_fields = ['latched', 'overall']
        return self.create_point(name, pscu_data[name], trace_fields)

    def create_pscu_humidity_points(self, pscu_data):

        name = 'humidity'
        humidity_fields = [
            'disabled', 'humidity', 'humidity_volts', 'mode', 'setpoint',
            'setpoint_volts', 'trace', 'tripped'
        ]

        return self.create_pscu_sensor_group_points(name, pscu_data[name], humidity_fields)

    def create_pscu_temperature_points(self, pscu_data):

        name = 'temperature'
        temperature_fields = [
            'disabled', 'mode', 'setpoint', 'setpoint_volts',
            'temperature', 'temperature_volts',
            'trace', 'tripped'
        ]

        return self.create_pscu_sensor_group_points(name, pscu_data[name], temperature_fields)

    def create_pscu_quad_points(self, pscu_data):

        name = 'quad'
        quad_fields = ['current', 'voltage', 'fusevoltage', 'enabled', 'fetfailed', 'fuseblown']
        
        quad_group_data = pscu_data['quad']['quads']
        quad_trace_data = pscu_data['quad']['trace']

        quad_channel_points = []
        for quad in range(len(quad_group_data)):
            quad_idx = str(quad)
            quad_extra_fields = {
                'trace': quad_trace_data[quad_idx],
                'supply': quad_group_data[quad_idx]['supply'],
            }
            channel_data = quad_group_data[quad_idx]['channels']
            for channel in range(len(channel_data)):
                channel_idx = str(channel)
                quad_tags = {
                    'quad_idx': quad_idx,
                    'channel_idx': channel_idx,
                }
                quad_channel_points.append(self.create_point('quad', channel_data[channel_idx], quad_fields,
                                                             tags=quad_tags, extra_fields=quad_extra_fields))
        return quad_channel_points

    def do_pscu_update(self):

        pscu_data = self.get_pscu_data()

        if pscu_data is not None:

            points = []
            points.append(self.create_pscu_global_point(pscu_data))
            points.append(self.create_pscu_fan_point(pscu_data))
            points.append(self.create_pscu_pump_point(pscu_data))
            points.append(self.create_pscu_position_point(pscu_data))
            points.append(self.create_pscu_trace_point(pscu_data))
            points.extend(self.create_pscu_humidity_points(pscu_data))
            points.extend(self.create_pscu_temperature_points(pscu_data))
            points.extend(self.create_pscu_quad_points(pscu_data))
    
            shared_tags = {
                'pscu_host': self.pscu_host,
            }
            
            try:
                self.influx_client.write_points(points, tags=shared_tags)
            except influxdb.exceptions.InfluxDBCLientError as e:
                logging.error("Got error updataing PSCU data in influxDB: {}".format(str(e)))
                
        else:
           logging.error("PSCU update errors encountered, not updating DB")

    def create_fem_sensor_points(self, fem_device):

        num_sensors = 16
        sensor_params = ['Temp', 'Voltage', 'Current']

        sensor_fields = [param.lower() for param in sensor_params]
        sensor_points = []

        for sensor_idx in range(num_sensors):
            
            sensor_data = {}
            sensor_tags = {
                'sensor_idx': sensor_idx
            }
            
            for (param, field) in zip(sensor_params, sensor_fields):
                param_name = 'sensor' + str(sensor_idx) + param
                (rc, sensor_data[field]) = fem_device.paramGet(param_name)
                if rc != LpdDevice.ERROR_OK:
                    self.fem_error_count += 1
                    if self.fem_error_count < max_error_display:
                        logging.error("Error reading parameter {} from FEM: rc={}: {}".format(
                            field, rc, fem_device.errorStringGet()))
                    if self.fem_error_count == max_error_display:
                        logging.error("Multiple parameter read errors from FEM, suppressing further error messages")
                        
            sensor_points.append(self.create_point('fem_sensors', sensor_data, sensor_fields, 
                                                   tags=sensor_tags))

        return sensor_points

    def create_fem_powercard_points(self, fem_device):

        num_powercards = 2
        powercard_params = ['powerCardTemp', 'femVoltage',  'femCurrent', 'digitalVoltage', 
                            'digitalCurrent', 'sensorBiasVoltage', 'sensorBiasCurrent', 
                            'sensorBias', 'sensorBiasEnable', 'asicPowerEnable', 
                            'powerCardFault', 'powerCardFemStatus', 'powerCardExtStatus', 
                            'powerCardOverCurrent', 'powerCardOverTemp', 'powerCardUnderTemp']

        powercard_fields = [param.lower() for param in powercard_params]
        powercard_points = []

        for powercard_idx in range(num_powercards):
            
            powercard_data = {}
            powercard_tags = {
                'powercard_idx': powercard_idx
            }

            for (param, field) in zip(powercard_params, powercard_fields):
                param_name = param + str(powercard_idx)
                (rc, powercard_data[field]) = fem_device.paramGet(param_name)
                if rc != LpdDevice.ERROR_OK:
                    self.fem_error_count += 1
                    if self.fem_error_count < max_error_display:
                        logging.error("Error reading parameter {} from FEM: rc={}: {}".format(
                            field, rc, fem_device.errorStringGet()))
                    if self.fem_error_count == max_error_display:
                        logging.error("Multiple parameter read errors from FEM, suppressing further error messages")
                        
            powercard_points.append(self.create_point('fem_powercard', powercard_data, powercard_fields,
                                                      tags=powercard_tags))

        return powercard_points

    def read_fem_temperature(self, fem_device, temp_channel):

        lm82_addr = 0x18
        fem_client = fem_device.femClient
        
        try:
            fem_client.i2cWrite(lm82_addr, (temp_channel))
            response = fem_client.i2cRead(lm82_addr, 1)
            temperature = float(response[0])
        except FemClientError as e:
            self.fem_error_count += 1
            if self.fem_error_count < max_error_display:              
                logging.error("Error reading temperature from FEM: {}".format(str(e)))
            if self.fem_error_count == max_error_display:
                logging.error("Multiple parameter read errors from FEM, suppressing further error messages")               
            temperature = None

        return temperature

    def create_fem_temperature_point(self, fem_device):

        temperature_data = {
            'pcb': self.read_fem_temperature(fem_device, 0),
            'fpga': self.read_fem_temperature(fem_device, 1),
        }

        return self.create_point('fem_temperature', temperature_data, temperature_data.keys())

    def do_fem_update(self, fem):
        
        fem_idx = self.fem_idx[fem]
        
        if self.fem_connected[fem]:
        
            self.fem_error_count = 0
            
            points = []
            points.extend(self.create_fem_sensor_points(self.fem_devices[fem]))
            points.extend(self.create_fem_powercard_points(self.fem_devices[fem]))
            points.append(self.create_fem_temperature_point(self.fem_devices[fem]))

            shared_tags = {
                'fem_idx': fem_idx,
                'fem_host': self.fem_addr[fem],
             }
            
            if self.fem_error_count == 0:
                try:
                    self.influx_client.write_points(points, tags=shared_tags)
                    fem_updated = True
                except influxdb.exceptions.InfluxDBClientError as e:
                    logging.error("Got error updating FEM {} data in influxDB: {}".format(fem_idx, str(e)))
            else:
                logging.error("FEM update errors encountered, not updating DB, closing FEM connection")
                self.fem_devices[fem].close()
                self.fem_connected[fem] = False

        if not self.fem_connected[fem]:
            
            rc = self.fem_devices[fem].open(self.fem_addr[fem], fem_port, timeout=fem_timeout)
            if rc == LpdDevice.ERROR_OK:
                logging.info("Re-opened connection to FEM {}".format(fem_idx))
                self.fem_connected[fem] = True
            else:
                logging.error("Failed to reopen connection to FEM {} : {}".format(fem_idx, self.fem_devices[fem].errorStringGet()))
                
    
    def do_fem_updates(self):

        thread_pool_size = 10 # Size of underlying connection pool used by requests library as part of DB access
        
        with ThreadPoolExecutor(max_workers = thread_pool_size) as executor:
            for fem in range(self.num_fems):
                executor.submit(self.do_fem_update, fem)


    def run(self):

        while LpdLogger.do_update:
            self.now = datetime.today()

            self.do_pscu_update()           
            self.do_fem_updates()

            logging.info("DB update completed in {:.2f}s".format((datetime.today() - self.now).total_seconds()))

            next_update = self.now + timedelta(seconds=update_interval)
            sleep_duration = (next_update - datetime.today()).total_seconds()
            if sleep_duration > 0.0:
                time.sleep(sleep_duration)
            else:
                logging.warning("Last update took longer than update interval, skipping sleep...")

        for fem_idx in range(self.num_fems):
            logging.info("Closing connection to FEM {}".format(fem_idx))
            self.fem_devices[fem_idx].close()

        logging.info("LpdLogger shutting down")

if __name__ == '__main__':
    
    logger = LpdLogger()
    logger.run()
