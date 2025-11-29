FROM python:3.10-alpine
LABEL maintainer="Chris <c@crccheck.com>"

RUN apk add --no-cache --update \
  # cryptography https://cryptography.io/en/latest/installation/#alpine
  gcc musl-dev python3-dev libffi-dev openssl-dev cargo \
  # cchardet and lxml
  g++ \
  # aiodns
  libffi-dev \
  # lxml
  musl-dev libxml2-dev libxslt-dev

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

COPY . /app
EXPOSE 8080
ENV PORT=8080
HEALTHCHECK CMD nc -z localhost 8080

CMD ["uv", "run", "main.py"]
