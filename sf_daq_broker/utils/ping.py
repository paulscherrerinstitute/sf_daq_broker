import socket
from concurrent.futures import ThreadPoolExecutor
from functools import partial


def ping_many(hosts, port=23, timeout=2, max_workers=None):
    max_workers = max_workers or len(hosts)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        primed_ping = partial(ping, port=port, timeout=timeout)
        pings = executor.map(primed_ping, hosts)
        return dict(zip(hosts, pings))


def ping(host, port=23, timeout=2): # telnet is port 23
    address = (host, port)
    try:
        with socket.create_connection(address, timeout):
            return True
    except OSError:
        return False



