from bottle import request


def register_endpoints(manager, route, endpoints):
    for ep in endpoints:
        register_endpoint(manager, route, ep)

def register_endpoint(manager, route, endpoint):
    func = getattr(manager, endpoint)
    @route(f"/{endpoint}")
    def handler():
        return func(request.json, request.remote_addr)



