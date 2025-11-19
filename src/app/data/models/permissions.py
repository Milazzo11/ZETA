"""
Permissions data model.

:author: Max Milazzo
"""



from app.crypto import hash
from app.data.storage import permissions_store
from app.error.errors import DomainException, ErrorKind

from pydantic import BaseModel, Field
from typing import Self



class Permissions(BaseModel):
    """
    Endpoint event permission options.
    """

    cancel_ticket: bool = Field(
        False,
        description="Allow the user to cancel tickets for event"
    )
    see_ticket_flag: bool = Field(
        False,
        description="Allow a user to see private ticket flags"
    )
    update_ticket_flag: bool = Field(
        False,
        description="Allow the user to set a ticket's flag value"
    )
    authorize_registration: bool = Field(
        False,
        description="Allow the user to authorize restricted registrations for event"
    )
    see_stamped_ticket: bool = Field(
        False,
        description="Allow the user to view if tickets are stamped"
    )
    stamp_ticket: bool = Field(
        False,
        description="Allow the user to stamp tickets for event"
    )


    @staticmethod
    def is_owner(event_id: str, check_public_key: str) -> bool:
        """
        Check if public key belongs to event owner.

        :param event_id: unique event identifier
        :param check_public_key: public key to check for ownership status
        :return: event ownership status of checked public key
        """

        public_key_hash = permissions_store.load_owner_public_key_hash(event_id)

        if public_key_hash is None:
            raise DomainException(ErrorKind.NOT_FOUND, "event not found")
        
        return hash.generate_bytes(check_public_key) == public_key_hash


    @classmethod
    def load(cls, event_id: str, target_public_key: str) -> Self:
        """
        Load event permissions.

        :param event_id: unique event identifier
        :param target_public_key: public key of the target user for permission access
        :return: event permissions
        """

        if Permissions.is_owner(event_id, target_public_key):
            return cls(
                cancel_ticket=True,
                see_ticket_flag=True,
                update_ticket_flag=True,
                authorize_registration=True,
                see_stamped_ticket=True,
                stamp_ticket=True
            )
            # enable all permissions
        
        permissions = permissions_store.load_permissions(event_id, target_public_key)

        if permissions is None:
            return cls()
            # disable all permissions

        return cls(**permissions)


    def is_authorized(self, permission: str) -> bool:
        """
        Check if a loaded permission is set.

        :param permission: permission field to check
        :return: authorization status
        """

        if permission not in Permissions.model_fields:
            raise Exception(f"incorrect permission: '{permission}'")

        return getattr(self, permission)


    def update(self, event_id: str, target_public_key: str) -> None:
        """
        Update event permissions.

        :param event_id: unique event identifier
        :param target_public_key: public key of the target user for permission update
        """

        if all(not getattr(self, name) for name in Permissions.model_fields):
            permissions_store.remove_permissions(event_id, target_public_key)
            return

        permissions_store.update_permissions(
            event_id,
            target_public_key,
            self.model_dump()
        )