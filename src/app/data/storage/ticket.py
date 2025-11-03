import sqlite3
import pickle
from config import DB_FILE

from typing import List

### TODO * transfer table

### TODO - abstract out SQLite specifically
### TODO* cursor.execute("BEGIN IMMEDIATE") in front of everything


BYTE_SIZE = 8
# assumed byte size (in bits)

## TODO* maybe make byte size global







### TODO * gotta add "issued #" to all of these and incorporate in final checks











def _redeem_check(cursor):
    # Fetch the redemption bitstring for the event
    cursor.execute("""
        SELECT redeemed_bitstring FROM event_data
        WHERE event_id = ?
    """, (event_id,))
    row = cursor.fetchone()

    redeemed_bitstring = bytearray(row[0])
    ticket_mask = 1 << (ticket_number % 8)

    if redeemed_bitstring[ticket_number // BYTE_SIZE] & ticket_mask != 0:
        return True

    return False





def _transfer_valid_checker(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Validates ticket ownership (to prevent transfer fraud attempts).
    """
    ## called from ./../ticket.load and reissue prob



def transfer_valid_check(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Validates ticket ownership (to prevent transfer fraud attempts).
    """
    ## called from ./../ticket.load and reissue prob

    cur.execute("""
        SELECT * FROM transfer_log
        WHERE event_id = ?
            AND ticket_number = ?
            AND version = ?
    """, (event_id, ticket_number, version))

    if cur.rowcount == 1:
        return True

    return False


def reissue(event_id: str, ticket_number: int, version: int) -> None:
    """
    """
    ### TODO*** this should happen here but with sql clause to prevent rare fraud-induced race condition

    ## atomic w/ race cond prevention

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE transfer_log
        SET version = version + 1
        WHERE event_id = ?
            AND ticket_number = ?
            AND version = ?
    """, (event_id, ticket_number, version))

    if cursor.rowcount != 1:
        raise HTTPException(409, "Transfer concurrency race condition detected")

    conn.commit()
    conn.close()





def verify(event_id: str, ticket_number: int) -> bool:
    """
    Verifies ticket redemption
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    res = _redeem_check(cursor)

    conn.close()
    return res


def redeem(event_id: str, ticket_number: int) -> bool:
    """
    Alter the redemption bitstring for the associated ticket number bit to reflect a redemption.

    :returns: True if ticket has been redeemed before, false if this is a new redemption
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()##this will be in basefile

    if _redeem_check(event_id, ticket_number):
        return False

    # Mark the ticket as redeemed (set the bit at the ticket number index to 1)
    redeemed_bitstring[ticket_number // BYTE_SIZE] |= mask

    # Update the database with the new redeemed bitstring
    cursor.execute("""
        UPDATE event_data
        SET redeemed_bitstring = ?
        WHERE event_id = ?
    """, (bytes(redeemed_bitstring), event_id))

    conn.commit()
    conn.close()
    return True