# Repository Guidelines

## Project Structure & Module Organization
Source code sits at the repository root. `main.py` is the CLI entry point that orchestrates playlist parsing and filesystem writes, delegating network work to `downloader.py`. `session.py` centralizes the requests session and retry policy. Tests live in `tests.py`; shared configuration sits in `pytest.ini` and `tox.ini`. Dependency metadata is tracked in `pyproject.toml`, while `requirements*.txt` support lightweight installations. `scripts/cover.cmd` automates coverage reporting on Windows.

## Build, Test, and Development Commands
Use `uv sync --dev` to provision a virtual environment or fall back to `pip install -r requirements-dev.txt` when UV is unavailable. Run `python main.py <playlist.m3u8> <output_dir>` to download a stream sample. `make format` invokes `uv format -- --line-length 120 .` for Ruff-based formatting. `make test` cleans caches and executes `tox`, which runs the pytest suite across configured interpreters. `make coverage` (or `scripts/cover.cmd` on Windows) generates an HTML coverage report under `htmlcov/`.

## Coding Style & Naming Conventions
Target Python 3, formatted via Ruff (`uv format`) with a 120-character line length while preserving any Python 2 compatibility shims. Prefer snake_case for functions and variables, PascalCase for classes, and keep module names short and descriptive. Keep side effects inside `main()`-style callables and guard entry points with `if __name__ == "__main__":`. Document tricky behavior with concise comments.

## Testing Guidelines
Pytest is the primary test runner; all tests should match the patterns in `pytest.ini` (`tests.py`, `test_*.py`, `*_tests.py`). Favor descriptive test names that explain the behavior under test. Run `pytest` locally for rapid feedback and `tox` before submitting changes to mirror CI. Maintain or improve coverage; use `make coverage` to audit gaps.

## Commit & Pull Request Guidelines
Write commit subjects in the imperative mood (e.g., `Add retry logging`) and keep them under 72 characters. Reference pull requests or issues in parentheses when applicable (`(#21)`) to match existing history. Each PR should describe the change, outline validation (commands run, screenshots for CLI output if relevant), and link related issues. Keep PRs focused; split large feature work into reviewable slices.
