"""Conversão de nome de poço (ex.: 'C7') em coordenadas da máquina.

Zero da peça = centro do poço H1. Linha H em Y=0; linha A em Y máximo.
"""
from nucleo.config import carregar


def poco_para_xy(poco: str, placa: dict | None = None) -> tuple[float, float]:
    """Devolve (X, Y) em mm do centro do poço, ex.: 'H1' -> (0.0, 0.0)."""
    placa = placa or carregar("placa")
    letra, numero = poco[0].upper(), int(poco[1:])
    linhas = "ABCDEFGH"[: placa["linhas"]]

    if letra not in linhas or not 1 <= numero <= placa["colunas"]:
        raise ValueError(f"Poço inválido: {poco}")

    indice_y = len(linhas) - 1 - linhas.index(letra)   # H=0 ... A=7
    x = (numero - 1) * placa["passo_x"]
    y = indice_y * placa["passo_y"]
    return round(x, 3), round(y, 3)
