"""
"""


import psycopg
from psycopg.rows import dict_row

from typing import List, Optional

from config import DATABASE_CREDS



from app.error.errors import DomainException, ErrorKind

from .connection import pool


### all of these should be simple SQL queries (complex logic happens outside this module)


## TODO* look into possibly renaming some of these functions
## idea - load_event, load_data, issue?





def _load(query: str, event_id: str) -> Optional[dict]:
    """
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (event_id,))
                row = cur.fetchone()

                if not row:
                    return None

                return dict(row)

    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e



def issue(event_id: str) -> dict:
    """
    """
    
    event = _load(
        """
        UPDATE events
            SET issued = issued + 1
                WHERE id = %s
                AND issued < tickets
        RETURNING *;
        """,
        event_id
    )

    if event is None:
        raise DomainException(ErrorKind.CONFLICT, "unable to issue ticket")
    
    return event


def load_event(event_id: str) -> dict:
    """
    Load an event given an event ID.

    :param event_id: event ID
    :return: event dictionary
    """

    event = _load("SELECT * FROM events WHERE id = %s;", event_id)

    if event is None:
        raise DomainException(ErrorKind.NOT_FOUND, "event not found")
    
    return event
    

def load_secrets(event_id: str) -> dict:
    """
    Load an event and associated data (besides redemption and storage bitstrings).
    """

    event = _load(
        """
        SELECT event_key, owner_public_key
            FROM event_data
        WHERE event_id = %s;
        """,
        event_id
    )

    if event is None:
        raise DomainException(ErrorKind.NOT_FOUND, "event not found")
    
    return event






def search(text: str, limit: int) -> List[dict]:##these dicts are ONLY event, no data
    """
    Search for an event.

    :param text: search parameters (if text is in event name)
    :param limit: return limit

    :return: list of event dictionaries (events only, no event-associated data dictionaries)
    """

    pattern = f"%{text}%"

    try:
        with pool.connection() as conn:
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
            
    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e



def create(event: dict, event_secrets: dict) -> None:
    """
    Create an event.

    :param event: event dictionary
    :param event_data: event data dictionary (exclusing redemption and storage
        bitstrings, which should contain all 0 bits )
    """

    data_bytes = b"\x00" * int(event["tickets"])

    try:
        with pool.connection() as conn:
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

    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e



def delete(event_id: str) -> bool:
    """
    """

    try:
        with pool.connection() as conn:
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
            
    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e