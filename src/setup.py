"""
"""


import os
import pickle
import json
import base64

import sqlite3

from app.crypto.asymmetric import AKE
from app.crypto.symmetric import SKE
from app.util import display
from dateutil import parser

from config import (
    PRIV_KEY_FILE, PUB_KEY_FILE, DB_FILE
)



def app_credits() -> None:
    """
    Application credits and information display.
    """
    
    print("Yellowtail")
    print("© Maximus Milazzo\n")
    print("Create and release digital cryptographically secure tickets that users can exchange and redeem.")
    print('See the "README.txt" file for more information and to learn how it works.  Enjoy!')
    
    input()
    
    

def key_setup() -> None:
    """
    Application asymmetric cryptosystem initialization.
    """
    
    try:
        cipher = AKE()

        with open(PRIV_KEY_FILE, "wb") as f:
            f.write(cipher.private_key)
            
        with open(PUB_KEY_FILE, "wb") as f:
            f.write(cipher.public_key)
            
        display.clear()
        print("SUCCESS: System keys generated")
        
    except Exception as e:
        display.clear()
        print(f"ERROR: Key setup failed --\n{e}")
        
    input()
    
    

def db_setup() -> None:
    """
    Set up the database schema for storing events and their data.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Create events table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            tickets INTEGER NOT NULL,
            issued INTEGER NOT NULL,
            start REAL NOT NULL,
            end REAL NOT NULL,
            exchanges INTEGER NOT NULL,
            private INTEGER NOT NULL
        )
        """)
        
        # Create event_data table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_data (
            event_id TEXT PRIMARY KEY,
            event_key BLOB NOT NULL,
            owner_public_key TEXT NOT NULL,
            redeemed_bitstring BLOB NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events (id)
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transfer_log (
            event_id TEXT NOT NULL,
            ticket_num INTEGER NOT NULL,
            reissued INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (event_id, ticket_num),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
        """)

        
        conn.commit()
        conn.close()

        display.clear()
        print("SUCCESS: Database setup completed")

    except Exception as e:
        display.clear()
        print(f"ERROR: Database setup failed --\n{e}")

    input()


def main() -> None:
    """
    Program entry point.
    """
    
    display.clear()
    # clear initial display
    
    while True:
        print("Ticket Configration Menu\n")
        print("1 - Credits and information")
        print("2 - Database setup")
        print("3 - Key setup")
        print("x - Exit\n")
        # program options
        
        option = input("> ")
        display.clear()
        
        match option.lower():
            case "1":
                app_credits()
                # show credits and infromation

            case "2":
                db_setup()
                # set up server database
            
            case "3":
                key_setup()
                # setup global keys

            case "x":
                return
                # exit application
            
            case _:
                print("ERROR: Invalid input")
                input()
                # bad input

        display.clear()



if __name__ == "__main__":
    main()