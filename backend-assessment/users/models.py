import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, update_last_login
from django.db import models
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from users.managers import UserManager

class UserRole(models.TextChoices):
    OWNER = "OWNER", "Owner"
    PARTICIPANT = "PARTICIPANT", "Participant"

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    role = models.CharField(choices=UserRole.choices, max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def authenticate(self, request=None, password=None):
        """
        Passwordless (no password) -> ensure active, update last_login, return self.
        With password -> verify using self.check_password (raw password), update last_login.
        """
        if not self.is_active:
            raise PermissionDenied("User account is disabled.")

        # Passwordless flow (e.g., SSN/DOB-style logins)
        if password is None:
            update_last_login(None, self)
            return self

        # Email/password flow using the stored hash
        if not self.check_password(password):
            raise AuthenticationFailed("Invalid credentials.")

        update_last_login(None, self)
        return self