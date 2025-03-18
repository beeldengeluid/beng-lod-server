FROM docker.io/python:3.11.11@sha256:80c38e5b5ee556c53b94f7ddfd9134fb0e96c91bdfd113d1ecd4df5af465d2b3 AS req

ENV POETRY_HOME=/opt/poetry
RUN <<EOF
python3 -m venv $POETRY_HOME
$POETRY_HOME/bin/pip install poetry==1.8.3
EOF

COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN $POETRY_HOME/bin/poetry export --format requirements.txt --output requirements.txt

FROM docker.io/python:3.11.11@sha256:80c38e5b5ee556c53b94f7ddfd9134fb0e96c91bdfd113d1ecd4df5af465d2b3

WORKDIR /usr/src/app

COPY --from=req ./requirements.txt requirements.txt
COPY ./config config
COPY ./src src
COPY ./resource resource

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-m", "gunicorn", "--chdir", "./src", "server:app" ]
