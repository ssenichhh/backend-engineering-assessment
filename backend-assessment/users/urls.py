from django.urls import path
from rest_framework.routers import DefaultRouter
from users.views import LoginView, RegisterView, UserView

app_name = "users"
router = DefaultRouter()
router.register("users", UserView, basename="user")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
] + router.urls
