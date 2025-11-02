"""
"""


import os


###################################
## Server Configuration Variables:
###################################


PRIV_KEY_FILE = os.path.join("data", "priv.key")
# private key file


PUB_KEY_FILE = os.path.join("data", "pub.key")


DB_FILE = os.path.join("data", "events.db")
### TODO - rename var prob

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


TIMESTAMP_ERROR = 10
# timestamp error allowance (in seconds) for requests


STATE_CLEANUP_INTERVAL = 10



# DEFAULT_EVENT_TICKETS = 1_000


# MAX_EVENT_TICKETS = 1_000_000


# DEFAULT_EXCHANGES = 2 ** 4


# MAX_EXCHANGES = 2 ** 8


# DEFAULT_EVENT_TTL = 2_628_00


# MAX_EVENT_TTL = 31_536_000


###################################
###################################