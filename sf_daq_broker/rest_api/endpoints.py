from bottle import request

from .return_status import return_status


def register_endpoints(manager, route, endpoints):
    for ep in endpoints:
        register_endpoint(manager, route, ep)

def register_endpoint(manager, route, endpoint):
    func = getattr(manager, endpoint)
    @route(f"/{endpoint}")
    @return_status
    def handler():
        return func(request.json, request.remote_addr)



