"""
"""


from app.data.storage import permissions_store
from app.crypto import hash
from app.error.errors import ErrorKind, DomainException

import time
import uuid
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
        """

        public_key_hash = permissions_store.load_owner_public_key_hash(event_id)

        if public_key_hash is None:
            raise DomainException(ErrorKind.NOT_FOUND, "event not found")
        
        return hash.generate_bytes(check_public_key) == public_key_hash


    @staticmethod
    def is_authorized(event_id: str, check_public_key: str, permission: str) -> bool:
        """
        """

        if permission not in Permissions.model_fields:
            raise Exception(f"Incorrect permission: '{permission}'")

        if Permissions.is_owner(event_id, check_public_key):
            return True
        
        ## TODO - finish


    @classmethod
    def load(cls, event_id: str, target_public_key: str) -> Self:
        """
        Load event permissions.

        :param event_id: unique event identifier
        :param target_public_key: public key of the target user for permission access
        :return: event permissions
        """
        
        permissions = permissions_store.load_permissions(event_id, target_public_key)

        if permissions is None:
            raise DomainException(ErrorKind.NOT_FOUND, "user permissions not found")

        return cls(**permissions)


    def update(self, event_id: str, target_public_key: str) -> None:
        """
        Update event permissions.
        """

        permissions_store.update_permissions(
            event_id,
            target_public_key,
            self.model_dump()
        )