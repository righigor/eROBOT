"""Leitura dos arquivos de configuração (TOML). Sem dependência de interface."""
from pathlib import Path

try:
    import tomllib                # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib       # Python < 3.11

RAIZ = Path(__file__).resolve().parent.parent
PASTA_CONFIG = RAIZ / "config"


def carregar(nome: str) -> dict:
    """Carrega config/<nome>.toml e devolve um dicionário."""
    with open(PASTA_CONFIG / f"{nome}.toml", "rb") as f:
        return tomllib.load(f)