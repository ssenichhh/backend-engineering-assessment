import uuid

from django.db import models
from django.utils import timezone
from users.models import User


class QuizState(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    LIVE = "LIVE", "Live"
    CLOSED = "CLOSED", "Closed"


class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="quizzes_owned",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    state = models.CharField(
        max_length=12, choices=QuizState.choices, default=QuizState.DRAFT
    )
    randomized = models.BooleanField(default=False)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def is_open_for(self, user) -> bool:
        now = timezone.now()
        if self.state != QuizState.LIVE:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return Membership.objects.filter(user=user, quiz=self, active=True).exists()


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    body = models.TextField()
    position = models.PositiveIntegerField(default=0, db_index=True)
    points = models.PositiveSmallIntegerField(default=1)
    shuffle_options = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "position"], name="uq_question_position_per_quiz"
            ),
        ]

    def __str__(self) -> str:
        return self.body[:60]

    def save(self, *args, **kwargs):
        if not self.position:
            last = (
                Question.objects.filter(quiz=self.quiz).aggregate(
                    mx=models.Max("position")
                )["mx"]
                or 0
            )
            self.position = last + 1
        super().save(*args, **kwargs)


class Option(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    text = models.CharField(max_length=500)
    correct = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position"]

    def save(self, *args, **kwargs):
        if not self.position:
            last = (
                Option.objects.filter(question=self.question).aggregate(
                    mx=models.Max("position")
                )["mx"]
                or 0
            )
            self.position = last + 1
        super().save(*args, **kwargs)


class Membership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="quiz_memberships"
    )
    active = models.BooleanField(default=True)
    progress_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )  # 0..100
    total_score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("quiz", "user")]
        indexes = [models.Index(fields=["quiz", "user"])]

    def __str__(self) -> str:
        return f"{self.user} → {self.quiz}"

    def recalculate(self):
        total_questions = self.quiz.questions.count()
        answered = Submission.objects.filter(membership=self).count()
        correct_points = (
            Submission.objects.filter(membership=self, correct=True)
            .select_related("question")
            .aggregate(points=models.Sum("question__points"))
            .get("points")
            or 0
        )
        self.total_score = int(correct_points)
        self.progress_pct = (
            round(100 * (answered / total_questions), 2) if total_questions else 0
        )
        self.save(update_fields=["total_score", "progress_pct", "updated_at"])


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="submissions"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("membership", "question")]
        indexes = [models.Index(fields=["membership", "question"])]
