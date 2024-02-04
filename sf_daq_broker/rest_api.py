from bottle import request

from .rest_api_error import register_error_handler


def register_rest_interface(app, manager, endpoints_post=None, endpoints_get=None):
    register_error_handler(app)

    if endpoints_post:
        register_endpoints(manager, app.post, endpoints_post)

    if endpoints_get:
        register_endpoints(manager, app.get, endpoints_get)


def register_endpoints(manager, route, endpoints):
    for ep in endpoints:
        register_endpoint(manager, route, ep)

def register_endpoint(manager, route, endpoint):
    func = getattr(manager, endpoint)
    @route(f"/{endpoint}")
    def handler():
        return func(request.json, request.remote_addr)



