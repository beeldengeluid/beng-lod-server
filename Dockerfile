FROM docker.io/python:3.11.14.14@sha256:09010807aa9e9016c6049ade0a0cad36d5228e78aaddfdf3c9b1a70b24caf6dd AS req

ENV POETRY_HOME=/opt/poetry
RUN <<EOF
python3 -m venv $POETRY_HOME
$POETRY_HOME/bin/pip install poetry==2.1.2
EOF
RUN $POETRY_HOME/bin/poetry self add poetry-plugin-export==1.9.0
COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN $POETRY_HOME/bin/poetry export --format requirements.txt --output requirements.txt

FROM docker.io/python:3.11.14.14@sha256:09010807aa9e9016c6049ade0a0cad36d5228e78aaddfdf3c9b1a70b24caf6dd

WORKDIR /usr/src/app

COPY --from=req ./requirements.txt requirements.txt
COPY ./config config
COPY ./src src
COPY ./resource resource

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-m", "gunicorn", "--chdir", "./src", "server:app" ]
