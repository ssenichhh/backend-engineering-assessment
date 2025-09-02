from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .models import Membership, Quiz


def add_members(owner, quiz_id, user_ids):
    if not user_ids:
        raise ValidationError({"detail": "user_ids cannot be empty"})
    quiz = get_object_or_404(Quiz, id=quiz_id, owner=owner)
    memberships = []
    for uid in user_ids:
        memder, _ = Membership.objects.get_or_create(
            quiz=quiz, user_id=uid, defaults={"active": True}
        )
        memberships.append(memder)
    return memberships


def dashboard(owner, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, owner=owner)
    data = (
        quiz.memberships.select_related("user")
        .values("user__first_name", "user__last_name")
        .annotate(progress=Sum("progress_pct"), score=Sum("total_score"))
        .order_by("-score")
    )
    return [
        {
            "participant": f"{row['user__first_name']} {row['user__last_name']}".strip(),
            "progress": float(row["progress"]),
            "total_score": row["score"],
        }
        for row in data
    ]
