DEFAULT_BROKER_URL = "127.0.0.1"

# Exchange where the write requests are sent.
REQUEST_EXCHANGE = "request"

# Exchange where the status of the writing is reported.
STATUS_EXCHANGE = "status"

QUEUE_DATA_API          = "write_request"
QUEUE_DETECTOR_CONVERT  = "detector_convert"
QUEUE_DETECTOR_PEDESTAL = "detector_pedestal"
QUEUE_DETECTOR_RETRIEVE = "detector_retrieve"

ROUTE_DATA_API          = "bs.*"
ROUTE_DETECTOR_CONVERT  = "detector.convert"
ROUTE_DETECTOR_PEDESTAL = "detector.pedestal"
ROUTE_DETECTOR_RETRIEVE = "detector.retrieve"

WRITER_DATA_API          = 0
WRITER_DETECTOR_CONVERT  = 2
WRITER_DETECTOR_PEDESTAL = 3
WRITER_DETECTOR_RETRIEVE = 1

# Name of the tags for rabbitmq requests.
TAG_DATA3BUFFER       = "data3buffer"
TAG_IMAGEBUFFER       = "imagebuffer"
TAG_DETECTOR_CONVERT  = "detector_convert"
TAG_DETECTOR_PEDESTAL = "pedestal"
TAG_DETECTOR_POWER_ON = "detector_power_on"
TAG_DETECTOR_RETRIEVE = "detector_buffer"

