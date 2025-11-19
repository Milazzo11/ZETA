"""
Ticket model database integrations.

:author: Max Milazzo
"""



from . import connection as db



def issue(event_id: str) -> int | None:
    """
    Update the database to issue a new event ticket with a unique ticket number.

    :param event_id: unique event identifier
    :return: the issued ticket number or None if a ticket cannot be issued
    """

    pool = db.get_pool()

    with pool.connection() as conn:
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
    
    return int(row["issued"]) - 1 if row else None


def reissue(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Update the database to reflect a ticket reissue (version number increase).

    :param event_id: unique event identifier
    :param ticket_number: ticket issue number
    :param version: current version (before update)
    :return: reissue success status
    """

    pool = db.get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE event_data
                SET state_bytes = set_byte(state_bytes, %s, %s)
                WHERE event_id = %s
                    AND get_byte(state_bytes, %s) = %s
                """,
                (ticket_number, version + 1, event_id, ticket_number, version)
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

    pool = db.get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE event_data
                SET state_bytes = set_byte(state_bytes, %s, %s)
                WHERE event_id = %s
                    AND get_byte(state_bytes, %s) < %s
                    AND %s < (
                        SELECT issued
                        FROM events
                        WHERE id = %s
                    );
                """,
                (
                    ticket_number,
                    data, event_id,
                    ticket_number,
                    threshold,
                    ticket_number,
                    event_id
                )
            )

            return cur.rowcount == 1


def load_state_byte(event_id: str, ticket_number: int) -> int | None:
    """
    Load a ticket's state data byte from the database.

    :param event_id: unique event identifier
    :param ticket_number: ticket issue number
    :return: ticket state data byte or None if not found
    """

    pool = db.get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT get_byte(state_bytes, %s) AS state_byte
                FROM event_data
                WHERE event_id = %s;
                """,
                (ticket_number, event_id)
            )
            row = cur.fetchone()

    return int(row["state_byte"]) if row else None


def set_flag(event_id: str, ticket_number: int, value: int) -> bool:
    """
    Set the flag byte at the given ticket index and return its new value.

    :param event_id: ID of the event
    :param ticket_number: 0-indexed ticket number
    :param value: new byte value (already validated 0–255)
    :return: set success status
    """

    pool = db.get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE event_data
                SET flag_bytes = set_byte(flag_bytes, %s, %s)
                WHERE event_id = %s
                    AND flag_bytes IS NOT NULL;
                """,
                (ticket_number, value, event_id)
            )

            return cur.rowcount == 1


def get_flag(event_id: str, ticket_number: int) -> int | None:
    """
    Get a ticket's flag value.

    :param event_id: unique event identifier
    :param ticket_number: ticket issue number
    :return: ticket flag value.
    """

    pool = db.get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT get_byte(flag_bytes, %s) AS flag_byte
                FROM event_data
                WHERE event_id = %s
                    AND flag_bytes IS NOT NULL;
                """,
                (ticket_number, event_id)
            )
            row = cur.fetchone()

    return int(row["flag_byte"]) if row else None