from copy import deepcopy

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import exception_handler
from users.models import User


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if not response:  # handle 500 responses
        return response

    # Preserve the original error payload
    original_errors = deepcopy(response.data)
    return_data = {"success": "False", "data": original_errors}

    if response.status_code == HTTP_400_BAD_REQUEST:
        message = "Bad request"
        if not context["kwargs"].get("message") and hasattr(
            exc, "default_error_message"
        ):
            message = getattr(exc, "default_error_message")

        return_data["message"] = message
        try:
            if context["request"].user.is_authenticated and context["request"].user:
                return_data["user_id"] = context["request"].user.id
        except User.DoesNotExist:
            pass

    if response.status_code == HTTP_404_NOT_FOUND:
        return_data.pop("data", None)
        return_data["message"] = str(exc)

    response.data = return_data
    return response


class APIResponse(Response):
    def __init__(
        self,
        data: dict = None,
        status=None,
        template_name=None,
        headers=None,
        exception=False,
        content_type=None,
        **kwargs,
    ):
        is_success = True
        return_data = {}

        if status and status >= HTTP_400_BAD_REQUEST:
            is_success = False

        if data:
            return_data["data"] = data

        return_data.update({"success": str(is_success), **kwargs})

        super().__init__(
            data=return_data,
            status=status,
            template_name=template_name,
            headers=headers,
            exception=exception,
            content_type=content_type,
        )


class Serializer(serializers.Serializer):
    default_error_message = None

    def is_valid(self, *, raise_exception=False):
        valid = super().is_valid(raise_exception=False)
        if not valid and raise_exception:
            exc = serializers.ValidationError(self.errors)
            exc.default_error_message = getattr(self, "default_error_message", False)
            raise exc
        return valid
