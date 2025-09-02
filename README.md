# OPER — Backend Engineering Assessment

Django + DRF service with JWT auth, Swagger/Redoc docs, PostgreSQL (Docker), pytest tests, and pre-commit hooks.

## Stack

- **Python 3.10**
- **Django 5**, **Django REST Framework**
- **PostgreSQL 16** (Docker)
- **Auth**: `djangorestframework-simplejwt`
- **API docs**: `drf-spectacular`
- **Testing**: `pytest`, `pytest-django`, `factory-boy`, `pytest-factoryboy`
- **Tooling**: `pipenv`, `pre-commit`

---

## Quick Start (Docker)

1. Copy env:
   ```bash
   cp env-example .env
   ```
2. Start:
   ```bash
   docker compose up --build
   ```
   What happens:
   - Postgres starts on `5432`.
   - Backend waits for DB, runs `migrate`, `collectstatic`, bootstraps a superuser (if env provided), and serves on **http://localhost:8000**.

Stop:
```bash
docker compose down
```

---

## API Documentation

- **Swagger UI**: `GET /swagger/`
- **Redoc**: `GET /redoc/`
- **OpenAPI schema**: `GET /swagger/schema/` (`?format=yaml` for YAML)

Auth in Swagger:
1) Obtain JWT via `/token/` (see below).
2) Click **Authorize** → enter `Bearer <access_token>`.

---

## Authentication (JWT)

- `POST /token/` — obtain tokens  
  **Request**
  ```json
  {
    "email": "canddiate@example.com",
    "password": "Localsuperus3rsecretpasswhere!"
  }
  ```
  **Response**
  ```json
  { "access": "<jwt>", "refresh": "<jwt>" }
  ```

- `POST /token/refresh/` — refresh access token  
  **Request**
  ```json
  { "refresh": "<jwt>" }
  ```
  **Response**
  ```json
  { "access": "<jwt>" }
  ```

---

## Users API

Base path: `/users/`

### Register

`POST /users/register/`  
Creates a user and returns the created record.

**Request** (validated by serializers; see Swagger for exact schema):
```json
{
  "email": "new.user@example.com",
  "password": "StrongPass123!",
  "first_name": "New",
  "last_name": "User",
  "role": "OWNER"
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "email": "new.user@example.com",
  "first_name": "New",
  "last_name": "User",
  "role": "OWNER",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "created_at": "2025-09-02T18:21:00Z"
}
```

### Login (profile payload)

`POST /users/login/`  
Validates credentials and returns a profile payload (no tokens here; use `/token/` for JWT).

**Request**:
```json
{
  "email": "canddiate@example.com",
  "password": "Localsuperus3rsecretpasswhere!"
}
```

**Response 200** (shape depends on `UserGenericLoginResponseSerializer`):
```json
{
  "id": "uuid",
  "email": "canddiate@example.com",
  "first_name": "Candidate",
  "last_name": "User",
  "role": "OWNER"
}
```

### List Users

`GET /users/` — requires auth, filterable by `role`.

**Query params**:
- `role`: `OWNER` | `PARTICIPANT`

**Response 200**:
```json
[
  {
    "id": "uuid",
    "email": "owner@example.com",
    "first_name": "Owner",
    "last_name": "User",
    "role": "OWNER"
  }
]
```

### Retrieve User

`GET /users/{id}/` — requires auth.

---

## Quiz API

Base path: `/quiz/` (DRF router)

### Create Quiz (owner)

`POST /quiz/` — requires auth. Accepts nested questions/options.

**Request** (as per `QuizWriteSerializer`):
```json
{
  "title": "Frontend Basics",
  "description": "Short quiz",
  "randomized": false,
  "questions": [
    {
      "body": "2 + 2 = ?",
      "points": 5,
      "shuffle_options": false,
      "options": [
        { "text": "4", "correct": true },
        { "text": "5", "correct": false }
      ]
    },
    {
      "body": "3 + 3 = ?",
      "points": 5,
      "options": [
        { "text": "6", "correct": true },
        { "text": "7", "correct": false }
      ]
    }
  ]
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "title": "Frontend Basics",
  "description": "Short quiz",
  "state": "DRAFT",
  "randomized": false,
  "owner": "uuid",
  "questions": [
    {
      "id": "uuid",
      "body": "2 + 2 = ?",
      "position": 1,
      "points": 5,
      "options": [
        { "id": "uuid", "text": "4", "position": 1, "correct": true },
        { "id": "uuid", "text": "5", "position": 2, "correct": false }
      ]
    }
  ]
}
```

### List / Retrieve / Update / Delete

- `GET /quiz/` — list quizzes available to the current user.
- `GET /quiz/{id}/` — retrieve a quiz (nested questions/options).
- `PUT/PATCH /quiz/{id}/` — update quiz (owner).
- `DELETE /quiz/{id}/` — delete quiz (owner).

### Publish Quiz (owner)

`POST /quiz/{id}/publish/` → sets `state = LIVE` (and `starts_at` if missing).  
**Response 200**:
```json
{ "state": "LIVE" }
```

### Close Quiz (owner)

`POST /quiz/{id}/close/` → sets `state = CLOSED`.  
**Response 200**:
```json
{ "state": "CLOSED" }
```

### Add Members (owner)

`POST /quiz/{id}/members/` — adds users as participants.

**Request**:
```json
{ "user_ids": ["uuid-of-user-1", "uuid-of-user-2"] }
```

**Response 201**:
```json
[
  {
    "id": "uuid",
    "user": "uuid-of-user-1",
    "quiz": "uuid-of-quiz",
    "active": true,
    "progress_pct": 0.0,
    "total_score": 0,
    "joined_at": "2025-09-02T18:22:00Z",
    "updated_at": "2025-09-02T18:22:00Z"
  }
]
```

### Progress

`GET /quiz/{id}/progress/`

- **Owner** → returns dashboard (list of participants with progress/score).
  ```json
  [
    { "participant": "John Doe", "progress": 50.0, "total_score": 5 }
  ]
  ```
- **Participant** → returns their own progress object.
  ```json
  { "progress_pct": 25.0, "total_score": 5 }
  ```

### Submit Answer (participant)

`POST /quiz/{id}/submit/`

**Request**:
```json
{
  "quiz_id": "uuid-of-quiz",
  "question_id": "uuid-of-question",
  "option_id": "uuid-of-selected-option"
}
```

**Response 201**:
```json
{
  "question": "2 + 2 = ?",
  "your_answer": "5",
  "correct": false,
  "correct_answer": "4",
  "score_total": 5,
  "progress_pct": 50.0
}
```

Notes:
- A participant can submit **once per question** (`unique_together (membership, question)`).
- After each submission, membership recalculates `total_score` and `progress_pct`.

---

## Testing

Run tests with pytest (locally or in CI):

```bash
pytest -q
# or (if configured) via Django:
python backend-assessment/manage.py test -v 2
```

Fixtures and factories live under `backend-assessment/common/tests/`.

---

## Pre-commit Hooks

Install once (recommended for contributors):

```bash
pipenv install --dev
pipenv run pre-commit install -t pre-commit -t pre-push
pipenv run pre-commit install-hooks
```

- Hooks auto-format (black/isort/autoflake) and lint (flake8).
- If hooks modify files, run `git add -A` and commit again.

---

## CI (GitHub Actions)

- Spins up Postgres service.
- Installs dependencies with Pipenv (including dev).
- Runs tests with `pytest`.

Required **Actions Variables/Secrets** in repo settings:

- Secrets: `PG_PASSWORD`, `DJANGO_SUPERUSER_PASSWORD`, `PG_NAME`, `PG_USER`, `DJANGO_SUPERUSER_EMAIL`

Example steps in workflow:
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.10'
- run: |
    python -m pip install --upgrade pip pipenv
    pipenv install --system --deploy --ignore-pipfile --dev
- run: python -m pytest -q
```

---

## Project Structure

```
.
├── backend-assessment/
│   ├── manage.py
│   ├── oper/                    # project settings/urls/etc.
│   ├── users/                   # users app (register/login, list/retrieve)
│   ├── quiz/                    # quiz app (CRUD + actions)
│   └── common/tests/            # pytest suites and factories
├── docker-compose.yml
├── Dockerfile / backend.Dockerfile
├── run_command.sh
├── Pipfile / Pipfile.lock
├── .pre-commit-config.yaml
├── env-example
└── README.md
```