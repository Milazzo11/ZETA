import sqlite3
import pickle
from config import DB_FILE

from typing import List

### TODO * transfer table

### TODO - abstract out SQLite specifically
### TODO* cursor.execute("BEGIN IMMEDIATE") in front of everything


BYTE_SIZE = 8
# assumed byte size (in bits)


REDEEMED_BYTE = 255

## TODO* maybe make byte size global







### TODO * gotta add "issued #" to all of these and incorporate in final checks














def transfer_valid_check(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Validates ticket ownership (to prevent transfer fraud attempts).
    """
    ## called from ./../ticket.load and reissue prob

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Read exactly one byte (SQLite substr is 1-based)
    cur.execute("""
        SELECT substr(data_bytes, ?, 1)
        FROM event_data
        WHERE event_id = ?
    """, (ticket_number + 1, event_id))
    row = cur.fetchone()
    conn.close()

    # If row exists, row[0] is a bytes object of length 1
    return row[0][0] == version



def reissue(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Increment the ticket's version byte only if it currently equals `version`,
    and do not increment past 254. Return True if updated, False otherwise.
    """

    if version >= REDEEMED_BYTE - 1:
        return False  # can't increment past 254

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        UPDATE event_data
           SET data_bytes =
                substr(data_bytes, 1, ?) || ? || substr(data_bytes, ? + 2)
         WHERE event_id = ?
           AND substr(data_bytes, ?, 1) = ?
    """, (
        ticket_number,                 # start of prefix
        bytes([version + 1]),          # replacement byte
        ticket_number,                 # start of suffix
        event_id,                      # match row
        ticket_number + 1,             # 1-based index for SQLite
        bytes([version])               # must match current version
    ))

    changed = (cur.rowcount == 1)

    if changed:
        conn.commit()

    conn.close()
    return changed



def verify(event_id: str, ticket_number: int) -> bool:
    """
    Verifies ticket redemption: return True if redeemed, else False.
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Read exactly one byte (SQLite substr is 1-based)
    cur.execute("""
        SELECT substr(data_bytes, ?, 1)
        FROM event_data
        WHERE event_id = ?
    """, (ticket_number + 1, event_id))
    row = cur.fetchone()
    conn.close()

    # If row exists, row[0] is a bytes object of length 1
    return row[0][0] == REDEEMED_BYTE



def redeem(event_id: str, ticket_number: int) -> bool:
    """
    Mark the ticket as redeemed (set its byte to 0xFF) only if not already redeemed.

    :returns: True if this is a new redemption, False if it had been redeemed before.
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Splice in a single byte (0xFF) only if the current byte is not already 0xFF.
    # If another writer redeems concurrently, this UPDATE affects 0 rows and we return False.
    cur.execute("""
        UPDATE event_data
           SET data_bytes =
                substr(data_bytes, 1, ?) || x'FF' || substr(data_bytes, ? + 2)
         WHERE event_id = ?
           AND substr(data_bytes, ?, 1) <> x'FF'
    """, (ticket_number, ticket_number, event_id, ticket_number + 1))

    changed = (cur.rowcount == 1)

    if changed:
        conn.commit()

    conn.close()
    return changed