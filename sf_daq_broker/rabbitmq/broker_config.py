DEFAULT_BROKER_URL = "127.0.0.1"

# Exchange where the write requests are sent.
REQUEST_EXCHANGE = "request"

# Exchange where the status of the writing is reported.
STATUS_EXCHANGE = "status"

# Names of the queues for rabbitmq requests.
QUEUE_DATA_API          = "write_request"
QUEUE_DETECTOR_CONVERT  = "detector_convert"
QUEUE_DETECTOR_PEDESTAL = "detector_pedestal"
QUEUE_DETECTOR_RETRIEVE = "detector_retrieve"

# Names of the routes for rabbitmq requests.
ROUTE_DATA_API          = "bs.*"
ROUTE_DETECTOR_CONVERT  = "detector.convert"
ROUTE_DETECTOR_PEDESTAL = "detector.pedestal"
ROUTE_DETECTOR_RETRIEVE = "detector.retrieve"

# Names of the tags for rabbitmq requests.
TAG_DATA3BUFFER       = "data3buffer"
TAG_IMAGEBUFFER       = "imagebuffer"
TAG_DETECTOR_CONVERT  = "detector_convert"
TAG_DETECTOR_PEDESTAL = "pedestal"
TAG_DETECTOR_POWER_ON = "detector_power_on"
TAG_DETECTOR_RETRIEVE = "detector_buffer"

