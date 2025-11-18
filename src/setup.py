"""
Setup and information module.

:author: Max Milazzo
"""



from app.data.models.event import TRANSFER_LIMIT
from app.util import display, keys
from config import DATABASE_CREDS

import psycopg
import time



def app_credits() -> None:
    """
    Application credits and information display.
    """
    
    print("ZETA")
    print("© Maximus Milazzo\n")
    print("Create and release digital cryptographically secure tickets that users can exchange and redeem.")
    print('See the "README.txt" file for more information and to learn how it works.  Enjoy!')
    
    input()


def key_setup() -> None:
    """
    Application asymmetric cryptosystem initialization.
    """
    
    try:
        keys.setup()

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
        with psycopg.connect(**DATABASE_CREDS) as conn:
            conn.execute("DROP TABLE IF EXISTS event_data;")
            conn.execute("DROP TABLE IF EXISTS events;")

            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    tickets INTEGER NOT NULL CHECK (tickets >= 0),
                    issued INTEGER NOT NULL CHECK (issued >= 0),
                    start DOUBLE PRECISION NOT NULL,
                    finish DOUBLE PRECISION NOT NULL,
                    restricted BOOLEAN NOT NULL,
                    transfer_limit INTEGER NOT NULL CHECK (
                        transfer_limit >= 0
                        AND transfer_limit <= {TRANSFER_LIMIT}
                    ),
                    CHECK (issued <= tickets)
                );
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_data (
                    event_id TEXT PRIMARY KEY,
                    event_key BYTEA NOT NULL,
                    owner_public_key_hash BYTEA NOT NULL,
                    state_bytes BYTEA NOT NULL,
                    flag_bytes BYTEA,
                    FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE
                );
                """
            )

            conn.commit()

        display.clear()
        print("SUCCESS: Database setup completed")

    except Exception as e:
        display.clear()
        print(f"ERROR: Database setup failed --\n{e}")

    input()


def event_cleanup() -> None:
    """
    Delete expired events from the database.
    """

    try:
        with psycopg.connect(**DATABASE_CREDS) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM events WHERE finish < %s;", (time.time(),))

        display.clear()
        print("SUCCESS: Database purge completed")

    except Exception as e:
        display.clear()
        print(f"ERROR: Database purge failed --\n{e}")

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
        print("2 - Database initialization")
        print("3 - Key initialization")
        print("4 - Clear expired events")
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

            case "4":
                event_cleanup()
                # delete expired events

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