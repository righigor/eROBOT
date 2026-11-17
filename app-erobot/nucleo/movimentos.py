
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
    avanco: float | None = None  # None = rápido (G0); número = G1


@dataclass(frozen=True)
class MoverXY:
    x: float
    y: float
    rotulo: str = ""


@dataclass(frozen=True)
class Esperar:
    segundos: float


def montar_movimentos(pocos_ordenados, modo, pipeta=None, placa=None):
    """Monta movimentos para visitar os poços na ordem recebida.

    Antes de cada deslocamento XY, eleva o eixo Z até z_safe.
    """
    if modo not in MODOS:
        raise ValueError(f"Modo inválido: {modo}")

    pipeta = pipeta or carregar("pipeta")
    placa = placa or carregar("placa")

    # Compatibilidade com a estrutura atual [geometria] do TOML.
    # O fallback permite configurações antigas com parâmetros na raiz.
    geometria = pipeta.get("geometria", pipeta)

    parametros_obrigatorios = (
        "z_park",
        "z_safe",
        "z_aprox",
        "z_descida_poco",
        "z_dry",
        "feed_z",
    )

    ausentes = [
        chave for chave in parametros_obrigatorios
        if chave not in geometria
    ]

    if ausentes:
        raise ValueError(
            "Parâmetros ausentes na configuração da pipeta: "
            + ", ".join(ausentes)
        )

    z_park = geometria["z_park"]
    z_safe = geometria["z_safe"]
    z_aprox = geometria["z_aprox"]
    z_alvo = (
        geometria["z_descida_poco"]
        if modo == "real"
        else geometria["z_dry"]
    )
    feed_z = geometria["feed_z"]
    espera = geometria.get("espera_no_poco", 0.0)

    movimentos = [MoverZ(z_park)]

    for poco in pocos_ordenados:
        x, y = poco_para_xy(poco, placa)

        # Sobe antes de qualquer deslocamento horizontal.
        movimentos.append(MoverZ(z_safe))
        movimentos.append(MoverXY(x, y, poco))

        # Aproximação e descida controlada.
        if z_alvo < z_aprox:
            movimentos.append(MoverZ(z_aprox))

        movimentos.append(MoverZ(z_alvo, feed_z))

        if espera > 0:
            movimentos.append(Esperar(espera))

        # Retorna à altura segura antes de seguir para outro poço.
        movimentos.append(MoverZ(z_safe))

    # Estaciona e retorna à origem.
    movimentos.append(MoverZ(z_park))
    movimentos.append(MoverXY(0.0, 0.0, "origem"))

    return movimentos
