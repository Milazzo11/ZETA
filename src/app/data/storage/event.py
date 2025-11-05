"""
"""


import psycopg
from psycopg.rows import dict_row

import pickle
from typing import List, Optional

from config import DATABASE_CREDS
from fastapi import HTTPException





### all of these should be simple SQL queries (complex logic happens outside this module)


## TODO* look into possibly renaming some of these functions




def load(event_id: str) -> Optional[dict]:###<-this funtionality will probably need to be split up
    """
    Load an event given an event ID.

    :param event_id: event ID
    :return: event dictionary
    """
    ### Event return

    try:
        with psycopg.connect(**DATABASE_CREDS, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # NOTE: psycopg uses %s placeholders (not ? like sqlite)
                cur.execute("SELECT * FROM events WHERE id = %s;", (event_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    except Exception as e:
        # optionally log e
        return None


def load_full(event_id: str, issue: bool) -> Optional[dict]:###<-this funtionality will probably need to be split up
    """
    Load an event and associated data (besides redemption and storage bitstrings).

    :param event_id: event ID
    :return: {
        "event" : event dictionary,
        "data"  : event data dictionary (exclusing bitstrings)
    }
    """

    try:
        with psycopg.connect(**DATABASE_CREDS, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                if issue:
                    cur.execute(
                        """
                        UPDATE events
                           SET issued = issued + 1
                         WHERE id = %s
                           AND issued < tickets
                        RETURNING *;
                        """,
                        (event_id,),
                    )
                else:
                    cur.execute("SELECT * FROM events WHERE id = %s;", (event_id,))

                event_row = cur.fetchone()
                if event_row is None:
                    # covers both "not found" and "sold out" when issue=True
                    return None

                cur.execute(
                    """
                    SELECT event_key, owner_public_key
                      FROM event_data
                     WHERE event_id = %s;
                    """,
                    (event_id,),
                )
                data_row = cur.fetchone()

                # relying on context manager to commit

        return {"event": event_row, "data": data_row}

    except Exception:
        return None



def search(text: str, limit: int) -> List[dict]:##these dicts are ONLY event, no data
    """
    Search for an event.

    :param text: search parameters (if text is in event name)
    :param limit: return limit

    :return: list of event dictionaries (events only, no event-associated data dictionaries)
    """

    pattern = f"%{text}%"

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




def create(event: dict, event_data: dict) -> None:
    """
    Create an event.

    :param event: event dictionary
    :param event_data: event data dictionary (exclusing redemption and storage
        bitstrings, which should contain all 0 bits )
    """

    data_bytes = b"\x00" * int(event["tickets"])

    with psycopg.connect(**DATABASE_CREDS) as conn:
        with conn.cursor() as cur:
            # Insert into events
            cur.execute(
                """
                INSERT INTO events (id, name, description, tickets, issued, start, finish, private)
                VALUES (%(id)s, %(name)s, %(description)s, %(tickets)s, %(issued)s, %(start)s, %(finish)s, %(private)s);
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
                    "event_key": event_data["event_key"],            # bytes for BYTEA
                    "owner_public_key": event_data["owner_public_key"],
                    "data_bytes": data_bytes,                         # bytes for BYTEA
                },
            )
        # context manager commits on successful exit