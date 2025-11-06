"""
Base authenticated data packet models.

:author: Max Milazzo
"""



from app.crypto.asymmetric import AKE
from app.util import keys
from config import REDIS_URL

import time
import uuid
from fastapi import HTTPException
from pydantic import BaseModel, Field
from threading import Lock
from typing import Generic, Self, TypeVar



TIMESTAMP_ERROR = 10
# timestamp error allowance (in seconds) for requests


if REDIS_URL is None:
    STATE_CLEANUP_INTERVAL = 10

    nonce_store = {}
    store_lock = Lock()
    next_cleanup = time.time() + STATE_CLEANUP_INTERVAL
    # set up in-memory fallback for nonce key/value storage replay prevention

else:
    import redis

    try:
        REDIS = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        REDIS.ping()
        # set up Redis for nonce key/value storage replay prevention

    except Exception as e:
        raise Exception(f"Redis connection failed: {e}") from e


T = TypeVar("T")



class Data(BaseModel, Generic[T]):
    """
    Internal signed data payload.
    """

    nonce: str = Field(..., description="Unique UUID nonce")
    timestamp: float = Field(..., description="Epoch timestamp at send time")
    content: T = Field(..., description="Data contents")


    @classmethod
    def load(self, content: T) -> Self:
        """
        Load content into a data payload.

        :param content: content to be loaded
        :return: new valid data payload with injected content
        """

        return self(
            id=str(uuid.uuid4()),
            timestamp=time.time(),
            content=content
        )
    


class Auth(BaseModel, Generic[T]):
    """
    External packet containing signed payload, sender public key, and signature.
    """

    data: Data[T] = Field(..., description="Authenticated data")
    public_key: str = Field(..., description="Public key")
    signature: str = Field(..., description="Digital signature")

    @classmethod
    def load(self, data: Data[T]) -> Self:
        """
        Sign a data payload and load into an authenticated packet.

        :param data: data payload
        :return: new valid authenticated packet with injected data payload
        """

        cipher = AKE(private_key=keys.priv())

        return self(
            data=data, public_key=keys.pub(),
            signature=cipher.sign(data.model_dump())
        )


    def unwrap(self) -> T:
        """
        Unwrap internal data packet raw contents.

        :return: data packet contents
        """

        return self.data.content


    def authenticate(self) -> T:
        """
        Authenticate a received packet.

        :return: validated data packet contents
        """

        cipher = AKE(public_key=self.public_key)
        now = time.time()

        if abs(now - self.data.timestamp) > TIMESTAMP_ERROR:
            raise HTTPException(status_code=401, detail="Timestamp sync failure")
            # check for expired timestamp

        if REDIS_URL is None:
            global next_cleanup
            
            with store_lock:
                if self.data.nonce in nonce_store:
                    raise HTTPException(
                        status_code=400,
                        detail="Duplicate request nonce detected."
                    )
                    # check for duplicate request nonce

                nonce_store[self.data.nonce] = self.data.timestamp
                # set nonce key in global storage

                to_delete = []

                if next_cleanup <= now:
                    for key, value in nonce_store.items():
                        if abs(now - value) > TIMESTAMP_ERROR:
                            to_delete.append(key)
                            # mark expired nonce keys for cleanup
                            
                    for key in to_delete:
                        del nonce_store[key]
                        # delete expired nonce keys

                    next_cleanup = now + STATE_CLEANUP_INTERVAL

        else:
            key = f"replay:{self.public_key}:{self.data.nonce}"
            was_set = REDIS.set(
                name=key,
                value=str(self.data.timestamp),
                nx=True,
                ex=TIMESTAMP_ERROR
            )
            # set nonce key in Redis

            if not was_set:
                raise HTTPException(
                    status_code=400,
                    detail="Duplicate request nonce detected"
                )
                # check for duplicate request nonce

        if not cipher.verify(self.signature, self.data.model_dump(exclude_unset=True)):
            raise HTTPException(status_code=401, detail="Authentication failed")
            # verify signature
        
        return self.data.content