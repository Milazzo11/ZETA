"""
Setup and information module.

:author: Max Milazzo
"""



from app.util import display, keys
from config import DATABASE_CREDS

import psycopg



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

        # Connect to Postgres
        with psycopg.connect(**DATABASE_CREDS) as conn:

            # Drop in FK order to mimic a clean slate
            conn.execute("DROP TABLE IF EXISTS event_data;")
            conn.execute("DROP TABLE IF EXISTS events;")

            # Recreate tables using PostgreSQL types
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    tickets INTEGER NOT NULL,
                    issued INTEGER NOT NULL,
                    start DOUBLE PRECISION NOT NULL,
                    finish DOUBLE PRECISION NOT NULL,
                    restricted BOOLEAN NOT NULL
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS event_data (
                    event_id TEXT PRIMARY KEY,
                    event_key BYTEA NOT NULL,
                    owner_public_key TEXT NOT NULL,
                    data_bytes BYTEA NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES events (id)
                );
            """)

            conn.commit()

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