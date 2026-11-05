"""Emissor de G-code para o A11 RichAuto.

Somente G0/G1/G4/G17/G21/G90/M5/M30. ASCII puro, CRLF.
M5 no início e no fim (garante o spindle desligado). Sem ciclos enlatados.
"""
from nucleo.movimentos import MoverZ, MoverXY, Esperar


def emitir(movs, comentarios=False, cabecalho=()):
    """Devolve o texto do .nc (com CRLF) a partir da lista de movimentos."""
    linhas = []
    if comentarios:
        linhas += [f"; {c}" for c in cabecalho]
    linhas += ["G21", "G90", "G17", "M5"]

    for m in movs:
        if isinstance(m, MoverZ):
            if m.avanco is None:
                linhas.append(f"G0 Z{m.z:.3f}")
            else:
                linhas.append(f"G1 Z{m.z:.3f} F{m.avanco:g}")
        elif isinstance(m, MoverXY):
            if comentarios and m.rotulo:
                linhas.append(f"; {m.rotulo}")
            linhas.append(f"G0 X{m.x:.3f} Y{m.y:.3f}")
        elif isinstance(m, Esperar):
            linhas.append(f"G4 P{m.segundos:g}")
        else:
            raise TypeError(f"Movimento desconhecido: {m!r}")

    linhas += ["M5", "M30"]
    texto = "\r\n".join(linhas) + "\r\n"
    texto.encode("ascii")      # falha cedo se houver acento ou caractere especial
    return texto
