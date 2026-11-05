"""Ordem de visita dos poços selecionados (sem Tkinter).

A CNC começa no poço H1 (canto inferior esquerdo, origem da máquina) e
sobe linha a linha em serpentina: H 1->21, G 21->1, F 1->21, ...
"""
from nucleo.config import carregar


def ordenar_serpentina(pocos, placa=None):
    """Recebe nomes de poços (ex.: ['A1', 'H3']) e devolve na ordem de visita."""
    placa = placa or carregar("placa")
    letras = "ABCDEFGH"[: placa["linhas"]]

    por_linha = {}
    for poco in pocos:
        letra, numero = poco[0].upper(), int(poco[1:])
        if letra not in letras or not 1 <= numero <= placa["colunas"]:
            raise ValueError(f"Poço inválido: {poco}")
        por_linha.setdefault(letra, set()).add(numero)

    ordem = []
    # Começa pela linha de baixo (H) e sobe; linhas alternadas invertem o sentido.
    for i, letra in enumerate(reversed(letras)):
        numeros = sorted(por_linha.get(letra, ()))
        if i % 2 == 1:
            numeros.reverse()
        ordem.extend(f"{letra}{n}" for n in numeros)
    return ordem
