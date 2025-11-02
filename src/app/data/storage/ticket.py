import sqlite3
import pickle
from config import DB_FILE

from typing import List

### TODO * transfer table

### TODO - abstract out SQLite specifically


BYTE_SIZE = 8
# assumed byte size (in bits)

## TODO* maybe make byte size global


def register(event_id: str, ticket_number: int) -> None:
    """
    Store ticket issue data.
    """
    ### literally just increment the "issued tickets" data by 1
    #### ALSO if "returned list" in data contains the ticket number, remove it

    ## TODO (*) -- no more "returned list" nc no cancel.  on reissue just mark tick version somehow

    # Connect to the database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    ## TODO* race cond should be fixed by just adding a check here that issued is whats expected (passed ticket num from loaded value non atomically) and making this whole func atomic
    ### error on check failure
    ### ensure reissue atomic too (and add atomic comment)

    # Step 1: Increment the issued count
    cursor.execute("""
        UPDATE events
        SET issued = issued + 1
        WHERE id = ?
    """, (event_id,))
    ### TODO * deal with possible register race condition if scaled
    
    # # Step 2: Fetch the current returned list
    # cursor.execute("""
    #     SELECT returned FROM event_data WHERE event_id = ?
    # """, (event_id,))
    # row = cursor.fetchone()

    # # Step 3: Deserialize the returned list from the database
    # returned_list: List = pickle.loads(row[0])

    # Step 4: Remove the ticket_number from the returned list if it exists
    # if ticket_number in returned_list:
    #     returned_list.remove(ticket_number)

    #     # Step 5: Serialize the updated returned list and update the database
    #     cursor.execute("""
    #         UPDATE event_data
    #         SET returned = ?
    #         WHERE event_id = ?
    #     """, (pickle.dumps(returned_list), event_id))

    # # Commit the changes and close the connection
    conn.commit()
    conn.close()







def reissue(event_id: str, ticket_number: int) -> None:
    """
    """
    ### add this ticket number to the "returned tickets" list for re-registration

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch the current returned list from the database
    cursor.execute("""
        SELECT returned
        FROM event_data
        WHERE event_id = ?
    """, (event_id,))
    row = cursor.fetchone()

    # Unpickle the returned list
    returned_list: List = pickle.loads(row[0])
    returned_list.append(ticket_number)

    # Update the database with the new returned list
    cursor.execute("""
        UPDATE event_data
        SET returned = ?
        WHERE event_id = ?
    """, (pickle.dumps(returned_list), event_id))

    conn.commit()
    conn.close()




def redeem(event_id: str, ticket_number: int) -> bool:
    """
    Alter the redemption bitstring for the associated ticket number bit to reflect a redemption.

    :returns: True if ticket has been redeemed before, false if this is a new redemption
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch the redemption bitstring for the event
    cursor.execute("""
        SELECT redeemed_bitstring FROM event_data
        WHERE event_id = ?
    """, (event_id,))
    row = cursor.fetchone()

    redeemed_bitstring = bytearray(row[0])
    ticket_mask = 1 << (ticket_number % 8)

    if redeemed_bitstring[ticket_number // BYTE_SIZE] & ticket_mask != 0:
        conn.close()
        return True

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
    return False