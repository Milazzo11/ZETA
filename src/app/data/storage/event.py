"""
"""



from .connection import pool
from app.error.errors import DomainException, ErrorKind

from typing import List, Optional









def load_event(event_id: str) -> Optional[dict]:
    """
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM events WHERE id = %s;", (event_id,))
                row = cur.fetchone()

                return dict(row) if row else None

    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e




def load_event_key(event_id: str) -> Optional[bytes]:
    """
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT event_key FROM event_data WHERE event_id = %s;
                """, (event_id,))
                row = cur.fetchone()

                if not row or row["event_key"] is None:
                    return None

                return bytes(row["event_key"])

    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e



def load_owner_public_key(event_id: str) -> Optional[str]:
    """
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT owner_public_key FROM event_data WHERE event_id = %s;
                """, (event_id,))
                row = cur.fetchone()

                if not row or row["owner_public_key"] is None:
                    return None

                return str(row["owner_public_key"])

    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e




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



def create(event: dict, event_key, owner_public_key: str) -> None:
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
                        "event_key": event_key,            # bytes for BYTEA
                        "owner_public_key": owner_public_key,
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