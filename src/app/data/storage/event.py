"""
"""


import sqlite3
import pickle
from typing import List

from config import DB_FILE



BYTE_SIZE = 8
# assumed byte size (in bits)



### all of these should be simple SQL queries (complex logic happens outside this module)


#### TODO - I don't think using "event" and data objects here makes sense -- that logic can be dealt with at the obj level


def load(event_id: str) -> dict:###<-this funtionality will probably need to be split up
    """
    Load an event given an event ID.

    :param event_id: event ID
    :return: event dictionary
    """
    ### Event return


    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch event by ID
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event_row = cursor.fetchone()

    print(event_row)

    columns = [desc[0] for desc in cursor.description]

    conn.close()

    
    return dict(zip(columns, event_row))


def load_full(event_id: str, issue: bool) -> dict:###<-this funtionality will probably need to be split up
    """
    Load an event and associated data (besides redemption and storage bitstrings).

    :param event_id: event ID
    :return: {
        "event" : event dictionary,
        "data"  : event data dictionary (exclusing bitstrings)
    }
    """
    
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if issue:
        cursor.execute("""
            UPDATE events
                SET issued = CASE
                    WHEN issued + 1 > tickets THEN tickets
                    ELSE issued + 1
                END
            WHERE id = ?
                AND issued < tickets
            RETURNING *
        """, (event_id,))
        # issue a new ticket before loading data for new registrations     

    else:
        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    
    event_row = cursor.fetchone()
    event_columns = [desc[0] for desc in cursor.description]

    # Fetch event data
    cursor.execute("""
        SELECT event_key, owner_public_key 
        FROM event_data 
        WHERE event_id = ?
    """, (event_id,))
    data_row = cursor.fetchone()

    


    conn.commit()
    conn.close()

    
    data_columns = ["event_key", "owner_public_key"]

    data = {
        "event": dict(zip(event_columns, event_row)),
        "data": dict(zip(data_columns, data_row))
    }

    return data


def search(text: str, limit: int) -> List[dict]:##these dicts are ONLY event, no data
    """
    Search for an event.

    :param text: search parameters (if text is in event name)
    :param limit: return limit

    :return: list of event dictionaries (events only, no event-associated data dictionaries)
    """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Search events by partial name match
    cursor.execute("""
        SELECT * 
        FROM events 
        WHERE name LIKE ? 
        LIMIT ?
    """, (f"%{text}%", limit))

    rows = cursor.fetchall()
    conn.close()

    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]





def create(event: dict, event_data: dict) -> None:
    """
    Create an event.

    :param event: event dictionary
    :param event_data: event data dictionary (exclusing redemption and storage
        bitstrings, which should contain all 0 bits )
    """

    # Create redeemed bitstring (all tickets start unredeemed)
    redeemed_bitstring = b'\x00' * (event["tickets"] // BYTE_SIZE + 1)  # Create a bytes object of size `tickets`

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Insert into events table
    cursor.execute("""
        INSERT INTO events (id, name, description, tickets, issued, start, end, exchanges, private)
        VALUES (:id, :name, :description, :tickets, :issued, :start, :end, :exchanges, :private)
    """, event)

    # Insert into event_data table
    cursor.execute("""
        INSERT INTO event_data (event_id, event_key, owner_public_key, returned, redeemed_bitstring)
        VALUES (:event_id, :event_key, :owner_public_key, :returned, :redeemed_bitstring)
        """, {
            "event_id": event["id"],
            "event_key": event_data["event_key"],
            "owner_public_key": event_data["owner_public_key"],
            "returned": pickle.dumps(event_data["returned"]),
            "redeemed_bitstring": redeemed_bitstring,
        }
    )

    conn.commit()
    conn.close()