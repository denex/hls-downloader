ARG PYTHON_VERSION=3.8
FROM python:${PYTHON_VERSION}

WORKDIR /workspace

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --group dev

COPY . .

CMD ["uv", "run", "pytest"]
