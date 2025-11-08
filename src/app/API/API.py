"""
API request flows.

:author: Max Milazzo
"""



from app.API.models import *

from fastapi import HTTPException



def search_events(data: Auth[SearchRequest]) -> Auth[SearchResponse]:
    """
    /search request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = SearchResponse.generate(request)

    packet = Data[SearchResponse].load(response)
    return Auth[SearchResponse].load(packet)


def create_event(data: Auth[CreateRequest]) -> Auth[CreateResponse]:
    """
    /create request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = CreateResponse.generate(request, data.public_key)
    
    packet = Data[CreateResponse].load(response)
    return Auth[CreateResponse].load(packet)


def register_user(data: Auth[RegisterRequest]) -> Auth[RegisterResponse]:
    """
    /register request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = RegisterResponse.generate(request, data.public_key)

    packet = Data[RegisterResponse].load(response)
    return Auth[RegisterResponse].load(packet)


def transfer_ticket(data: Auth[TransferRequest]) -> Auth[TransferResponse]:
    """
    /transfer request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = TransferResponse.generate(request, data.public_key)

    packet = Data[TransferResponse].load(response)
    return Auth[TransferResponse].load(packet)


def redeem_ticket(data: Auth[RedeemRequest]) -> Auth[RedeemResponse]:
    """
    /redeem request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = RedeemResponse.generate(request, data.public_key)

    packet = Data[RedeemResponse].load(response)
    return Auth[RedeemResponse].load(packet)


def verify_redemption(data: Auth[VerifyRequest]) -> Auth[VerifyResponse]:
    """
    /verify request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = VerifyResponse.generate(request)

    packet = Data[VerifyResponse].load(response)
    return Auth[VerifyResponse].load(packet)


def delete_event(data: Auth[DeleteRequest]) -> Auth[DeleteResponse]:
    """
    /delete request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = DeleteResponse.generate(request, data.public_key)

    packet = Data[DeleteResponse].load(response)
    return Auth[DeleteResponse].load(packet)



## TODO - this is prob gonna have to go
def exception_handler(exception: HTTPException) -> Auth[Error]:
    """
    Produce a signed error response.

    :param exception: HTTP exception
    :return: server response
    """

    response = Error.generate(exception)

    packet = Data[Error].load(response)
    return Auth[Error].load(packet)