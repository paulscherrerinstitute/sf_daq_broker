import json
import logging

import bottle

_logger = logging.getLogger(__name__)


def register_rest_interface(app, manager):

    @app.post("/get_detector_settings")
    def get_detector_settings():
        return manager.get_detector_settings(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.post("/set_detector_settings")
    def set_detector_settings():
        return manager.set_detector_settings(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.post("/copy_user_files")
    def copy_user_files():
        return manager.copy_user_files(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.post("/get_dap_settings")
    def get_dap_settings():
        return manager.get_dap_settings(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.post("/set_dap_settings")
    def set_dap_settings():
        return manager.set_dap_settings(request=bottle.request.json, remote_ip=bottle.request.remote_addr)

    @app.error(500)
    def error_handler_500(error):
        bottle.response.content_type = "application/json"
        bottle.response.status = 200

        error_text = str(error.exception)

        _logger.error(error_text)

        return json.dumps({"state": "error",
                           "status": error_text})
