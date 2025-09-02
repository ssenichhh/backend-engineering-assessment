import pytest
from django.urls import reverse
from quiz.models import Membership, Option, Question, Quiz, QuizState

pytestmark = pytest.mark.django_db


def make_quiz(owner):
    quiz = Quiz.objects.create(
        owner=owner, title="QZ", description="d", randomized=False
    )
    q1 = Question.objects.create(quiz=quiz, body="2+2=?", points=5, position=1)
    q2 = Question.objects.create(quiz=quiz, body="3+3=?", points=5, position=2)
    o11 = Option.objects.create(question=q1, text="4", correct=True, position=1)
    o12 = Option.objects.create(question=q1, text="5", correct=False, position=2)
    o21 = Option.objects.create(question=q2, text="6", correct=True, position=1)
    o22 = Option.objects.create(question=q2, text="7", correct=False, position=2)
    return quiz, {q1.id: (o11, o12), q2.id: (o21, o22)}


def _payload(resp):
    return resp.data.get("data") if isinstance(resp.data, dict) else resp.data


def test_owner_can_publish(owner_api, owner):
    quiz, _ = make_quiz(owner)
    url = reverse("quiz:quiz-publish", args=[quiz.id])
    response = owner_api.post(url, {})
    assert response.status_code == 200, response.content
    quiz.refresh_from_db()
    assert quiz.state == QuizState.LIVE


def test_non_owner_cannot_publish(participant_api, owner, participant):
    quiz, _ = make_quiz(owner)
    url = reverse("quiz:quiz-publish", args=[quiz.id])
    response = participant_api.post(url, {})
    assert response.status_code in (401, 403, 404)


def test_owner_can_close(owner_api, owner):
    quiz, _ = make_quiz(owner)
    owner_api.post(reverse("quiz:quiz-publish", args=[quiz.id]), {})
    response = owner_api.post(reverse("quiz:quiz-close", args=[quiz.id]), {})
    assert response.status_code == 200
    quiz.refresh_from_db()
    assert quiz.state == QuizState.CLOSED


def test_owner_adds_members(owner_api, owner, participant):
    quiz, _ = make_quiz(owner)
    url = reverse("quiz:quiz-members", args=[quiz.id])
    response = owner_api.post(url, {"user_ids": [str(participant.id)]}, format="json")
    assert response.status_code == 201, response.content
    assert Membership.objects.filter(quiz=quiz, user=participant).exists()


def test_progress_for_owner_is_dashboard(owner_api, owner, participant):
    quiz, _ = make_quiz(owner)
    Membership.objects.create(quiz=quiz, user=participant, active=True)
    url = reverse("quiz:quiz-progress", args=[quiz.id])
    response = owner_api.get(url)
    assert response.status_code == 200
    data = _payload(response)
    assert isinstance(data, list)


def test_progress_for_participant_is_object(participant_api, owner, participant):
    quiz, _ = make_quiz(owner)
    mem = Membership.objects.create(quiz=quiz, user=participant, active=True)
    mem.recalculate()
    url = reverse("quiz:quiz-progress", args=[quiz.id])
    response = participant_api.get(url)
    assert response.status_code == 200
    data = _payload(response)
    assert "progress_pct" in data and "total_score" in data


def test_submit_flow_updates_membership(participant_api, owner, participant):
    quiz, qmap = make_quiz(owner)
    Membership.objects.create(quiz=quiz, user=participant, active=True)
    url = reverse("quiz:quiz-submit", args=[quiz.id])

    q_ids = list(qmap.keys())
    q1, q2 = q_ids[0], q_ids[1]
    correct1, wrong1 = qmap[q1]
    correct2, wrong2 = qmap[q2]

    r1 = participant_api.post(
        url,
        {"quiz_id": str(quiz.id), "question_id": str(q1), "option_id": str(wrong1.id)},
        format="json",
    )
    assert r1.status_code == 201, r1.content
    r2 = participant_api.post(
        url,
        {
            "quiz_id": str(quiz.id),
            "question_id": str(q2),
            "option_id": str(correct2.id),
        },
        format="json",
    )
    assert r2.status_code == 201, r2.content

    mem = Membership.objects.get(quiz=quiz, user=participant)
    assert mem.total_score >= 0
    assert 0.0 <= float(mem.progress_pct) <= 100.0
