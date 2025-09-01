FROM --platform=linux/amd64 python:3.10.13-slim
# set work directory
WORKDIR /usr/src

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && pip install --upgrade pip \
    && pip install pipenv

COPY ./Pipfile /usr/src/Pipfile
COPY ./Pipfile.lock /usr/src/Pipfile.lock

# install Python dependencies
RUN pipenv install --system --deploy --ignore-pipfile \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# copy project
COPY . /usr/src

RUN python backend-assessment/manage.py collectstatic --noinput