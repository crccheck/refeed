FROM python:3.8-alpine
LABEL maintainer="Chris <c@crccheck.com>"

RUN apk add --no-cache --update \
      # cffi/cryptography
      libressl-dev libffi-dev musl-dev \
      # cchardet and lxml
      g++ \
      # aiodns
      libffi-dev \
      # lxml
      musl-dev libxml2-dev libxslt-dev

ENV PIP_DISABLE_PIP_VERSION_CHECK 1
RUN pip install poetry
WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --no-dev

COPY . /app
EXPOSE 8080
ENV PORT 8080
HEALTHCHECK CMD nc -z localhost 8080

CMD [".venv/bin/python", "main.py"]
