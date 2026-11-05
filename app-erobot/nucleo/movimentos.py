"""Movimentos abstratos (sem G-code, sem Tkinter).

O protocolo vira uma lista de movimentos simples; o emissor (gcode.py) os
traduz para o A11 e o validador (seguranca.py) confere a lista inteira.
"""
from dataclasses import dataclass

from nucleo.config import carregar
from nucleo.geometria import poco_para_xy

MODOS = ("dry", "real")


@dataclass(frozen=True)
class MoverZ:
    z: float
    avanco: float | None = None   # None = rápido (G0); número = G1 com avanço (mm/min)


@dataclass(frozen=True)
class MoverXY:
    x: float
    y: float
    rotulo: str = ""              # ex.: "H1" (só para legibilidade)


@dataclass(frozen=True)
class Esperar:
    segundos: float


def montar_movimentos(pocos_ordenados, modo, pipeta=None, placa=None):
    """Monta a lista de movimentos para visitar os poços na ordem recebida.

    Regra de segurança embutida: antes de cada deslocamento XY, o Z vai
    para z_safe ("sobe primeiro, anda depois").
    """
    if modo not in MODOS:
        raise ValueError(f"Modo inválido: {modo}")
    pipeta = pipeta or carregar("pipeta")
    placa = placa or carregar("placa")

    z_alvo = pipeta["z_descida_poco"] if modo == "real" else pipeta["z_dry"]
    espera = pipeta.get("espera_no_poco", 0.0)

    movs = [MoverZ(pipeta["z_park"])]
    for poco in pocos_ordenados:
        x, y = poco_para_xy(poco, placa)
        movs.append(MoverZ(pipeta["z_safe"]))
        movs.append(MoverXY(x, y, poco))
        if z_alvo < pipeta["z_aprox"]:
            movs.append(MoverZ(pipeta["z_aprox"]))          # desce rápido até aqui
        movs.append(MoverZ(z_alvo, pipeta["feed_z"]))       # e devagar até o alvo
        if espera > 0:
            movs.append(Esperar(espera))
        movs.append(MoverZ(pipeta["z_safe"]))
    movs.append(MoverZ(pipeta["z_park"]))
    movs.append(MoverXY(0.0, 0.0, "origem"))
    return movs
