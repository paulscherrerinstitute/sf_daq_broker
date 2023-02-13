import json

import bottle
import logging

import os

_logger = logging.getLogger(__name__)


def register_rest_interface(app, manager):

    @app.post("/retrieve_from_buffers")
    def retrieve_from_buffers():
        return manager.retrieve(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.post("/take_pedestal")
    def take_pedestal():
        return manager.take_pedestal(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.get("/get_allowed_detectors_list")
    def get_allowed_detectors_list():
        return manager.get_list_allowed_detectors(remote_ip=bottle.request.remote_addr)

    @app.get("/get_running_detectors_list")
    def get_running_detectors_list():
        return manager.get_list_running_detectors(remote_ip=bottle.request.remote_addr)

    @app.post("/power_on_detector")
    def power_on_detector():
        return manager.power_on_detector(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.get("/get_next_run_number")
    def get_next_run_number():
        return manager.get_next_run_number(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.get("/get_last_run_number")
    def get_last_run_number():
        return manager.get_next_run_number(request=bottle.request.json, remote_ip=bottle.request.remote_addr, increment_run_number=False)

    @app.get("/get_pvlist")
    def get_pvlist():
        return manager.get_pvlist(remote_ip=bottle.request.remote_addr)

    @app.post("/set_pvlist")
    def set_pvlist():
        return manager.set_pvlist(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.post("/close_pgroup_writing")
    def close_pgroup_writing():
        return manager.close_pgroup_writing(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.error(500)
    def error_handler_500(error):
        bottle.response.content_type = 'application/json'
        bottle.response.status = 200

        error_text = str(error.exception)

        _logger.error(error_text)

        return json.dumps({"state": "error",
                           "status": error_text})
