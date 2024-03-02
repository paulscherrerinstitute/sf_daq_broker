import socket
import unittest
from multiprocessing import Process
from time import sleep

import requests

from sf_daq_broker import broker


class TestBroker(unittest.TestCase):

    def setUp(self):
        self.broker_url = None
        self.rest_port = 11000

        # bottle server binds to this hostname
        self.hostname = socket.gethostname()

        self.broker_process = Process(
            target=broker.start_server, args=(self.broker_url, self.rest_port)
        )

        self.broker_process.start()
        sleep(1)


    def tearDown(self):
        self.broker_process.terminate()
        sleep(1)


    def test_REST_API(self):
        # test response status code for non-existent endpoint
        url = f"http://{self.hostname}:{self.rest_port}/this_endpoint_does_not_exist"
        response = requests.get(url)
        self.assertEqual(response.status_code, 404)

        # test response status codes for get endpoints
        get_endpoints = [
            "get_allowed_detectors_list",
            "get_running_detectors_list",
            "get_next_run_number",
            "get_last_run_number",
            "get_pvlist"
        ]
        for ep in get_endpoints:
            response = requests.get(f"http://{self.hostname}:{self.rest_port}/{ep}")
            status = response.json()["status"]
            self.assertIn(status, ["ok", "failed"])



