"""
"""




###################################
## Server Configuration Variables:
###################################












DEFAULT_EVENT_TICKETS = 256


# MAX_EVENT_TICKETS = 1_000_000


# DEFAULT_EXCHANGES = 2 ** 4


# MAX_EXCHANGES = 2 ** 8


DEFAULT_EVENT_TTL = 2_628_00


# MAX_EVENT_TTL = 31_536_000

#### keep these vvvv

DATABASE_CREDS = {
    "dbname": "zeta",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": 5432,
}


REDIS_URL = "redis://localhost:6379/0"
# set to None to use local memory replay prevention
# (Redis must be active if using multiple pods/replicas)



###################################
###################################