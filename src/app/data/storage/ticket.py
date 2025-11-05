import psycopg
import pickle
from config import DATABASE_CREDS

from typing import List, Optional

### TODO * transfer table

### TODO - abstract out SQLite specifically
### TODO* cursor.execute("BEGIN IMMEDIATE") in front of everything


BYTE_SIZE = 8
# assumed byte size (in bits)


REDEEMED_BYTE = 2 ** (BYTE_SIZE - 1) # high order bit

## TODO* maybe make byte size global







### TODO * gotta add "issued #" to all of these and incorporate in final checks





## TODO - now that text factory bytes is set, this fucking bs isnt needed
def _get_data_byte(event_id: str, ticket_number: int) -> Optional[int]:
    """
    Verifies ticket redemption: return True if redeemed, else False.
    """

    with psycopg.connect(**DATABASE_CREDS) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT get_byte(data_bytes, %s)
                  FROM event_data
                 WHERE event_id = %s;
                """,
                (ticket_number, event_id),
            )
            row = cur.fetchone()

    # If no event_data row exists → not redeemed (your SQLite logic implied same)
    if row is None or row[0] is None:
        return None

    return int(row[0])





## TODO* prob change to like "version_check"
def transfer_valid_check(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Validates ticket ownership (to prevent transfer fraud attempts).
    """
    ## called from ./../ticket.load and reissue prob

    state_version = _get_data_byte(event_id, ticket_number)

    if state_version is None:
        return False

    # Either exact match, or matches when masked by REDEEMED_BYTE
    return (state_version == version) or ((state_version - REDEEMED_BYTE) == version)






def reissue(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Increment the ticket's version byte only if it currently equals `version`,
    and do not increment past 254. Return True if updated, False otherwise.
    """

    if version >= REDEEMED_BYTE - 1:
        return False

    with psycopg.connect(**DATABASE_CREDS) as conn:
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







## TODO for this and other suctr data_bytes prob just get the thing and select the index manually in python
def verify(event_id: str, ticket_number: int) -> bool:
    """
    Verifies ticket redemption: return True if redeemed, else False.
    """

    state_version = _get_data_byte(event_id, ticket_number)

    if state_version is None:
        return False

    return state_version >= REDEEMED_BYTE





## TODO - maybe have some of these return int codes instead of bool for better err msg?
def redeem(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Mark the ticket as redeemed (set its byte to 0xFF) only if not already redeemed.
    
    :returns: True if this is a new redemption, False if it had been redeemed before.
    """


    if version >= REDEEMED_BYTE:
        return False

    new_byte = version + REDEEMED_BYTE  # 128..255

    with psycopg.connect(**DATABASE_CREDS) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE event_data
                   SET data_bytes = set_byte(data_bytes, %s, %s)
                 WHERE event_id = %s
                   AND get_byte(data_bytes, %s) < %s
                """,
                (ticket_number, new_byte, event_id, ticket_number, REDEEMED_BYTE),
            )
            return cur.rowcount == 1