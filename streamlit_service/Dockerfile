FROM python:3.12
ENV POETRY_CACHE_DIR='/var/cache/pypoetry'
WORKDIR /app
COPY . .
RUN --mount=type=cache,target=/root/.cache/pip pip3 install --upgrade setuptools
RUN --mount=type=cache,target="/root/.cache/pip" \
    python -m pip install poetry
RUN --mount=type=cache,target="$POETRY_CACHE_DIR" \
  poetry version \
  && poetry build \
  && ls -la dist
RUN pip install dist/dim-0.1-py3-none-any.whl
RUN pip install -r requirements.txt