"""
"""



from . import connection as db



def load_owner_public_key_hash(event_id: str) -> bytes | None:
    """
    Load the event owner's public key hash from the database.

    :param event_id: unique event identifier
    :return: the event owner's public key hash or None if not found
    """

    pool = db.get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT owner_public_key_hash FROM event_data WHERE event_id = %s;",
                (event_id,)
            )
            row = cur.fetchone()

    return None if row is None else bytes(row["owner_public_key_hash"])