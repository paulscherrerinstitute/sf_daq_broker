
SUBNET_TO_BEAMLINE = {
    "129.129.242": "alvra",
    "129.129.243": "bernina",
    "129.129.244": "cristallina",
    "129.129.245": "diavolezza",
    "129.129.246": "maloja",
    "129.129.247": "furka"
}


def get_beamline(ip):
    subnet = get_subnet(ip)
    try:
        return SUBNET_TO_BEAMLINE[subnet]
    except KeyError as e:
        raise ValueError(f"cannot match requester network IP {ip} to beamline") from e


def get_subnet(ip):
    if not isinstance(ip, str) or len(ip) < 11:
        raise ValueError(f"cannot extract subnet from requester network IP {ip}")
    return ip[:11]



