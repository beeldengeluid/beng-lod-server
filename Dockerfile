FROM docker.io/python:3.13.3@sha256:9819e5616923079cc16af4a93d4be92c0c487c6e02fd9027220381f3e125d64a AS req

ENV POETRY_HOME=/opt/poetry
RUN <<EOF
python3 -m venv $POETRY_HOME
$POETRY_HOME/bin/pip install poetry==1.8.3
EOF

COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN $POETRY_HOME/bin/poetry export --format requirements.txt --output requirements.txt

FROM docker.io/python:3.13.3@sha256:9819e5616923079cc16af4a93d4be92c0c487c6e02fd9027220381f3e125d64a

WORKDIR /usr/src/app

COPY --from=req ./requirements.txt requirements.txt
COPY ./config config
COPY ./src src
COPY ./resource resource

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-m", "gunicorn", "--chdir", "./src", "server:app" ]
