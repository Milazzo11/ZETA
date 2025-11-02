"""
"""

import time
from fastapi import HTTPException

from app.data.event import Event
from app.util import keys
from typing import List, Union, Generic, TypeVar, Optional, Protocol
from pydantic import BaseModel, Field

import uuid

from app.crypto.asymmetric import AKE

from config import TIMESTAMP_ERROR, STATE_CLEANUP_INTERVAL

### encrypted ticktu must encrypt some punlic key data to validate owner


##### events probably should use an actual SQL DB

### managing bits in SQL seems easy too...


### REQUEST OBJECTS HANDLE PARSING LOGIC; RESPONSE HANDLE ACCESSING INTERNAL SERVER OPS
# <- move all this to __init__?


### TODO - tickets DO NOT NEED TO BE SEND ENCRYPTED -- BECAUSE THEY WILL ENCRYPT A PUBKEY
### SO EVEN IF ANOTHER USER GETS THE TICKET, IT WILL BE UNVERIFIABLE WITHOUT PRIVKEY ACCESS FOR SIGNATURES


### TODO - optional instead of union in crypto lib


### TODO - maybe figure out best Field conventions "..." vs. description= or just put the thing first


## TODO - ensure no white charactertics in vscode linting


### TODO - prob rework crypto libs to allow JWT and JWE for dict type (but do Union[bytes, str, dict] to generalize)

from threading import Lock





T = TypeVar("T")



id_store = {}
store_lock = Lock()  # To handle concurrency
next_cleanup = time.time() + STATE_CLEANUP_INTERVAL





class Data(BaseModel, Generic[T]):
    id: str = Field(
        ..., description="Unique data transaction ID"
    )  ###default_factory makes docs say this isn't required
    timestamp: float = Field(..., description="Epoch timestamp at send time")
    content: T = Field(..., description="Data contents")

    ### keep ID until message timestamp expire to prevent any form of replay attack

    @classmethod
    def load(self, content: T) -> "Data":
        """
        """

        return self(id=str(uuid.uuid4()), timestamp=time.time(), content=content)
    

    def to_dict(self) -> dict:

        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "content": self.content.to_dict()###<<-- TODO, somehow add interface functionality
        }
    
    ## ALSO TODO -- rn, it is required that users send everything for verification... but we don't want that


class Auth(BaseModel, Generic[T]):
    data: Data[T] = Field(..., description="Authenticated data")
    public_key: str = Field(..., description="Public key (to verify signature)")
    signature: str = Field(
        ..., description="Digital signature (JWT of the internal JSON data block)"
    )

    @classmethod
    def load(self, data: Data[T]) -> "Auth":
        """
        """

        cipher = AKE(private_key=keys.priv())

        return self(
            data=data, public_key=keys.pub(),
            signature=cipher.sign(data.to_dict())
        )


    def unwrap(self) -> T:
        return self.data.content


    def authenticate(self, challenge_verif: callable = lambda _: None) -> T:
        """
        """

        global next_cleanup
        cipher = AKE(public_key=self.public_key)

        ### TODO - (done)
        ### verify that ID is unique within timeframe to prevent replay
        ### call "challenge_verif" to confirm completion of additional complexity challenge (not to be implemented in this version)

        now = time.time()
        if abs(now - self.data.timestamp) > TIMESTAMP_ERROR:
            raise HTTPException(status_code=401, detail="Timestamp sync failure")

        with store_lock:
            if self.data.id in id_store:
                raise HTTPException(
                    status_code=400, detail="Duplicate request ID detected."
                )

            id_store[self.data.id] = self.data.timestamp
            to_delete = []

            if next_cleanup <= now:
                for key, value in id_store.items():
                    if abs(now - value) > TIMESTAMP_ERROR:
                        to_delete.append(key)
                        
                for key in to_delete:
                    del id_store[key]

                next_cleanup = now + STATE_CLEANUP_INTERVAL

        challenge_verif(self.data)

        if not cipher.verify(self.signature, self.data.to_dict()):
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        return self.data.content


    def to_dict(self) -> dict:
        """
        """

        return {
            "data": self.data.to_dict(),
            "public_key": self.public_key,
            "signature": self.signature
        }