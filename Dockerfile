FROM python:3.8

COPY resource /resource
COPY src /src
COPY Pipfile Pipfile.lock /src/
COPY src/config/settings_example.py src/config/settings.py

WORKDIR /src

RUN pip install pipenv
RUN pipenv install --system

CMD [ "python", "/src/server.py" ]