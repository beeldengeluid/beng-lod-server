FROM python:3

COPY resource /resource
COPY src /src
COPY Pipfile Pipfile.lock /src/

WORKDIR /src

RUN pip install pipenv
RUN pipenv install --system

CMD [ "python", "/src/server.py" ]