import sqlite3
import pickle
from config import DB_FILE

from typing import List

### TODO * transfer table

### TODO - abstract out SQLite specifically
### TODO* cursor.execute("BEGIN IMMEDIATE") in front of everything


BYTE_SIZE = 8
# assumed byte size (in bits)


REDEEMED_BYTE = 2 ** (BYTE_SIZE - 1) # high order bit

## TODO* maybe make byte size global







### TODO * gotta add "issued #" to all of these and incorporate in final checks





## TODO - now that text factory bytes is set, this fucking bs isnt needed
def _parse_row_byte(row):
    print("new vers")
    
    cell = row[0]

    if cell is None:
        raise Exception("Data not found")

    # Already a raw int (SQLite optimizes 1-byte blobs sometimes)
    if isinstance(cell, int):
        return cell

    
    # # Text like "☺" -> convert 1:1 to byte → int
    # elif isinstance(cell, str):
    #     if not cell:
    #         raise Exception("Data not found")

    #     return cell.encode("latin1")[0]

    # bytes, bytearray, memoryview
    else:
        b = bytes(cell)
        if not b:
            raise Exception("Data not found")

        return b[0]






def transfer_valid_check(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Validates ticket ownership (to prevent transfer fraud attempts).
    """
    ## called from ./../ticket.load and reissue prob

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    conn.text_factory = bytes

    # Read exactly one byte (SQLite substr is 1-based)
    cur.execute("""
        SELECT substr(data_bytes, ?, 1)
        FROM event_data
        WHERE event_id = ?
    """, (ticket_number + 1, event_id))
    row = cur.fetchone()
    conn.close()

    print("ticketnum+1", ticket_number + 1)

    
    db_version = _parse_row_byte(row)
    print("db version", db_version)
    print("tick version", version)

    return (db_version == version) or ((db_version - REDEEMED_BYTE) == version)



def reissue(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Increment the ticket's version byte only if it currently equals `version`,
    and do not increment past 254. Return True if updated, False otherwise.
    """

    if version >= REDEEMED_BYTE - 1:
        return False  # can't increment past 254

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    conn.text_factory = bytes

    ### NOTE -- in postgres, you can concatenate blobs, so this can be made fully CAS (put this note everywhere)
    cur.execute("SELECT data_bytes FROM event_data WHERE event_id=?", (event_id,))
    data = bytearray(cur.fetchone()[0])

    if data[ticket_number] != version:
        return False

    new_data = bytearray(data)
    new_data[ticket_number] = version + 1

    cur.execute("""
        UPDATE event_data
        SET data_bytes = ?
        WHERE event_id = ?
           AND data_bytes = ?
    """, (
        new_data,
        event_id,
        data
    ))

    changed = (cur.rowcount == 1)

    if changed:
        conn.commit()

    conn.close()
    return changed


## TODO for this and other suctr data_bytes prob just get the thing and select the index manually in python
def verify(event_id: str, ticket_number: int) -> bool:
    """
    Verifies ticket redemption: return True if redeemed, else False.
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    conn.text_factory = bytes

    # Read exactly one byte (SQLite substr is 1-based)
    cur.execute("""
        SELECT substr(data_bytes, ?, 1)
        FROM event_data
        WHERE event_id = ?
    """, (ticket_number + 1, event_id))
    row = cur.fetchone()
    conn.close()

    redemption_code = _parse_row_byte(row)

    # If row exists, row[0] is a bytes object of length 1
    return redemption_code >= REDEEMED_BYTE


## TODO - maybe have some of these return int codes instead of bool for better err msg?
def redeem(event_id: str, ticket_number: int, version: int) -> bool:
    """
    Mark the ticket as redeemed (set its byte to 0xFF) only if not already redeemed.
    
    :returns: True if this is a new redemption, False if it had been redeemed before.
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    conn.text_factory = bytes

    ### NOTE -- in postgres, you can concatenate blobs, so this can be made fully CAS (put this note everywhere)
    
    # TODO also prob put begin immediate on these ones
    
    cur.execute("SELECT data_bytes FROM event_data WHERE event_id=?", (event_id,))
    data = bytearray(cur.fetchone()[0])

    if data[ticket_number] >= REDEEMED_BYTE:
        return False

    new_data = bytearray(data)
    new_data[ticket_number] = version + REDEEMED_BYTE

    cur.execute("""
        UPDATE event_data
        SET data_bytes = ?
        WHERE event_id = ?
           AND data_bytes = ?
    """, (
        new_data,
        event_id,
        data
    ))

    changed = (cur.rowcount == 1)

    if changed:
        conn.commit()

    conn.close()
    return changed

### TODO - blob seems to turn to text somehow before concat for substr stuff