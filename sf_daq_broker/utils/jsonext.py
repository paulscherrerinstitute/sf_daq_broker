import logging


_logger = logging.getLogger(__name__)


try:
    import ujson as json
except ImportError:
    _logger.warning("ujson package not available -- performance may suffer")
    import json


#TODO:
# make requests use ujson as well?
# `requests.models.complexjson = ujson`
# or
# `requests.compat.json = ujson`
# or even
# `sys.modules["json"] = ujson`


def json_save(what, filename, *args, mode="w", indent=4, sort_keys=True, **kwargs):
    with open(filename, mode=mode) as f:
        json.dump(what, f, *args, indent=indent, sort_keys=sort_keys, **kwargs)

def json_load(filename, *args, **kwargs):
    with open(filename, "r") as f:
        return json.load(f, *args, **kwargs)


json_obj_to_str = json.dumps
json_str_to_obj = json.loads



