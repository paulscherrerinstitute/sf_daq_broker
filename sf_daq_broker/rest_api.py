import bottle

from .rest_api_error import register_error_handler


def register_rest_interface(app, manager):

    register_error_handler(app)

    @app.post("/retrieve_from_buffers")
    def retrieve_from_buffers():
        return manager.retrieve_from_buffers(bottle.request.json, bottle.request.remote_addr)

    @app.post("/take_pedestal")
    def take_pedestal():
        return manager.take_pedestal(bottle.request.json, bottle.request.remote_addr)

    @app.get("/get_allowed_detectors_list")
    def get_allowed_detectors_list():
        return manager.get_allowed_detectors_list(bottle.request.json, bottle.request.remote_addr)

    @app.get("/get_running_detectors_list")
    def get_running_detectors_list():
        return manager.get_running_detectors_list(bottle.request.json, bottle.request.remote_addr)

    @app.post("/power_on_detector")
    def power_on_detector():
        return manager.power_on_detector(bottle.request.json, bottle.request.remote_addr)

    @app.get("/get_next_run_number")
    def get_next_run_number():
        return manager.get_next_run_number(bottle.request.json, bottle.request.remote_addr)

    @app.get("/get_last_run_number")
    def get_last_run_number():
        return manager.get_last_run_number(bottle.request.json, bottle.request.remote_addr)

    @app.get("/get_pvlist")
    def get_pvlist():
        return manager.get_pvlist(bottle.request.json, bottle.request.remote_addr)

    @app.post("/set_pvlist")
    def set_pvlist():
        return manager.set_pvlist(bottle.request.json, bottle.request.remote_addr)

    @app.post("/close_pgroup_writing")
    def close_pgroup_writing():
        return manager.close_pgroup_writing(bottle.request.json, bottle.request.remote_addr)



