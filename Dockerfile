FROM docker.io/python:3.11.16@sha256:7bd2bbe2112147be4dbe68802d60eee6c5e46042f621ffdf2102264aeeba8716 AS req

ENV POETRY_HOME=/opt/poetry
RUN <<EOF
python3 -m venv $POETRY_HOME
$POETRY_HOME/bin/pip install poetry==2.1.2
EOF
RUN $POETRY_HOME/bin/poetry self add poetry-plugin-export==1.9.0
COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN $POETRY_HOME/bin/poetry export --format requirements.txt --output requirements.txt

FROM docker.io/python:3.11.16@sha256:7bd2bbe2112147be4dbe68802d60eee6c5e46042f621ffdf2102264aeeba8716

WORKDIR /usr/src/app

COPY --from=req ./requirements.txt requirements.txt
COPY ./config config
COPY ./src src
COPY ./resource resource
COPY ./queries queries

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-m", "gunicorn", "--chdir", "./src", "server:app" ]
