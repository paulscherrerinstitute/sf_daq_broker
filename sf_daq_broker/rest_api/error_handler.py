import logging

import bottle

from sf_daq_broker.utils import json_obj_to_str


_logger = logging.getLogger(__name__)



def register_error_handler(app):

    @app.error(500)
    def error_handler_500(error):
        bottle.response.content_type = "application/json"
        bottle.response.status = 200

        exc = error.exception

        _logger.exception("Internal Server Error (500)", exc_info=exc)

        return json_obj_to_str({
            "status": "error",
            "message": str(exc),
            "exception": type(exc).__name__
        })



