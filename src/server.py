"""
ZETA Server.

:author: Max Milazzo
"""



from app.API import API
from app.API.models import *
from app.data.storage.connection import pool
from app.error.errors import ErrorKind, DomainException
from app.error.map import HTTP_CODE
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator



logger = logging.getLogger("zeta")
logger.setLevel(logging.ERROR)

if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
    fh = logging.FileHandler(
        os.path.join("data", "error.log"),
        mode="a",
        encoding="utf-8"
    )
    fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    fh.setLevel(logging.ERROR)
    logger.addHandler(fh)
    # initialize application logger


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    Automatically close database connection pool when the server shuts down.
    """

    yield
    pool.close()


app = FastAPI(lifespan=lifespan)



@app.post("/search", description="Search for events")
async def search_events(data: Auth[SearchRequest]) -> Auth[SearchResponse]:
    return API.search_events(data)


@app.post("/create", description="Create a new event on the server")
async def create_event(data: Auth[CreateRequest]) -> Auth[CreateResponse]:
    return API.create_event(data)


@app.post("/register", description="Register for an event and receieve a ticket")
async def register_user(data: Auth[RegisterRequest]) -> Auth[RegisterResponse]:
    return API.register_user(data)


@app.post("/transfer", description="Receive a ticket transfer from another user")
async def transfer_ticket(data: Auth[TransferRequest]) -> Auth[TransferResponse]:
    return API.transfer_ticket(data)


@app.post("/redeem", description="Redeem a ticket")
async def redeem_ticket(data: Auth[RedeemRequest]) -> Auth[RedeemResponse]:
    return API.redeem_ticket(data)


@app.post("/verify", description="Verify that a user has redeemed his ticket")
async def verify_redemption(data: Auth[VerifyRequest]) -> Auth[VerifyResponse]:
    return API.verify_redemption(data)


@app.post("/cancel", description="Cancel an event attendee's ticket")
async def cancel_ticket(data: Auth[CancelRequest]) -> Auth[CancelResponse]:
    return API.cancel_ticket(data)


@app.post("/delete", description="Delete an event")
async def delete_event(data: Auth[DeleteRequest]) -> Auth[DeleteResponse]:
    return API.delete_event(data)


@app.exception_handler(DomainException)
async def domain_exception_handler(
    _: Request,
    exception: DomainException
) -> JSONResponse:
    """
    Handle domain-level exceptions and return a structured error response.

    :param exception: interrupting exception being handled
    :return: server error response
    """

    if exception.kind == ErrorKind.INTERNAL:
        logger.error(repr(exception), exc_info=exception)

    auth_error = API.exception_handler(exception)
    # generated authenticated error response

    return JSONResponse(
        status_code=HTTP_CODE[exception.kind],
        content=auth_error.model_dump()
    )


@app.exception_handler(Exception)
async def exception_handler(_: Request, exception: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions and return a generic internal error response.

    :param exception: interrupting exception being handled
    :return: server error response
    """

    logger.error(repr(exception), exc_info=exception)

    auth_error = API.exception_handler(
        DomainException(
            kind=ErrorKind.INTERNAL,
            message="unknwon error"
        )
    )
    # generated authenticated error response

    return JSONResponse(
        status_code=HTTP_CODE[ErrorKind.INTERNAL],
        content=auth_error.model_dump()
    )