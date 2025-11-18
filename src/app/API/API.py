"""
API request flows.

:author: Max Milazzo
"""



from app.API.models.base import Auth, ErrorResponse
from app.API.models.endpoints import *
from app.error.errors import DomainException



def create_event(data: Auth[CreateRequest]) -> Auth[CreateResponse]:
    """
    /create request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = CreateResponse.generate(request, data.public_key)
    
    return Auth[CreateResponse].load(response)


def search_events(data: Auth[SearchRequest]) -> Auth[SearchResponse]:
    """
    /search request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = SearchResponse.generate(request)

    return Auth[SearchResponse].load(response)


def register_user(data: Auth[RegisterRequest]) -> Auth[RegisterResponse]:
    """
    /register request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = RegisterResponse.generate(request, data.public_key)

    return Auth[RegisterResponse].load(response)


def transfer_ticket(data: Auth[TransferRequest]) -> Auth[TransferResponse]:
    """
    /transfer request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = TransferResponse.generate(request, data.public_key)

    return Auth[TransferResponse].load(response)


def redeem_ticket(data: Auth[RedeemRequest]) -> Auth[RedeemResponse]:
    """
    /redeem request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = RedeemResponse.generate(request, data.public_key)

    return Auth[RedeemResponse].load(response)


def validate_ticket(data: Auth[ValidateRequest]) -> Auth[ValidateResponse]:
    """
    /validate request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = ValidateResponse.generate(request, data.public_key)

    return Auth[ValidateResponse].load(response)


def flag_ticket(data: Auth[FlagRequest]) -> Auth[FlagResponse]:
    """
    /flag request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = FlagResponse.generate(request, data.public_key)

    return Auth[FlagResponse].load(response)


def cancel_ticket(data: Auth[CancelRequest]) -> Auth[CancelResponse]:
    """
    /cancel request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = CancelResponse.generate(request, data.public_key)

    return Auth[CancelResponse].load(response)


def delete_event(data: Auth[DeleteRequest]) -> Auth[DeleteResponse]:
    """
    /delete request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = DeleteResponse.generate(request, data.public_key)

    return Auth[DeleteResponse].load(response)


def update_permissions(data: Auth[PermissionsRequest]) -> Auth[PermissionsResponse]:
    """
    /permissions request flow.

    :param data: user request
    :return: server response
    """

    request = data.authenticate()
    response = PermissionsResponse.generate(request, data.public_key)

    return Auth[PermissionsResponse].load(response)


def exception_handler(exception: DomainException) -> Auth[ErrorResponse]:
    """
    Produce a signed error response.

    :param exception: application domain error exception
    :return: server error response
    """

    response = ErrorResponse.generate(exception)

    return Auth[ErrorResponse].load(response)