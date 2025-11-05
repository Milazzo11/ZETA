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


from config import REDIS_URL


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


## TODO * can model dump be used everywhere instead of to_dict?


from threading import Lock


T = TypeVar("T")


TIMESTAMP_ERROR = 10
# timestamp error allowance (in seconds) for requests


if REDIS_URL is None:
    STATE_CLEANUP_INTERVAL = 10

    id_store = {}
    store_lock = Lock()  # To handle concurrency
    next_cleanup = time.time() + STATE_CLEANUP_INTERVAL

else:
    import redis

    try:
        REDIS = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        REDIS.ping()  # verify connectivity

    except Exception as e:
        raise Exception(f"Redis connection failed: {e}") from e
















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
    


    
    ## ALSO TODO -- rn, it is required that users send everything for verification... but we don't want that


class Auth(BaseModel, Generic[T]):
    data: Data[T] = Field(..., description="Authenticated data")
    public_key: str = Field(..., description="Public key (to verify signature)")
    signature: str = Field(
        ..., description="Digital signature (JWS of the internal JSON data block)"
    )

    @classmethod
    def load(self, data: Data[T]) -> "Auth":
        """
        """

        cipher = AKE(private_key=keys.priv())

        return self(
            data=data, public_key=keys.pub(),
            signature=cipher.sign(data.model_dump())
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

        if REDIS_URL is None:
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

        else:
            # Atomic first-use with TTL; returns True if key was set, None/False if it already existed
            key = f"replay:{self.public_key}:{self.data.id}"
            # store timestamp as value for optional auditing/debug; TTL = TIMESTAMP_ERROR
            was_set = REDIS.set(name=key, value=str(self.data.timestamp), nx=True, ex=TIMESTAMP_ERROR)
            if not was_set:
                raise HTTPException(status_code=400, detail="Duplicate request ID detected.")

        challenge_verif(self.data)

        if not cipher.verify(self.signature, self.data.model_dump(exclude_unset=True)):
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        return self.data.content