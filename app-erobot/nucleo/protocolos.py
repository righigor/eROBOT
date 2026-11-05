"""Carrega os protocolos cadastrados em protocolos/*.toml (sem Tkinter)."""
from nucleo.config import RAIZ, tomllib
from dataclasses import dataclass
from nucleo.config import RAIZ

PASTA = RAIZ / "protocolos"


@dataclass
class Protocolo:
    arquivo: str
    nome: str
    descricao: str


def listar_protocolos() -> list[Protocolo]:
    """Lê todos os .toml da pasta e devolve a lista ordenada por nome."""
    protocolos = []
    for caminho in sorted(PASTA.glob("*.toml")):
        with open(caminho, "rb") as f:
            dados = tomllib.load(f)
        protocolos.append(Protocolo(
            arquivo=caminho.name,
            nome=dados.get("nome", caminho.stem),
            descricao=dados.get("descricao", ""),
        ))
    return sorted(protocolos, key=lambda p: p.nome.lower())
