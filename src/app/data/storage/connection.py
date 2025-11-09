"""
Database connection.

:author: Max Milazzo
"""



from app.util import flags
from config import DATABASE_CREDS

from psycopg import conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool



if flags.demo:
    pool = None

else:
    DSN = conninfo.make_conninfo(**DATABASE_CREDS)

    pool = ConnectionPool(
        conninfo=DSN,
        min_size=1,
        max_size=5,
        timeout=10,
        kwargs={
            "row_factory": dict_row
        }
    )
    # initialize a database connection pool