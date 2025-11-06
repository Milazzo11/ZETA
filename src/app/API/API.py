"""
API endpoint mappings.

:author: Max Milazzo
"""


from app.API.models import *

from fastapi import HTTPException


def search_events(data: Auth[SearchRequest]) -> Auth[SearchResponse]:
    request = data.authenticate()
    response = SearchResponse.generate(request)

    packet = Data[SearchResponse].load(response)
    return Auth[SearchResponse].load(packet)


def create_event(data: Auth[CreateRequest]) -> Auth[CreateResponse]:

    request = data.authenticate()
    response = CreateResponse.generate(request, data.public_key)
    
    packet = Data[CreateResponse].load(response)
    return Auth[CreateResponse].load(packet)



def register_user(data: Auth[RegisterRequest]) -> Auth[RegisterResponse]:
    request = data.authenticate()
    response = RegisterResponse.generate(request, data.public_key)

    packet = Data[RegisterResponse].load(response)
    return Auth[RegisterResponse].load(packet)


def transfer_ticket(data: Auth[TransferRequest]) -> Auth[TransferResponse]:
    request = data.authenticate()
    response = TransferResponse.generate(request, data.public_key)

    packet = Data[TransferResponse].load(response)
    return Auth[TransferResponse].load(packet)


def redeem_ticket(data: Auth[RedeemRequest]) -> Auth[RedeemResponse]:
    request = data.authenticate()
    response = RedeemResponse.generate(request, data.public_key)

    packet = Data[RedeemResponse].load(response)
    return Auth[RedeemResponse].load(packet)


def verify_redemption(data: Auth[VerifyRequest]) -> Auth[VerifyResponse]:
    request = data.authenticate()
    response = VerifyResponse.generate(request)

    packet = Data[VerifyResponse].load(response)
    return Auth[VerifyResponse].load(packet)


def delete_event(data: Auth[DeleteRequest]) -> Auth[DeleteResponse]:
    request = data.authenticate()
    response = DeleteResponse.generate(request, data.public_key)

    packet = Data[DeleteResponse].load(response)
    return Auth[DeleteResponse].load(packet)


def exception_handler(exception: HTTPException) -> Auth[Error]:
    response = Error.generate(exception)

    packet = Data[Error].load(response)
    return Auth[Error].load(packet)