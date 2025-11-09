import psycopg
from config import DATABASE_CREDS


### TODO * transfer table

### TODO - abstract out SQLite specifically
### TODO* cursor.execute("BEGIN IMMEDIATE") in front of everything


BYTE_SIZE = 8
# assumed byte size (in bits)


 # high order bit

## TODO* maybe make byte size global

from app.error.errors import DomainException, ErrorKind

from .connection import pool

from typing import Optional


### TODO * gotta add "issued #" to all of these and incorporate in final checks







def issue(event_id: str) -> Optional[int]:
    """
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE events
                        SET issued = issued + 1
                            WHERE id = %s
                            AND issued < tickets
                    RETURNING issued;
                """, (event_id,))
                row = cur.fetchone()

                if not row or row["issued"] is None:
                    return None

                return int(row["issued"]) - 1
            
    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e













def reissue(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Increment the ticket's version byte only if it currently equals `version`,
    and do not increment past 254. Return True if updated, False otherwise.
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE event_data
                    SET data_bytes = set_byte(data_bytes, %s, %s)
                    WHERE event_id = %s
                    AND get_byte(data_bytes, %s) = %s
                    """,
                    (ticket_number, version + 1, event_id, ticket_number, version),
                )

                return cur.rowcount == 1

    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e











## TODO - maybe have some of these return int codes instead of bool for better err msg?
def redeem(event_id: str, ticket_number: int, new_byte: int, threshold: int) -> bool:
    """
    Mark the ticket as redeemed (set its byte to 0xFF) only if not already redeemed.
    
    :returns: True if this is a new redemption, False if it had been redeemed before.
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE event_data
                    SET data_bytes = set_byte(data_bytes, %s, %s)
                    WHERE event_id = %s
                    AND get_byte(data_bytes, %s) < %s
                    """,
                    (ticket_number, new_byte, event_id, ticket_number, threshold),
                )

                return cur.rowcount == 1
        
    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e
    



def get_data_byte(event_id: str, ticket_number: int) -> Optional[int]:
    """
    Verifies ticket redemption: return True if redeemed, else False.
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT get_byte(data_bytes, %s) AS data_byte
                    FROM event_data
                    WHERE event_id = %s;
                    """,
                    (ticket_number, event_id),
                )
                row = cur.fetchone()

        # If no event_data row exists → not redeemed (your SQLite logic implied same)
        if not row or row["data_byte"] is None:
            return None

        return int(row["data_byte"])

    except Exception as e:
        raise DomainException(ErrorKind.INTERNAL, "database error") from e