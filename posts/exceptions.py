from rest_framework import status
from rest_framework.exceptions import APIException


class SubmitRateLimitedAPIException(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Try again in a few minutes."
