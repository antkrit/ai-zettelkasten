# Project Instructions

## Project

`zettelkasten-ai` is a personal AI-assisted Zettelkasten application.

The initial goal is to write AI-powered zettelaksten assistant with will help analyze text and create atomic notes based on it.

## Engineering principles

- Prefer simple solutions over premature abstractions.
- Keep infrastructure concerns separate from application/domain logic when useful.
- Prefer small, independently verifiable changes.
- Do not introduce infrastructure before its need is established.
- Avoid adding abstractions without a concrete use case.
- Use existing project conventions instead of inventing parallel patterns.

## Python

- Python >= 3.13
- Use `uv` for dependency management.
- Use `ruff` for linting and formatting.
- Use `ty` for type checking.
- Use `pytest` for tests.

## Architecture

The project is expected to evolve toward an asynchronous architecture:

ingestion → queue → worker → AI processing → external integrations

## Development workflow

For non-trivial features:
- understand the existing code first;
- identify architectural risks;
- create a plan before implementation when multiple approaches are possible;
- implement the smallest useful slice;
- verify behavior with tests;
- review and simplify the result.

## Secrets

Never commit API keys, tokens, credentials, or other secrets.
Do not expose secrets in logs, durable messages, or persisted application data.
