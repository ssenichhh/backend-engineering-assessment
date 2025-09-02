from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user(self):
        u = User.objects.create_user(
            email="user@example.com",
            password="s3cret",
            role="OWNER",
        )
        self.assertEqual(u.email, "user@example.com")
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertTrue(u.check_password("s3cret"))

    def test_create_superuser(self):
        su = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass",
            role="OWNER",
        )
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_superuser)
        self.assertTrue(su.check_password("adminpass"))

    def test_authenticate_success_updates_last_login(self):
        u = User.objects.create_user(
            email="auth@example.com",
            password="okpass",
            role="OWNER",
        )
        self.assertIsNone(u.last_login)
        returned = u.authenticate(password="okpass")
        self.assertEqual(returned.pk, u.pk)
        u.refresh_from_db()
        self.assertIsNotNone(u.last_login)

    def test_authenticate_wrong_password_raises(self):
        u = User.objects.create_user(
            email="bad@example.com",
            password="right",
            role="OWNER",
        )
        with self.assertRaises(AuthenticationFailed):
            u.authenticate(password="wrong")
