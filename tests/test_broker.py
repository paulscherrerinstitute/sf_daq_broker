import socket
import unittest
from multiprocessing import Process
from time import sleep

import requests

from sf_daq_broker import broker


ENDPOINTS_GET = [
    "get_allowed_detectors_list",
    "get_running_detectors_list",
    "get_next_run_number",
    "get_last_run_number",
    "get_pvlist"
]



class TestGeneral(unittest.TestCase):

    def test_all_get_endpoints_known(self):
        endpoints_broker = set(broker.ENDPOINTS_GET)
        endpoints_tested = set(ENDPOINTS_GET)
        self.assertEqual(endpoints_broker, endpoints_tested)



class TestBroker(unittest.TestCase):

    def setUp(self):
        broker_url = None
        rest_port = 11000

        # bottle server binds to this hostname
        hostname = socket.gethostname()
        self.address = f"http://{hostname}:{rest_port}"

        self.broker_process = Process(
            target=broker.start_server, args=(broker_url, rest_port)
        )

        self.broker_process.start()
        sleep(1)


    def tearDown(self):
        self.broker_process.terminate()
        sleep(1)


    def test_response_code_nonexistent_endpoint(self):
        url = f"{self.address}/this_endpoint_does_not_exist"

        response = requests.get(url)
        self.assertEqual(response.status_code, 404)

        response = requests.post(url)
        self.assertEqual(response.status_code, 404)


    def test_response_code_get_endpoints(self):
        for ep in ENDPOINTS_GET:
            response = requests.get(f"{self.address}/{ep}")
            self.assertEqual(response.status_code, 200)


    def test_response_status_get_endpoints(self):
        for ep in ENDPOINTS_GET:
            response = requests.get(f"{self.address}/{ep}")
            status = response.json()["status"]
            self.assertIn(status, ["ok", "failed"])



