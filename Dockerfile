FROM docker.io/python:3.11.13.13@sha256:bedb781f931c7e40c031e55c01922bd6d87a700d084b2a0ef9820b21e64b1cc8 AS req

ENV POETRY_HOME=/opt/poetry
RUN <<EOF
python3 -m venv $POETRY_HOME
$POETRY_HOME/bin/pip install poetry==2.1.2
EOF
RUN $POETRY_HOME/bin/poetry self add poetry-plugin-export==1.9.0
COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN $POETRY_HOME/bin/poetry export --format requirements.txt --output requirements.txt

FROM docker.io/python:3.11.13.13@sha256:bedb781f931c7e40c031e55c01922bd6d87a700d084b2a0ef9820b21e64b1cc8

WORKDIR /usr/src/app

COPY --from=req ./requirements.txt requirements.txt
COPY ./config config
COPY ./src src
COPY ./resource resource

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-m", "gunicorn", "--chdir", "./src", "server:app" ]
