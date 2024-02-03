from bottle import request

from .rest_api_error import register_error_handler


def register_rest_interface(app, manager):

    register_error_handler(app)

    @app.post("/get_detector_settings")
    def get_detector_settings():
        return manager.get_detector_settings(request.json, request.remote_addr)

    @app.post("/set_detector_settings")
    def set_detector_settings():
        return manager.set_detector_settings(request.json, request.remote_addr)

    @app.post("/copy_user_files")
    def copy_user_files():
        return manager.copy_user_files(request.json, request.remote_addr)

    @app.post("/get_dap_settings")
    def get_dap_settings():
        return manager.get_dap_settings(request.json, request.remote_addr)

    @app.post("/set_dap_settings")
    def set_dap_settings():
        return manager.set_dap_settings(request.json, request.remote_addr)



