"""
Database connection.

:author: Max Milazzo
"""



from config import DATABASE_CREDS

from psycopg import conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool



pool = None
# database connection pool



def start_pool() -> None:
    """
    Initialize a database connection pool
    """

    global pool

    pool = ConnectionPool(
        conninfo=conninfo.make_conninfo(**DATABASE_CREDS),
        min_size=1,
        max_size=5,
        timeout=10,
        kwargs={
            "row_factory": dict_row
        }
    )


def stop_pool() -> None:
    """
    Close a database connection pool.
    """

    global pool

    if pool is None:
        raise Exception("Database connection pool not started")

    pool.close()


def get_pool() -> ConnectionPool:
    """
    Get the initialized database connection pool.

    :return: database connection pool
    """

    if pool is None:
        raise Exception("Database connection pool not started")

    return pool