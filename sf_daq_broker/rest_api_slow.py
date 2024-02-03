import bottle

from .rest_api_error import register_error_handler


def register_rest_interface(app, manager):

    register_error_handler(app)

    @app.post("/get_detector_settings")
    def get_detector_settings():
        return manager.get_detector_settings(bottle.request.json, bottle.request.remote_addr)

    @app.post("/set_detector_settings")
    def set_detector_settings():
        return manager.set_detector_settings(bottle.request.json, bottle.request.remote_addr)

    @app.post("/copy_user_files")
    def copy_user_files():
        return manager.copy_user_files(bottle.request.json, bottle.request.remote_addr)

    @app.post("/get_dap_settings")
    def get_dap_settings():
        return manager.get_dap_settings(bottle.request.json, bottle.request.remote_addr)

    @app.post("/set_dap_settings")
    def set_dap_settings():
        return manager.set_dap_settings(bottle.request.json, bottle.request.remote_addr)



