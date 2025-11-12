"""
Ticket model database integrations.

:author: Max Milazzo
"""



from . import connection as db

from typing import Optional



def issue(event_id: str) -> Optional[int]:
    """
    Update the database to issue a new event ticket with a unique ticket number.

    :param event_id: unique event identifier
    :return: the issued ticket number or None if a ticket cannot be issued
    """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE events
                SET issued = issued + 1
                WHERE id = %s
                    AND issued < tickets
                RETURNING issued;
                """,
                (event_id,)
            )
            row = cur.fetchone()

            if not row or row["issued"] is None:
                return None

            return int(row["issued"]) - 1


def reissue(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Update the database to reflect a ticket reissue (version number increase).

    :param event_id: unique event identifier
    :param ticket_number: ticket issue number
    :param version: current version (before update)
    :return: reissue success status
    """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE event_data
                SET state_bytes = set_byte(state_bytes, %s, %s)
                WHERE event_id = %s
                    AND get_byte(state_bytes, %s) = %s
                """,
                (ticket_number, version + 1, event_id, ticket_number, version),
            )

            return cur.rowcount == 1


def advance_state(event_id: str, ticket_number: int, data: int, threshold: int) -> bool:
    """
    Set an integer state (representing redeemed, stamped, or canceled) on ticket data.
    
    :param event_id: unique event identifier
    :param ticket_number: ticket issue number
    :param data: new data byte with state update applied
    :param threshold: threshold value (current byte must be less than this to update)
    :return: state update success status
    """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE event_data
                SET state_bytes = set_byte(state_bytes, %s, %s)
                WHERE event_id = %s
                    AND get_byte(state_bytes, %s) < %s
                """,
                (ticket_number, data, event_id, ticket_number, threshold),
            )

            return cur.rowcount == 1


def load_state_byte(event_id: str, ticket_number: int) -> Optional[int]:
    """
    Load a ticket's state data byte from the database.

    :param event_id: unique event identifier
    :param ticket_number: ticket issue number
    :return: ticket state data byte or None if not found
    """

    with db.pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT get_byte(state_bytes, %s) AS state_byte
                FROM event_data
                WHERE event_id = %s;
                """,
                (ticket_number, event_id),
            )
            row = cur.fetchone()

    if not row or row["state_byte"] is None:
        return None

    return int(row["state_byte"])