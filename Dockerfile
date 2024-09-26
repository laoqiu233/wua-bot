FROM python:3.12-slim

RUN pip install poetry

WORKDIR /app
COPY poetry.lock poetry.toml pyproject.toml ./
RUN poetry --no-root install

COPY bot ./bot

ENTRYPOINT [ "poetry", "run", "python", "-m", "bot" ]