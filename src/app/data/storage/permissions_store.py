"""
Permissions model database integrations.

:author: Max Milazzo
"""



from . import connection as db
from app.crypto import hash



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

    return bytes(row["owner_public_key_hash"]) if row else None


def load_permissions(event_id: str, public_key: str) -> dict | None:
    """
    Load stored permissions for a given event and public key.

    :param event_id: unique event identifier
    :param public_key: PEM-encoded public key
    :return: dict of permission fields or None if no row exists
    """

    pool = db.get_pool()
    public_key_hash = hash.generate_bytes(public_key)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    cancel_ticket,
                    see_ticket_flag,
                    update_ticket_flag,
                    authorize_registration,
                    see_stamped_ticket,
                    stamp_ticket
                FROM event_permissions
                WHERE event_id = %s
                    AND public_key_hash = %s;
                """,
                (event_id, public_key_hash)
            )
            row = cur.fetchone()

    return dict(row) if row else None


def update_permissions(event_id: str, public_key: str, permissions: dict) -> None:
    """
    Insert or update permissions for a given event and public key.

    :param event_id: unique event identifier
    :param public_key: PEM-encoded public key
    :param permissions: permissions data dictionary
    """

    pool = db.get_pool()
    public_key_hash = hash.generate_bytes(public_key)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO event_permissions (
                    event_id,
                    public_key_hash,
                    cancel_ticket,
                    see_ticket_flag,
                    update_ticket_flag,
                    authorize_registration,
                    see_stamped_ticket,
                    stamp_ticket
                )
                VALUES (
                    %(event_id)s,
                    %(public_key_hash)s,
                    %(cancel_ticket)s,
                    %(see_ticket_flag)s,
                    %(update_ticket_flag)s,
                    %(authorize_registration)s,
                    %(see_stamped_ticket)s,
                    %(stamp_ticket)s
                )
                ON CONFLICT (event_id, public_key_hash) DO UPDATE
                SET
                    cancel_ticket = EXCLUDED.cancel_ticket,
                    see_ticket_flag = EXCLUDED.see_ticket_flag,
                    update_ticket_flag = EXCLUDED.update_ticket_flag,
                    authorize_registration = EXCLUDED.authorize_registration,
                    see_stamped_ticket = EXCLUDED.see_stamped_ticket,
                    stamp_ticket = EXCLUDED.stamp_ticket;
                """,
                {
                    "event_id": event_id,
                    "public_key_hash": public_key_hash,
                    **permissions
                }
            )


def remove_permissions(event_id: str, public_key: str) -> None:
    """
    Remove permissions for a given event and public key.

    :param event_id: unique event identifier
    :param public_key: PEM-encoded public key
    """

    pool = db.get_pool()
    public_key_hash = hash.generate_bytes(public_key)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM event_permissions
                WHERE event_id = %s
                    AND public_key_hash = %s;
                """,
                (event_id, public_key_hash)
            )