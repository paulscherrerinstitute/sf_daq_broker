from .endpoints import register_endpoints
from .error_handler import register_error_handler


def register_rest_api(app, manager, endpoints_post=None, endpoints_get=None):
    register_error_handler(app)

    if endpoints_post:
        register_endpoints(manager, app.post, endpoints_post)

    if endpoints_get:
        register_endpoints(manager, app.get, endpoints_get)



