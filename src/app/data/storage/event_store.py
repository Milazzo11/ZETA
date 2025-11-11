"""
Event model database integrations.

:author: Max Milazzo
"""



from .connection import pool

from typing import Optional



def load_event(event_id: str) -> Optional[dict]:
    """
    Load event data from the database.

    :param event_id: unique event identifier
    :return: event data dictionary or None if not found
    """

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM events WHERE id = %s;", (event_id,))
            row = cur.fetchone()

            return dict(row) if row else None


def load_event_key(event_id: str) -> Optional[bytes]:
    """
    Load event ticket granting key from the database.

    :param event_id: unique event identifier
    :return: event ticket granting key or None if not found
    """

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT event_key FROM event_data WHERE event_id = %s;",
                (event_id,)
            )
            row = cur.fetchone()

            if not row or row["event_key"] is None:
                return None

            return bytes(row["event_key"])


def load_owner_public_key(event_id: str) -> Optional[str]:
    """
    Load the event owner's public key from the database.

    :param event_id: unique event identifier
    :return: the event owner's public key or None if not found
    """

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT owner_public_key FROM event_data WHERE event_id = %s;",
                (event_id,)
            )
            row = cur.fetchone()

            if not row or row["owner_public_key"] is None:
                return None

            return str(row["owner_public_key"])


def search(text: str, limit: int) -> list[dict]:
    """
    Search for an event in the database and load its data

    :param text: text search pattern
    :param limit: query fetch limit
    :return: list of data dictionaries for matching events
    """

    pattern = f"%{text}%"

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM events WHERE name ILIKE %s LIMIT %s;",
                (pattern, limit),
            )
            rows = cur.fetchall()

            return list(rows)


def create(event: dict, event_key: bytes, owner_public_key: str) -> None:
    """
    Create an event.

    :param event: event data dictionary
    :param event_key: event ticket granting key
    :param owner_public_key: the event owner's public key
    """

    state_bytes = b"\x00" * int(event["tickets"])

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO events (
                    id,
                    name,
                    description,
                    tickets,
                    issued,
                    start,
                    finish,
                    restricted
                )
                VALUES (
                    %(id)s,
                    %(name)s,
                    %(description)s,
                    %(tickets)s,
                    %(issued)s,
                    %(start)s,
                    %(finish)s,
                    %(restricted)s
                );
                """,
                event
            )
            # create event row

            cur.execute(
                """
                INSERT INTO event_data (
                    event_id,
                    event_key,
                    owner_public_key,
                    state_bytes
                )
                VALUES (
                    %(event_id)s,
                    %(event_key)s,
                    %(owner_public_key)s,
                    %(state_bytes)s
                );
                """,
                {
                    "event_id": event["id"],
                    "event_key": event_key,
                    "owner_public_key": owner_public_key,
                    "state_bytes": state_bytes
                },
            )
            # create non-public event data row


def delete(event_id: str) -> bool:
    """
    Delete an event.

    :param event_id: unique event identifier
    :return: deletion success status
    """

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM events WHERE id = %s;", (event_id,))
            # delete event row
            # (event data row cascade deletes)

            return cur.rowcount > 0