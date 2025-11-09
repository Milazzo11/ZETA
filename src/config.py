"""
"""



DATABASE_CREDS = {
    "dbname": "zeta",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": 5432,
}
# PostgreSQL database connection credentials


REDIS_URL = None #"redis://localhost:6379/0"
# set to None to use local memory replay prevention
# (Redis must be active if using multiple pods/replicas)