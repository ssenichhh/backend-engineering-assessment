from django.contrib.auth import password_validation
from oper.rest_framework_utils import Serializer
from rest_framework import serializers
from users.models import User, UserRole


class UserBaseSerializer(Serializer):
    default_error_message = "The data you entered is not valid. Please adjust your information and try again."


class UserLoginSerializer(UserBaseSerializer):
    email = serializers.CharField(
        allow_blank=False,
        error_messages={
            "blank": "Email cannot be blank.",
            "required": "Email is required.",
        },
    )
    password = serializers.CharField(
        allow_blank=False,
        error_messages={
            "blank": "Password cannot be blank.",
            "required": "Password is required.",
        },
    )


class UserLoginModelSerializer(UserBaseSerializer, serializers.ModelSerializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        email = (data.get("email") or "").strip()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        self.instance = user
        return data

    class Meta:
        model = User
        fields = ("email", "password")


class UserRegisterSerializer(UserBaseSerializer):
    email = serializers.CharField(
        allow_blank=False,
        error_messages={
            "blank": "Email cannot be blank.",
            "required": "Email is required.",
        },
    )
    password = serializers.CharField(
        allow_blank=False,
        error_messages={
            "blank": "Password cannot be blank.",
            "required": "Password is required.",
        },
    )
    first_name = serializers.CharField(
        allow_blank=False,
        error_messages={
            "blank": "First name cannot be blank.",
            "required": "First name is required.",
        },
    )
    last_name = serializers.CharField(
        allow_blank=False,
        error_messages={
            "blank": "Last name cannot be blank.",
            "required": "Last name is required.",
        },
    )


class UserRegisterModelSerializer(UserBaseSerializer, serializers.ModelSerializer):
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password"]

    def validate_email(self, value: str) -> str:
        value = (value or "").strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate_password(self, value: str) -> str:
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        validated_data["role"] = UserRole.PARTICIPANT
        return User.objects.create_user(**validated_data)


class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "role"]


class UserGenericLoginResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    role = serializers.CharField()
    is_superuser = serializers.BooleanField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
