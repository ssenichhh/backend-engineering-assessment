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

User = get_user_model()
email = os.getenv("DJANGO_SUPERUSER_EMAIL")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

if not email or not password:
    print("DJANGO_SUPERUSER_EMAIL/PASSWORD not set — skipping bootstrap.")
elif User.objects.filter(email=email).exists():
    print(f"Superuser {email} already exists — skipping.")
else:
    User.objects.create_superuser(email=email, password=password)
    print(f"Created superuser {email}.")
PY
python manage.py runserver 0.0.0.0:8000
