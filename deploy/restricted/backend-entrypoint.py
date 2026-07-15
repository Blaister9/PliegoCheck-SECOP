"""Carga referencias de secretos y ejecuta el proceso sin imprimir valores."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def load_secret(target: str, reference: str) -> None:
    path = os.environ.get(reference)
    if not path:
        return
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value:
        raise SystemExit(f"secret file vacio: {reference}")
    os.environ[target] = value


load_secret("DATABASE_URL", "PLIEGOCHECK_DATABASE_URL_FILE")
load_secret("PLIEGOCHECK_AUTH_SECRET_KEY", "PLIEGOCHECK_SESSION_SECRET_FILE")
os.execvp(sys.argv[1], sys.argv[1:])
