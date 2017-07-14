from influxdb import InfluxDBClient
import logging
import requests
import json
import datetime
import time
import signal

db_host='te7aegserver.te.rl.ac.uk'
db_port=8086
db_name='lpd_test'

pscu_host='beagle03.aeg.lan'
pscu_port=8888

update_interval = 5.0

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

    def create_sensor_group_points(self, name, group_data, sensor_fields):

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

    def create_global_point(self, pscu_data):
        
        global_fields = [
            'allEnabled', 'armed', 'displayError', 'enableInterval', 'latched', 'overall'
        ]
        
        return self.create_point('global', pscu_data, global_fields)

    def create_fan_point(self, pscu_data):

        name = 'fan'
        fan_fields = [
            'setpoint_volts', 'currentspeed_volts', 'target', 'setpoint', 'currentspeed',
            'overall', 'mode', 'latched', 'tripped'
        ]

        return self.create_point(name, pscu_data[name], fan_fields)

    def create_pump_point(self, pscu_data):

        name = 'pump'
        pump_fields = [
           'flow', 'flow_volts', 'latched', 'mode', 'overall', 'setpoint',
           'setpoint_volts', 'tripped'
        ]
        return self.create_point(name, pscu_data[name], pump_fields)

    def create_position_point(self, pscu_data):

        name = 'position'
        position_fields = ['position', 'position_volts']
        return self.create_point(name, pscu_data, position_fields)

    def create_trace_point(self, pscu_data):

        name = 'trace'
        trace_fields = ['latched', 'overall']
        return self.create_point(name, pscu_data[name], trace_fields)

    def create_humidity_points(self, pscu_data):

        name = 'humidity'
        humidity_fields = [
            'disabled', 'humidity', 'humidity_volts', 'mode', 'setpoint',
            'setpoint_volts', 'trace', 'tripped'
        ]

        return self.create_sensor_group_points(name, pscu_data[name], humidity_fields)

    def create_temperature_points(self, pscu_data):

        name = 'temperature'
        temperature_fields = [
            'disabled', 'mode', 'setpoint', 'setpoint_volts',
            'temperature', 'temperature_volts',
            'trace', 'tripped'
        ]

        return self.create_sensor_group_points(name, pscu_data[name], temperature_fields)

    def create_quad_points(self, pscu_data):

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

        points = []
        points.append(self.create_global_point(pscu_data))
        points.append(self.create_fan_point(pscu_data))
        points.append(self.create_pump_point(pscu_data))
        points.append(self.create_position_point(pscu_data))
        points.append(self.create_trace_point(pscu_data))
        points.extend(self.create_humidity_points(pscu_data))
        points.extend(self.create_temperature_points(pscu_data))
        points.extend(self.create_quad_points(pscu_data))

        shared_tags = {
            'pscu_host': self.pscu_host,
        }
        write_ok = self.influx_client.write_points(points, tags=shared_tags)
        
        if not write_ok:
            logging.error("Failed to write PSCU update to DB")

    def run(self):

        while LpdLogger.do_update:
            self.now = datetime.datetime.today()

            self.do_pscu_update()
            
            logging.info("DB update completed")
            time.sleep(update_interval)

        logging.info("LpdLogger shutting down")

if __name__ == '__main__':
    
    logger = LpdLogger()
    logger.run()
