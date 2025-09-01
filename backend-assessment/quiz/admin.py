from django.contrib import admin
from .models import Quiz, Question, Option, Membership, Submission


class OptionInline(admin.TabularInline):
    model = Option
    extra = 2


class QuestionInline(admin.StackedInline):
    model = Question
    fields = ("body", "position", "points", "shuffle_options")
    extra = 1
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ("title", "owner", "state", "starts_at", "ends_at", "created_at")
    list_filter = ("state",)
    search_fields = ("title", "owner__email")
    autocomplete_fields = ("owner",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    ВАЖНО: есть search_fields, чтобы его можно было использовать в autocomplete_fields других админов.
    """
    inlines = [OptionInline]
    list_display = ("body", "quiz", "position", "points", "shuffle_options")
    list_filter = ("quiz",)
    search_fields = ("body", "quiz__title")            # ← обязательно для автокомплита
    autocomplete_fields = ("quiz",)                    # опционально, но удобно


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "correct", "position")
    list_filter = ("correct", "question__quiz")
    search_fields = ("text", "question__body", "question__quiz__title")
    autocomplete_fields = ("question",)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("quiz", "user", "active", "progress_pct", "total_score", "joined_at")
    list_filter = ("quiz", "active")
    search_fields = ("quiz__title", "user__email")
    autocomplete_fields = ("quiz", "user")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("membership", "question", "option", "correct", "created_at")
    list_filter = ("correct", "membership__quiz")
    search_fields = ("question__body", "membership__user__email", "option__text")
    autocomplete_fields = ("membership", "question", "option")