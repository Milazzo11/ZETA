"""
Base authenticated data packet models.

:author: Max Milazzo
"""



from app.crypto.asymmetric import AKC
from app.error.errors import ErrorKind, DomainException
from app.util import keys

import math
import time
import uuid
from pydantic import BaseModel, Field
from typing import Generic, Self, TypeVar



TIMESTAMP_ERROR = 10
# timestamp error allowance (in seconds) for requests


TTL_SECURITY_PAD = 1
# small amount of additional time (in seconds) added to nonce store TTL for security
# (useful if, for example, there are slight clock skews)


SERVICE_STARTED = False
# authentication nonce-tracker service status flag


REDIS = None
# Redis client


STATE_CLEANUP_INTERVAL = 10
nonce_store = None
store_lock = None
next_cleanup = None
# in-memory fallback global definitions


T = TypeVar("T")



class Data(BaseModel, Generic[T]):
    """
    Internal signed data payload.
    """

    nonce: str = Field(..., description="Unique UUID nonce")
    timestamp: float = Field(..., description="Epoch timestamp at send time")
    content: T = Field(..., description="Data contents")


    @classmethod
    def load(cls, content: T) -> Self:
        """
        Load content into a data payload.

        :param content: content to be loaded
        :return: new valid data payload with injected content
        """

        return cls(
            nonce=str(uuid.uuid4()),
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


    @staticmethod
    def start_service(redis_url: str | None) -> None:
        """
        Start the authentication nonce-tracker service.

        :param redis_url: Reddis connection URL string or None to use in-memory service
        """

        global SERVICE_STARTED
        SERVICE_STARTED = True
        # set service flag

        if redis_url is None:
            from threading import Lock
            global nonce_store, store_lock, next_cleanup

            nonce_store = {}
            store_lock = Lock()
            next_cleanup = time.time() + STATE_CLEANUP_INTERVAL
            # set up in-memory fallback for nonce key/value storage replay prevention

            return

        import redis
        global REDIS

        try:
            REDIS = redis.Redis.from_url(redis_url, decode_responses=True)
            REDIS.ping()
            # set up Redis for nonce key/value storage replay prevention

        except Exception as e:
            raise Exception("redis connection failed") from e


    @classmethod
    def load(
        cls,
        content: T,
        cipher: AKC = keys.RESPONSE_SIGNER,
    ) -> Self:
        """
        Sign a data payload and load into an authenticated packet.

        :param content: content to be loaded and authenticated
        :param cipher: asymmetric signing cipher
        :return: new valid authenticated packet with injected data payload
        """

        data = Data.load(content)

        return cls(
            data=data,
            public_key=cipher.public_key,
            signature=cipher.sign(data.model_dump())
        )


    def unwrap(self) -> T:
        """
        Unwrap internal data packet raw contents.

        :return: data packet contents
        """

        return self.data.content
    

    def _nonce_check_naive(self) -> None:
        """
        Naive in-memory repeat nonce detection.
        """

        global next_cleanup
        
        with store_lock:
            if self.data.nonce in nonce_store:
                raise DomainException(ErrorKind.CONFLICT, "duplicate request nonce")
                # check for duplicate request nonce

            nonce_store[self.data.nonce] = self.data.timestamp
            # set nonce key in global storage

            now = time.time()

            if next_cleanup <= now:
                to_delete = []

                for key, value in nonce_store.items():
                    if now > value + TIMESTAMP_ERROR + TTL_SECURITY_PAD:
                        to_delete.append(key)
                        # mark expired nonce keys for cleanup
                        
                for key in to_delete:
                    del nonce_store[key]
                    # delete expired nonce keys

                next_cleanup = now + STATE_CLEANUP_INTERVAL


    def _nonce_check_redis(self) -> None:
        """
        Redis-based repeat nonce detection.
        """

        key = f"replay:{self.public_key}:{self.data.nonce}"
        expiration = self.data.timestamp + TIMESTAMP_ERROR + TTL_SECURITY_PAD

        was_set = REDIS.set(
            name=key,
            value=str(self.data.timestamp),
            nx=True,
            ex=int(math.ceil(expiration - time.time()))
        )
        # set nonce key in Redis

        if not was_set:
            raise DomainException(ErrorKind.CONFLICT, "duplicate request nonce")
            # check for duplicate request nonce


    def authenticate(self) -> T:
        """
        Authenticate a received packet.

        :return: validated data packet contents
        """

        if not SERVICE_STARTED:
            raise Exception("Authentication nonce-tracker service not started")

        if abs(time.time() - self.data.timestamp) > TIMESTAMP_ERROR:
            raise DomainException(ErrorKind.VALIDATION, "timestamp out of sync")
            # check for expired timestamp

        if REDIS is None:
            self._nonce_check_naive()

        else:
            self._nonce_check_redis()

        cipher = AKC(public_key=self.public_key)

        if not cipher.verify(self.signature, self.data.model_dump(exclude_unset=True)):
            raise DomainException(ErrorKind.PERMISSION, "signature verification failed")
            # verify signature
        
        return self.data.content