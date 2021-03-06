DEFAULT_STREAM_OUTPUT_PORT = 12500
DEFAULT_QUEUE_LENGTH = 100
DEFAULT_BROKER_REST_PORT = 10002
DEFAULT_EPICS_WRITER_URL = "http://localhost:10200/notify"
DEFAULT_LOG_LEVEL = "INFO"

DATA_RETRIEVAL_DELAY = 60

AUDIT_FILE_TIME_FORMAT = "%Y%m%d-%H%M%S"

DEFAULT_AUDIT_FILENAME = "/var/log/sf_databuffer_audit.log"

# data_api and /matching query request. If sf-data-api-02 doesn't work (broke several times), switch to official one data-api.psi.ch
DATA_API_QUERY_ADDRESS = "http://sf-data-api-02.psi.ch/query"
#DATA_API_QUERY_ADDRESS = "https://data-api.psi.ch/sf/query"
IMAGE_API_QUERY_ADDRESS = ["http://172.27.0.14:8371/api/1/query", "http://172.27.0.15:8371/api/1/query"]
DATA_API3_QUERY_ADDRESS = "http://sf-daqbuf-33:8371/api/1"
EPICS_QUERY_ADDRESS = "https://data-api.psi.ch/sf"

DATA_BACKEND = "sf-databuffer"
IMAGE_BACKEND = "sf-imagebuffer"

ERROR_IF_NO_DATA = False
TRANSFORM_PULSE_ID_TO_TIMESTAMP_QUERY = False 
SEPARATE_CAMERA_CHANNELS = True

OUTPUT_FILE_SUFFIX_DATA_BUFFER = "BSREAD"
OUTPUT_FILE_SUFFIX_DATA3_BUFFER = "BSDATA"
OUTPUT_FILE_SUFFIX_IMAGE_BUFFER = "CAMERAS"
OUTPUT_FILE_SUFFIX_EPICS = "PVCHANNELS"
