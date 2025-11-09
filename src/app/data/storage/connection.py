from psycopg_pool import ConnectionPool
from psycopg import conninfo
from psycopg.rows import dict_row
from config import DATABASE_CREDS  # your existing dict like {"host": ..., "dbname": ...}
from app.util import flags


if flags.demo:
    pool = None

else:
    # Build a DSN from your existing dict so you don't duplicate config
    DSN = conninfo.make_conninfo(**DATABASE_CREDS)

    # Small, simple pool — perfect for your use case
    pool = ConnectionPool(
        conninfo=DSN,
        min_size=1,
        max_size=5,
        timeout=10,
        kwargs={
            "row_factory": dict_row
        }
    )