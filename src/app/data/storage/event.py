"""
"""


import psycopg
from psycopg.rows import dict_row

import pickle
from typing import List, Optional

from config import DATABASE_CREDS






### all of these should be simple SQL queries (complex logic happens outside this module)


## TODO* look into possibly renaming some of these functions
## idea - load_event, load_data, issue?





def _load(query: str, event_id: str) -> dict:
    """
    """

    try:
        with psycopg.connect(**DATABASE_CREDS, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (event_id,))
                row = cur.fetchone()

                if not row:
                    raise DomainError(ErrorKind.NOT_FOUND, "event not found")

                return dict(row)
            
    except DomainError:
        raise

    except Exception:
        raise DomainError(ErrorKind.INTERNAL, "database error")



def issue(event_id: str) -> dict:
    """
    """
    
    return _load(
        """
        UPDATE events
            SET issued = issued + 1
                WHERE id = %s
                AND issued < tickets
        RETURNING *;
        """,
        event_id
    )


def load_event(event_id: str) -> dict:
    """
    Load an event given an event ID.

    :param event_id: event ID
    :return: event dictionary
    """

    return _load("SELECT * FROM events WHERE id = %s;", event_id)
    

def load_secrets(event_id: str) -> dict:
    """
    Load an event and associated data (besides redemption and storage bitstrings).
    """

    return _load(
        """
        SELECT event_key, owner_public_key
            FROM event_data
        WHERE event_id = %s;
        """,
        event_id
    )

### TODO * exchange implementation to use these






def search(text: str, limit: int) -> List[dict]:##these dicts are ONLY event, no data
    """
    Search for an event.

    :param text: search parameters (if text is in event name)
    :param limit: return limit

    :return: list of event dictionaries (events only, no event-associated data dictionaries)
    """

    pattern = f"%{text}%"

    try:
        with psycopg.connect(**DATABASE_CREDS, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM events
                    WHERE name ILIKE %s
                    LIMIT %s;
                    """,
                    (pattern, limit),
                )
                rows = cur.fetchall()
                return list(rows)  # rows are already dicts
            
    except Exception:
        raise DomainError(ErrorKind.INTERNAL, "database error")



def create(event: dict, event_secrets: dict) -> None:
    """
    Create an event.

    :param event: event dictionary
    :param event_data: event data dictionary (exclusing redemption and storage
        bitstrings, which should contain all 0 bits )
    """

    data_bytes = b"\x00" * int(event["tickets"])

    try:
        with psycopg.connect(**DATABASE_CREDS) as conn:
            with conn.cursor() as cur:
                # Insert into events
                cur.execute(
                    """
                    INSERT INTO events (id, name, description, tickets, issued, start, finish, restricted)
                    VALUES (%(id)s, %(name)s, %(description)s, %(tickets)s, %(issued)s, %(start)s, %(finish)s, %(restricted)s);
                    """,
                    event,
                )

                # Insert into event_data
                cur.execute(
                    """
                    INSERT INTO event_data (event_id, event_key, owner_public_key, data_bytes)
                    VALUES (%(event_id)s, %(event_key)s, %(owner_public_key)s, %(data_bytes)s);
                    """,
                    {
                        "event_id": event["id"],
                        "event_key": event_secrets["event_key"],            # bytes for BYTEA
                        "owner_public_key": event_secrets["owner_public_key"],
                        "data_bytes": data_bytes,                         # bytes for BYTEA
                    },
                )
            # context manager commits on successful exit

    except Exception:
        raise DomainError(ErrorKind.INTERNAL, "database error")



def delete(event_id: str) -> bool:
    """
    """

    try:
        with psycopg.connect(**DATABASE_CREDS) as conn:
            with conn.cursor() as cur:
                
                # Delete from event_data first (if no FK cascade)
                cur.execute(
                    """
                    DELETE FROM event_data
                    WHERE event_id = %s;
                    """,
                    (event_id,)
                )

                # Delete from events table
                cur.execute(
                    """
                    DELETE FROM events
                    WHERE id = %s;
                    """,
                    (event_id,)
                )

                # rowcount from event delete check
                return cur.rowcount > 0
            
    except Exception:
        raise DomainError(ErrorKind.INTERNAL, "database error")