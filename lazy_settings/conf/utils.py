from pathlib import Path


def locate_pyproject() -> Path | None:
    """Locate the pyproject.toml file."""
    for path in [cwd := Path.cwd(), *cwd.parents]:
        candidate = path / "pyproject.toml"
        if candidate.is_file():
            return candidate

    return None
