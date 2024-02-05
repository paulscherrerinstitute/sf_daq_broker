import json
import logging

import bottle


_logger = logging.getLogger(__name__)



def register_error_handler(app):

    @app.error(500)
    def error_handler_500(error):
        bottle.response.content_type = "application/json"
        bottle.response.status = 200

        error_text = str(error.exception)

        _logger.error(error_text)

        return json.dumps({
            "state": "error",
            "status": error_text
        })



