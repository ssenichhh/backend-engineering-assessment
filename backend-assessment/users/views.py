from django_filters.rest_framework import DjangoFilterBackend
from oper.rest_framework_utils import APIResponse, custom_exception_handler
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from users.models import User
from users.serializers import (
    UserGenericLoginResponseSerializer,
    UserLoginModelSerializer,
    UserLoginSerializer,
    UserRegisterModelSerializer,
    UserRegisterSerializer,
    UserViewSerializer,
)


class RegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        input_simple_serializer = UserRegisterSerializer(data=request.data)
        input_simple_serializer.is_valid(raise_exception=True)

        serializer = UserRegisterModelSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse(
                data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()

        return APIResponse(data=serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        input_simple_serializer = UserLoginSerializer(data=request.data)
        input_simple_serializer.is_valid(raise_exception=True)

        user_serializer = UserLoginModelSerializer(data=request.data)
        if not user_serializer.is_valid():
            return APIResponse(
                data=user_serializer.errors, status=status.HTTP_403_FORBIDDEN
            )

        user = user_serializer.instance
        user.authenticate()

        response_serializer = UserGenericLoginResponseSerializer(user)
        return APIResponse(data=response_serializer.data, status=status.HTTP_200_OK)

    def get_exception_handler(self):
        return custom_exception_handler


class UserView(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserViewSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["role"]
