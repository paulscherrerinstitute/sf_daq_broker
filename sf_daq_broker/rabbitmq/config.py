DEFAULT_BROKER_URL = "127.0.0.1"

# Exchange where the write requests are sent.
REQUEST_EXCHANGE = "request"

# Exchange where the status of the writing is reported.
STATUS_EXCHANGE = "status"

DEFAULT_QUEUE = "write_request"
DEFAULT_ROUTE = "bs.*"

DETECTOR_RETRIEVE_QUEUE = "detector_retrieve"
DETECTOR_RETRIEVE_ROUTE = "detector.retrieve"

DETECTOR_CONVERSION_QUEUE = "detector_convert"
DETECTOR_CONVERSION_ROUTE = "detector.convert"

# Name of the tags for rabbitmq requests.
TAG_DATABUFFER = "databuffer"
TAG_IMAGEBUFFER = "imagebuffer"
TAG_EPICS = "epics"
TAG_DATA3BUFFER = "data3buffer"
TAG_PEDESTAL = "pedestal"
TAG_EPICS = "epics"
TAG_DETECTOR_RETRIEVE = "detector_buffer"
TAG_DETECTOR_CONVERT  = "detector_convert"
TAG_POWER_ON = "detector_power_on"

