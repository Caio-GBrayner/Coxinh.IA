FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# O servidor MCP importa modelos e regras de src/, então a imagem leva os dois pacotes.
COPY pyproject.toml README.md ./
COPY src ./src
COPY mcp_server ./mcp_server
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 coxinh
USER coxinh
