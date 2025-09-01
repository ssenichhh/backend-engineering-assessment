from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from oper.rest_framework_utils import Serializer
from .models import Quiz, Question, Option, Membership, Submission

User = get_user_model()


# ---- nested create for host ----

class OptionWriteSerializer(Serializer, serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "text", "correct", "position"]
        read_only_fields = ["id", "position"]


class QuestionWriteSerializer(Serializer, serializers.ModelSerializer):
    options = OptionWriteSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "body", "position", "points", "shuffle_options", "options"]
        read_only_fields = ["id", "position"]

    @transaction.atomic
    def create(self, validated_data):
        options = validated_data.pop("options", [])
        validated_data.pop("position", None)
        question = Question.objects.create(**validated_data)
        for option in options:
            option.pop("position", None)
            Option.objects.create(question=question, **option)
        return question

class QuizWriteSerializer(Serializer, serializers.ModelSerializer):
    questions = QuestionWriteSerializer(many=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "state",
            "randomized",
            "starts_at",
            "ends_at",
            "owner",
            "questions",
        ]
        read_only_fields = ["id", "owner"]

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        questions = validated_data.pop("questions", [])
        quiz = Quiz.objects.create(owner=request.user, **validated_data)
        for qd in questions:
            options = qd.pop("options", [])
            qd.pop("position", None)
            question = Question.objects.create(quiz=quiz, **qd)
            for od in options:
                od.pop("position", None)
                Option.objects.create(question=question, **od)
        return quiz

# ---- read serializers ----

class OptionReadSerializer(Serializer, serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "text"]


class QuestionReadSerializer(Serializer, serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "body", "position", "points", "options"]

    def get_options(self, obj):
        user = self.context["request"].user
        qs = obj.options.all()
        if obj.shuffle_options:
            qs = qs.order_by("?")
        return OptionReadSerializer(qs, many=True, context=self.context).data


class QuizReadSerializer(Serializer, serializers.ModelSerializer):
    questions = QuestionReadSerializer(many=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "state",
            "randomized",
            "starts_at",
            "ends_at",
            "questions",
        ]


# ---- membership/progress ----

class MembershipSerializer(Serializer, serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    quiz = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "user", "quiz", "active", "progress_pct", "total_score", "joined_at", "updated_at"]


# ---- answering ----

class SubmitSerializer(Serializer, serializers.Serializer):
    quiz_id = serializers.UUIDField()
    question_id = serializers.UUIDField()
    option_id = serializers.UUIDField()

    def create(self, validated_data):
        user = self.context["request"].user
        quiz = Quiz.objects.get(id=validated_data["quiz_id"])
        membership = Membership.objects.filter(quiz=quiz, user=user, active=True).first()
        if not membership:
            raise serializers.ValidationError({"detail": "You are not a member of this quiz."})

        question = Question.objects.filter(id=validated_data["question_id"], quiz=quiz).first()
        if not question:
            raise serializers.ValidationError({"detail": "Question not found in this quiz."})

        option = Option.objects.filter(id=validated_data["option_id"], question=question).first()
        if not option:
            raise serializers.ValidationError({"detail": "Option not found for this question."})

        created = Submission.objects.create(
            membership=membership,
            question=question,
            option=option,
            correct=bool(option.correct),
        )
        membership.recalculate()
        correct_text = question.options.filter(correct=True).values_list("text", flat=True).first()
        return {
            "question": question.body,
            "your_answer": option.text,
            "correct": created.correct,
            "correct_answer": correct_text,
            "score_total": membership.total_score,
            "progress_pct": float(membership.progress_pct),
        }