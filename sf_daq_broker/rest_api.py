import json

import bottle
import logging

import os

_logger = logging.getLogger(__name__)


def register_rest_interface(app, manager):

    @app.post("/retrieve_from_buffers")
    def retrieve_from_buffers():
        return manager.retrieve(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.error(500)
    def error_handler_500(error):
        bottle.response.content_type = 'application/json'
        bottle.response.status = 200

        error_text = str(error.exception)

        _logger.error(error_text)

        return json.dumps({"state": "error",
                           "status": error_text})
