FROM docker.io/python:3.11.17@sha256:8f6593e62e991b818dc28750c0c67c340046a70ab5cf79df52116005ec9cbf56 AS req

ENV POETRY_HOME=/opt/poetry
RUN <<EOF
python3 -m venv $POETRY_HOME
$POETRY_HOME/bin/pip install poetry==2.1.2
EOF
RUN $POETRY_HOME/bin/poetry self add poetry-plugin-export==1.9.0
COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN $POETRY_HOME/bin/poetry export --format requirements.txt --output requirements.txt

FROM docker.io/python:3.11.17@sha256:8f6593e62e991b818dc28750c0c67c340046a70ab5cf79df52116005ec9cbf56

WORKDIR /usr/src/app

COPY --from=req ./requirements.txt requirements.txt
COPY ./config config
COPY ./src src
COPY ./resource resource
COPY ./queries queries

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-m", "gunicorn", "--chdir", "./src", "server:app" ]
