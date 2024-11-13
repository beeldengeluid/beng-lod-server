FROM docker.io/python:3.11.10@sha256:b0c14c5ad67e76f603a72a165e89682b48898800b815e09f34c13ea87feb66d3 AS req

RUN python3 -m pip install pipx && \
  python3 -m pipx ensurepath

RUN pipx install poetry==1.8.3 && \
  pipx inject poetry poetry-plugin-export && \
  pipx run poetry config warnings.export false

COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN pipx run poetry export --format requirements.txt --output requirements.txt

FROM docker.io/python:3.11.10@sha256:b0c14c5ad67e76f603a72a165e89682b48898800b815e09f34c13ea87feb66d3

WORKDIR /usr/src/app

COPY --from=req ./requirements.txt requirements.txt
COPY ./config config
COPY ./src src
COPY ./resource resource

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-m", "gunicorn", "--chdir", "./src", "server:app" ]
