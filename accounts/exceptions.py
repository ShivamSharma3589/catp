from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidGoogleCredential(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Invalid Google credential.'
    default_code = 'invalid_google_credential'


class GoogleAuthUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Google login is not configured on the server.'
    default_code = 'google_auth_unavailable'
