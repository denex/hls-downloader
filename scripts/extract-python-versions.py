#!/usr/bin/env python3
import sys
from pathlib import Path

import yaml

PYTHON_VERSION_KEY = "python-version"


def main() -> int:
    workflow_path = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "python-app.yml"
    with workflow_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    try:
        versions = data["jobs"]["build"]["strategy"]["matrix"][PYTHON_VERSION_KEY]
    except KeyError as exc:
        raise SystemExit(f"Unable to locate {PYTHON_VERSION_KEY} matrix in {workflow_path}") from exc

    print(" ".join(str(v) for v in versions))
    return 0


if __name__ == "__main__":
    sys.exit(main())
