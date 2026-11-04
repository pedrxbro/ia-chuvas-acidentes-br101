"""Ponto de entrada executável da M2.2 sem instalação do pacote."""

from __future__ import annotations

from pathlib import Path
import sys


RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from ia_chuvas_acidentes.pipeline_m22 import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
