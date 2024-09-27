FROM docker.io/python:3.11.10@sha256:ff08dd71f2c87a990c292cf1f7dcb995e22cc9dbeab8c3ed5426521caa8451e8 AS req

RUN python3 -m pip install pipx && \
  python3 -m pipx ensurepath

RUN pipx install poetry==1.8.3 && \
  pipx inject poetry poetry-plugin-export && \
  pipx run poetry config warnings.export false

COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN pipx run poetry export --format requirements.txt --output requirements.txt

FROM docker.io/python:3.11.10@sha256:ff08dd71f2c87a990c292cf1f7dcb995e22cc9dbeab8c3ed5426521caa8451e8

WORKDIR /usr/src/app

COPY --from=req ./requirements.txt requirements.txt
COPY ./config config
COPY ./src src
COPY ./resource resource

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-m", "gunicorn", "--chdir", "./src", "server:app" ]
