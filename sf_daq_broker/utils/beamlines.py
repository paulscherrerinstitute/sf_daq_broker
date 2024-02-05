
SUBNET_TO_BEAMLINE = {
    "129.129.242": "alvra",
    "129.129.243": "bernina",
    "129.129.244": "cristallina",
    "129.129.245": "diavolezza",
    "129.129.246": "maloja",
    "129.129.247": "furka"
}


def ip_to_console(ip):
    if len(ip) < 11:
        return None
    subnet = ip[:11]
    return SUBNET_TO_BEAMLINE.get(subnet, None)



