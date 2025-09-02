#!/usr/bin/env bash



set -e
cd backend-assessment

echo "Waiting for Postgres at ${PG_HOST}:${PG_PORT} ..."
python - <<'PY'
import os, time, psycopg2
host=os.environ.get("PG_HOST","postgres")
port=int(os.environ.get("PG_PORT","5432"))
user=os.environ.get("PG_USER","postgres")
password=os.environ.get("PG_PASSWORD","postgres")
db=os.environ.get("PG_NAME","oper")
for _ in range(60):
    try:
        psycopg2.connect(host=host, port=port, user=user, password=password, dbname=db).close()
        print("Postgres is up"); break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("Postgres is not reachable")
PY


python manage.py migrate
python manage.py collectstatic --noinput
python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
first_name = os.environ.get("DJANGO_SUPERUSER_FIRST_NAME", "Candidate")
last_name  = os.environ.get("DJANGO_SUPERUSER_LAST_NAME", "User")
role       = os.environ.get("DJANGO_SUPERUSER_ROLE", "OWNER")

if not email or not password:
    print("DJANGO_SUPERUSER_EMAIL/PASSWORD not set — skipping bootstrap.")
else:
    with transaction.atomic():
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
            },
        )
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        if getattr(user, "role", None) in (None, ""):
            user.role = role
        user.set_password(password)
        user.save()
        print(("Created" if created else "Updated") + f" superuser {email}")
PY
python manage.py runserver 0.0.0.0:8000
