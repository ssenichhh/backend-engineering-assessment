# quizzes/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet

app_name = "quiz"

router = DefaultRouter()
router.register(r"", QuizViewSet, basename="quiz")

urlpatterns = [
    path("", include(router.urls)),
]