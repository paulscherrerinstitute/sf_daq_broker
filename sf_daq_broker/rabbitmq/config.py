DEFAULT_BROKER_URL = "127.0.0.1"

# Exchange where the write requests are sent.
REQUEST_EXCHANGE = "request"

# Exchange where the status of the writing is reported.
STATUS_EXCHANGE = "status"

DEFAULT_QUEUE = "write_request"

# Name of the queue for rabbitmq requests.
TAG_DATABUFFER = "databuffer"
TAG_IMAGEBUFFER = "imagebuffer"
TAG_EPICS = "epics"
TAG_DATA3BUFFER = "data3buffer"
TAG_PEDESTAL = "pedestal"
