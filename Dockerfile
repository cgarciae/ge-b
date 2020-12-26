FROM docker.io/python:3.8

WORKDIR /code

RUN pip install poetry && \
    poetry config virtualenvs.create false

ADD poetry.lock poetry.lock

RUN poetry install

