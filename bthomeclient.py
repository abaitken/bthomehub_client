import json
import math
import random
from urllib.parse import quote

import requests

from exception import AuthenticationException


class BtHomeClient(object):
    BT_HOME_HOST = 'bthomehub.home'
    DEFAULT_TIMEOUT = 10

    AUTH_COOKIE_OBJ = {'req_id': 1,
                       'sess_id': 0,
                       'basic': False,
                       'user': 'guest',
                       'dataModel':
                           {'name': 'Internal',
                            'nss': [
                                {
                                    'name': 'gtw',
                                    'uri': 'http://sagemcom.com/gateway-data'
                                }
                            ]},
                       'ha1': 'ca6e4940afd41d8cd98f00b204e9800998ecf8427e830e7a046fd8d92ecec8e4',
                       'nonce': ''}

    AUTH_REQUEST_OBJ = authRequestObj = {
        'request': {
            'id': 0,
            'session-id': 0,
            'priority': True,
            'actions': [
                {
                    'id': 0,
                    'method': 'logIn',
                    'parameters': {
                        'user': 'guest',
                        'persistent': True,
                        'session-options': {
                            'nss': [
                                {
                                    'name': 'gtw',
                                    'uri': 'http://sagemcom.com/gateway-data'
                                }
                            ],
                            'language': 'ident',
                            'context-flags': {
                                'get-content-name': True,
                                'local-time': True
                            },
                            'capability-depth': 2,
                            'capability-flags': {
                                'name': True,
                                'default-value': False,
                                'restriction': True,
                                'description': False
                            },
                            'time-format': 'ISO_8601'
                        }
                    }
                }
            ],
            'cnonce': 745670196,
            'auth-key': '06a19e589dc848a89675748aa2d509b3'
        }
    }

    def __init__(self, host=BT_HOME_HOST, timeout=DEFAULT_TIMEOUT):
        self.url = 'http://{}/cgi/json-req'.format(host)
        self.timeout = timeout

    def __authenticate(self):
        headers = {
            "Cookie": "lang=en; session=" + quote(json.dumps(self.AUTH_COOKIE_OBJ).encode("utf-8"))
        }
        request = "req=" + quote(json.dumps(self.AUTH_REQUEST_OBJ, sort_keys=True).encode("utf-8"))

        response = requests.post(self.url, data=request, headers=headers, timeout=self.timeout)

        if response.status_code != 200:
            raise AuthenticationException('Failed to authenticate. Status code: ' + response.status_code)
        self.authentication = json.loads(response.text)['reply']['actions'][0]['callbacks'][0]['parameters']

    def get_devices(self):

        if not self.authentication:
            self.__authenticate()

        client_nonce = str(math.floor(4294967295 * (random.uniform(0, 1))))
        request_id = '1'
        server_nonce = self.authentication['nonce']
        session_id = self.authentication['id']
        user = 'guest'
        password = 'd41d8cd98f00b204e9800998ecf8427e'

        auth_hash = md5_hex(user + ':' + server_nonce + ':' + password)
        auth_key = md5_hex(auth_hash + ':' + request_id + ':' + client_nonce + ':JSON:/cgi/json-req')

        listCookieObj = {
            'req_id': request_id,
            'sess_id': session_id,
            'basic': False,
            'user': 'guest',
            'dataModel': {
                'name': 'Internal',
                'nss': [
                    {
                        'name': 'gtw',
                        'uri': 'http://sagemcom.com/gateway-data'
                    }
                ]
            },
            'ha1': '2d9a6f39b6d41d8cd98f00b204e9800998ecf8427eba8d73fbd3de28879da7dd',
            'nonce': server_nonce
        }

        listReqObj = {
            'request': {
                'id': request_id,
                'session-id': session_id,
                'priority': False,
                'actions': [
                    {
                        'id': 1,
                        'method': 'getValue',
                        'xpath': 'Device/Hosts/Hosts',
                        'options': {
                            'capability-flags': {
                                'interface': True
                            }
                        }
                    }
                ],
                'cnonce': client_nonce,
                'auth-key': auth_key
            }
        }


headers = {
    "Cookie": "lang=en; session=" + quote(json.dumps(listCookieObj).encode("utf-8"))
}

request = "req=" + quote(json.dumps(listReqObj, sort_keys=True).encode("utf-8"))
try:
    response = requests.post(url, data=request, headers=headers, timeout=TIMEOUT)
except (requests.exceptions.Timeout, requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
    _LOGGER.exception("Devices - Connection to the router failed")
else:
    if response.status_code == 200:
        return _parse_homehub_response(response.text)
    else:
        _LOGGER.error("Invalid response from Home Hub: %s", response)

return None


def _parse_homehub_response(data_str):
    """Parse the BT Home Hub 5 data format."""
    known_devices = json.loads(data_str)['reply']['actions'][0]['callbacks'][0]['parameters']['value']

    devices = {}

    for device in known_devices:
        mac = device['PhysAddress'].upper()
        name = device['HostName'] or mac.lower().replace('-', '')
        if device['Active']:
            devices[mac] = name

    return devices


def md5_hex(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()
