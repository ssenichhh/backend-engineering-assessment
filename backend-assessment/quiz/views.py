from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from oper.rest_framework_utils import APIResponse
from quiz.models import Quiz, Membership, QuizState
from quiz.serializers import QuizWriteSerializer, QuizReadSerializer, MembershipSerializer, SubmitSerializer
from quiz.services import add_members, dashboard
from quiz.permissions import IsOwnerUser, IsParticipantUser


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        owner_crud = {"create", "update", "partial_update", "destroy"}
        if self.action in owner_crud:
            return [IsAuthenticated(), IsOwnerUser()]
        return super().get_permissions()

    def get_serializer_class(self):
        return QuizWriteSerializer if self.action in {"create", "update", "partial_update"} else QuizReadSerializer

    def get_queryset(self):
        u = self.request.user
        owned = Quiz.objects.filter(owner=u)
        member = Quiz.objects.filter(memberships__user=u, memberships__active=True)
        return (owned | member).distinct().prefetch_related("questions__options")

    def perform_create(self, serializer):
        serializer.save()


    @action(methods=["post"], detail=True, url_path="publish",
            permission_classes=[IsAuthenticated, IsOwnerUser])
    def publish(self, request, pk=None):
        quiz = self.get_object()
        if quiz.owner != request.user:
            return APIResponse(data={"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
        quiz.state = QuizState.LIVE
        if not quiz.starts_at:
            quiz.starts_at = timezone.now()
        quiz.save(update_fields=["state", "starts_at"])
        return APIResponse(data={"state": quiz.state}, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True, url_path="close",
            permission_classes=[IsAuthenticated, IsOwnerUser])
    def close(self, request, pk=None):
        quiz = self.get_object()
        if quiz.owner != request.user:
            return APIResponse(data={"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
        quiz.state = QuizState.CLOSED
        quiz.save(update_fields=["state"])
        return APIResponse(data={"state": quiz.state}, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True, url_path="members",
            permission_classes=[IsAuthenticated, IsOwnerUser])
    def members(self, request, pk=None):
        quiz = self.get_object()
        if quiz.owner != request.user:
            return APIResponse(data={"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
        user_ids = request.data.get("user_ids") or []
        memberships = add_members(request.user, pk, user_ids)
        data = MembershipSerializer(memberships, many=True).data
        return APIResponse(data=data, status=status.HTTP_201_CREATED)

    @action(methods=["get"], detail=True, url_path="progress",
            permission_classes=[IsAuthenticated, IsParticipantUser])
    def progress(self, request, pk=None):
        quiz = self.get_object()
        if quiz.owner == request.user:
            return APIResponse(data=dashboard(request.user, pk), status=status.HTTP_200_OK)
        membership = Membership.objects.filter(quiz=quiz, user=request.user).first()
        if not membership:
            return APIResponse(data={"detail": "Not a member"}, status=status.HTTP_404_NOT_FOUND)
        return APIResponse(
            data={"progress_pct": float(membership.progress_pct), "total_score": membership.total_score},
            status=status.HTTP_200_OK,
        )

    @action(methods=["post"], detail=True, url_path="submit",
            permission_classes=[IsAuthenticated, IsParticipantUser])
    def submit(self, request, pk=None):
        serializer = SubmitSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        return APIResponse(data=payload, status=status.HTTP_201_CREATED)