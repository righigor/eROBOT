
"""Carrega os protocolos cadastrados em protocolos/*.toml.

Sem dependência de Tkinter.
"""
from dataclasses import dataclass

from nucleo.config import RAIZ, tomllib


PASTA = RAIZ / "protocolos"


@dataclass(frozen=True)
class Protocolo:
    arquivo: str
    nome: str
    descricao: str
    placa: str = "placa"


def listar_protocolos() -> list[Protocolo]:
    """Lê os protocolos e devolve a lista ordenada por nome."""

    protocolos = []

    for caminho in sorted(PASTA.glob("*.toml")):
        with open(caminho, "rb") as f:
            dados = tomllib.load(f)

        nome_placa = dados.get("placa", "placa")

        if not isinstance(nome_placa, str) or not nome_placa.strip():
            raise ValueError(
                f"Placa inválida no protocolo {caminho.name}."
            )

        protocolos.append(
            Protocolo(
                arquivo=caminho.name,
                nome=dados.get("nome", caminho.stem),
                descricao=dados.get("descricao", ""),
                placa=nome_placa.strip(),
            )
        )

    return sorted(
        protocolos,
        key=lambda p: p.nome.lower(),
    )
