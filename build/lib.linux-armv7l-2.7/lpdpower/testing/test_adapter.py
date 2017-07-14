"""Test LpdPowerAdapter class from lpdpower.

Tim Nicholls, STFC Application Engineering Group
"""

import sys
if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, MagicMock, call, patch
else:                         # pragma: no cover
    from mock import Mock, MagicMock, call, patch

import json
from nose.tools import *

sys.modules['smbus'] = Mock()
sys.modules['serial'] = Mock()
sys.modules['Adafruit_BBIO'] = Mock()
sys.modules['Adafruit_BBIO.GPIO'] = Mock()
from lpdpower.adapter import LPDPowerAdapter

class TestLPDPowerAdapter():

    @classmethod
    @patch('lpdpower.pscu_data.PSCU')
    def setup_class(cls, mock_pscu):

        cls.pscu = mock_pscu
        cls.adapter = LPDPowerAdapter()

        cls.request = Mock()
        cls.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def test_get_toplevel(self):

        response = self.adapter.get('', self.request)
        assert_equal(response.status_code, 200)
        assert_equal(type(response.data), dict)

    def test_get_param(self):

        response = self.adapter.get('position', self.request)
        assert_equal(response.status_code, 200)
        assert_true('position' in response.data)

    def test_get_bad_path(self):

        bad_path = 'missing/path'
        response = self.adapter.get(bad_path, self.request)
        assert_equal(response.status_code, 400)
        assert_true('error' in response.data)
        assert_equal(response.data['error'], 'The path {} is invalid'.format(bad_path))

    def test_put(self):

        request_body = {'allEnabled': True}
        self.request.body = json.dumps(request_body)
        response = self.adapter.put('', self.request)
        assert_equal(response.status_code, 200)
        assert_true('allEnabled' in response.data)

    def test_put_bad_path(self):

        bad_path = 'does/not/exist'
        request_body = {'value': 1.2345}
        self.request.body = json.dumps(request_body)
        response = self.adapter.put(bad_path, self.request)
        assert_equal(response.status_code, 400)
        assert_true('error' in response.data)
        assert_true(response.data['error'], "Invalid path: {}".format(bad_path))

    def test_put_invalid_request(self):

        self.request.body = 'this is not json'
        response = self.adapter.put('', self.request)
        assert_equal(response.status_code, 400)
        assert_true('error' in response.data)
        assert_true(response.data['error'], 'Failed to decode PUT request body: No JSON object could be decoded')

    def test_adapter_cleanup(self):

        self.adapter.cleanup()
        self.pscu.assert_has_calls([call().cleanup()])
