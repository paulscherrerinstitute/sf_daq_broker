
subnet_to_beamline = {
    "129.129.242": "alvra",
    "129.129.243": "bernina",
    "129.129.244": "cristallina",
    "129.129.246": "maloja",
    "129.129.247": "furka"
}


def ip_to_console(remote_ip):
    beamline = None
    if len(remote_ip) > 11:
        beamline = subnet_to_beamline.get(remote_ip[:11], None)
    return beamline



