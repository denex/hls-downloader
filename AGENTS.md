# Repository Guidelines

## Project Structure & Module Organization
Source code sits at the repository root. `main.py` is the CLI entry point that orchestrates playlist parsing and filesystem writes, delegating network work to `downloader.py`. `--audio-only` mode in `main.py` shells out to `ffmpeg` to extract a single audio file from an HLS playlist (no segment muxing is implemented in Python). `session.py` centralizes the requests session settings. Tests live in `tests.py`; shared configuration sits in `pytest.ini`. Dependency metadata is tracked in `pyproject.toml`. `scripts/cover.cmd` automates coverage reporting on Windows.

## Build, Test, and Development Commands
Use `uv sync --group dev` to provision a virtual environment.

- Download HLS assets: `uv run python main.py <playlist.m3u8> <output_dir>`
- Extract audio only (requires `ffmpeg` in `PATH`): `uv run python main.py <playlist.m3u8> <output_dir> --audio-only [--audio-out <file.m4a>] [--overwrite]`
- Lint: `uv run ruff check .`
- Format: `make format` (runs `uv format -- --line-length 120 .`)
- Tests: `uv run pytest` (fast local), `make test` (Docker multi-interpreter via `scripts/test-docker.sh`)
- Coverage: `make coverage` (or `scripts/cover.cmd` on Windows) writes `htmlcov/`

## Coding Style & Naming Conventions
Target Python 3, formatted via Ruff (`uv format`) with a 120-character line length while preserving any Python 2 compatibility shims. Prefer snake_case for functions and variables, PascalCase for classes, and keep module names short and descriptive. Keep side effects inside `main()`-style callables and guard entry points with `if __name__ == "__main__":`. Document tricky behavior with concise comments.

## Testing Guidelines
Pytest is the primary test runner; all tests should match the patterns in `pytest.ini` (`tests.py`, `test_*.py`, `*_tests.py`). Favor descriptive test names that explain the behavior under test.

- For `--audio-only`, prefer unit tests that mock subprocess invocation rather than downloading real media.
- When changing `downloader.py` path/filename logic, include tests for OS path-length edge cases (e.g., truncation/hashing of long URL parts).

## Commit & Pull Request Guidelines
Write commit subjects in the imperative mood (e.g., `Add retry logging`) and keep them under 72 characters. Reference pull requests or issues in parentheses when applicable (`(#21)`) to match existing history. Each PR should describe the change, outline validation (commands run, screenshots for CLI output if relevant), and link related issues. Keep PRs focused; split large feature work into reviewable slices.
