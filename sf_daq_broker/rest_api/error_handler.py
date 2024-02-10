import logging

import bottle

from sf_daq_broker.utils import json_obj_to_str

_logger = logging.getLogger(__name__)



def register_error_handler(app):

    @app.error(500)
    def error_handler_500(error):
        bottle.response.content_type = "application/json"
        bottle.response.status = 200

        error_text = str(error.exception)

        _logger.error(error_text)

        return json_obj_to_str({
            "state": "error",
            "status": error_text
        })



