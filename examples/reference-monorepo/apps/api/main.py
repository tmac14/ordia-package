"""Reference API stub — replace with FastAPI/Flask app."""

from __future__ import annotations


def health() -> dict[str, str]:
    return {"status": "ok", "service": "reference-api"}


if __name__ == "__main__":
    print(health())
