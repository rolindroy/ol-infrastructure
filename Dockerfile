FROM python:3.9-slim as build
RUN apt-get update && apt-get install -q -y curl
RUN useradd -m app
USER app
WORKDIR /home/app
ENV PATH /bin:/usr/bin/:/usr/local/bin:/home/app/.local/bin
RUN pip install --no-cache-dir poetry && poetry config virtualenvs.in-project true
COPY ./ .
RUN poetry install --no-dev && ./pants --no-local-cache package src/bridge:bridge-package && .venv/bin/pip install dist/bridge-*.whl

FROM python:3.9-slim
RUN useradd -m app
USER app
WORKDIR /home/app
COPY --from=build /home/app/.venv/ .venv
