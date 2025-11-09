"""
Error to HTTP code mappings.

:author: Max Milazzo
"""



from .errors import ErrorKind



HTTP_CODE = {
    ErrorKind.VALIDATION: 400,
    ErrorKind.NOT_FOUND: 404,
    ErrorKind.CONFLICT: 409,
    ErrorKind.PERMISSION: 403,
    ErrorKind.UNAVAILABLE: 503,
    ErrorKind.INTERNAL: 500
}