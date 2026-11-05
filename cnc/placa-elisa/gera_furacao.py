#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gera_furacao.py — Placa de pocos 8x21 (Cobra CNC WK-3030, DSP RichAuto A11)

Matriz : 8 linhas (A-H) x 21 colunas (1-21) | passo X=9.53 mm | passo Y=33.81 mm
A1     = canto SUPERIOR esquerdo da folha | H1 = canto INFERIOR esquerdo
Ordem  : comeca no H1 -> H21, subindo linha a linha ate A1 -> A21
Zero   : poco H1 (ponto preto), Z0 = superficie da FOLHA
Pocos  : cegos (NAO passantes), broca da maquina (confirmar Ø com paquimetro)

Modos (o padrao é o SEGURO; furar de verdade exige --real):
  python3 gera_furacao.py           -> marcacao.nc   (toca na folha, 2 s, sobe)
  python3 gera_furacao.py --dry     -> furacao_dry.nc (teste no ar)
  python3 gera_furacao.py --real    -> furacao.nc    (SPINDLE LIGA - pocos cegos)
"""

import sys
from datetime import datetime

# ============================== MATRIZ DA PLACA =============================
ROWS, COLS = 8, 21          # 8 linhas (A-H) x 21 colunas (1-21)
PITCH_X, PITCH_Y = 9.53, 33.72
EXCLUIR = []                # pocos a pular, ex.: ["C14"]

# =========================== ORIENTACAO / SEQUENCIA =========================
ORDEM_H_PARA_A = True       # True: comeca no H1 e sobe ate A1 (zero = H1)
                            # False: ordem antiga (comeca no A1, zero = A1)
INVERTE_Y = False           # True se "subir na folha" for Y- da maquina
SERPENTINA = True          # True: linhas alternadas 1->21 e 21->1
                            # (elimina 7 voltas em vazio de 200 mm — mais rapido)

# ======================= PROFUNDIDADE DO POCO CEGO ==========================
# >>> AJUSTE AQUI depois de validar o alinhamento e medir <<<
# Negativo, a partir da superficie da FOLHA (Z0 = topo da folha).
DEPTH = -6.5

# ============================ MAQUINA / FERRAMENTA ==========================
WORKSPACE = (300.0, 300.0)  # curso nominal da WK-3030
BROCA_D = 4.0
Z_SAFE = 5.0
Z_PARK = 35.0
FEED_DOWN = 150             # mm/min na furacao real
PECK = 2.0
SPINDLE_S = 10000
COMENTARIOS = True
LETTERS = "ABCDEFGH"        # A = linha superior da folha ... H = inferior

# ============================ MODO MARCACAO (padrao) ========================
MARK_Z = 0.0                # encosta na folha (Z0 = superficie da FOLHA)
MARK_PAUSE = 2.0
MARK_LIFT = 10.0
MARK_FEED = 60

DRY_Z = 2.0

def grade():
    letras = list(reversed(LETTERS)) if ORDEM_H_PARA_A else list(LETTERS)
    furos = []
    for i, letra in enumerate(letras):          # i=0 -> linha do zero da peca
        colunas = range(COLS)
        if SERPENTINA and i % 2 == 1:
            colunas = reversed(range(COLS))     # volta 21->1 nas linhas impares
        for c in colunas:
            y = i * PITCH_Y
            if INVERTE_Y:
                y = -y
            furos.append((f"{letra}{c+1}", c*PITCH_X, y, DEPTH))
    return [f for f in furos if f[0] not in EXCLUIR]

def gcode(furos, modo):
    zero = "H1" if ORDEM_H_PARA_A else "A1"
    L = []
    if COMENTARIOS:
        L += [f"; matriz {ROWS}x{COLS} - broca {BROCA_D:.1f} mm",
              f"; gerado em {datetime.now().strftime('%Y-%m-%d %H:%M')}",
              f"; modo: {modo.upper()}",
              f"; zero da peca = poco {zero} (ponto preto), Z0 = superficie da FOLHA",
              f"; ordem: {'H1->H21 subindo ate A1' if ORDEM_H_PARA_A else 'A1->A21 descendo ate H1'}"]
        if modo == "real":
            L.append(f"; poco cego: profundidade final {DEPTH} mm")
    L += ["G21", "G90", "G17", "M5", f"G0 Z{Z_PARK}"]
    if modo == "real":
        L += [f"M3 S{SPINDLE_S}", "G4 P3"]
    for nome, x, y, prof in furos:
        if COMENTARIOS:
            L.append(f"; poco {nome}")
        L.append(f"G0 X{x:.3f} Y{y:.3f}")
        if modo == "mark":
            L += ["G0 Z1.0",
                  f"G1 Z{MARK_Z:.3f} F{MARK_FEED}",
                  f"G4 P{MARK_PAUSE}",
                  f"G0 Z{MARK_LIFT}"]
        elif modo == "dry":
            L += [f"G1 Z{DRY_Z:.3f} F{MARK_FEED}", f"G0 Z{Z_SAFE}"]
        else:
            if prof <= -PECK:
                zp = -PECK
                while zp > prof + 1e-9:
                    L += ["G0 Z1.0", f"G1 Z{zp:.3f} F{FEED_DOWN}", f"G0 Z{Z_SAFE}"]
                    zp -= PECK
            L += ["G0 Z1.0", f"G1 Z{prof:.3f} F{FEED_DOWN}", f"G0 Z{Z_SAFE}"]
    
    L += ["M5", f"G0 Z{Z_PARK}", "G0 X0 Y0", "M30"]
    if not COMENTARIOS:
        L = [l for l in L if not l.startswith(";")]
    return "\n".join(L) + "\n"

def preview(furos):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("(instale matplotlib para ver o preview)"); return
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.scatter([f[1] for f in furos], [f[2] for f in furos],
               s=90, facecolors="none", edgecolors="red")
    for nome, x, y, _ in furos:
        if nome in ("A1", "A21", "H1", "H21"):
            ax.annotate(nome, (x, y), textcoords="offset points", xytext=(6, 6))
    ax.set_aspect("equal"); ax.grid(True, ls=":")
    ax.set_xlabel("X (mm) - zero no H1"); ax.set_ylabel("Y (mm)")
    ax.set_title(f"Matriz {ROWS}x{COLS} - zero = H1 (canto inf. esq.), A em cima")
    # plt.savefig("preview_placa.png", dpi=150, bbox_inches="tight")
    # plt.show()

if __name__ == "__main__":
    if "--real" in sys.argv:
        modo = "real"
    elif "--dry" in sys.argv:
        modo = "dry"
    else:
        modo = "mark"
    furos = grade()
    ext_x, ext_y = (COLS-1)*PITCH_X, (ROWS-1)*PITCH_Y
    zero = "H1" if ORDEM_H_PARA_A else "A1"
    print(f"modo={modo.upper()} | {len(furos)} furos | extensao {ext_x:.0f} x {ext_y:.0f} mm")
    print(f"  -> zerar X/Y no poco {zero} e Z na folha!")
    if modo == "real":
        print(f"  -> POÇOS CEGOS de {DEPTH} mm. Spindle LIGA. Confira antes de rodar!")
    if ext_x > WORKSPACE[0] or ext_y > WORKSPACE[1]:
        print("AVISO: extensao maior que o workspace!")
    preview(furos)
    out = {"mark": "marcacao.nc", "dry": "furacao_dry.nc", "real": "furacao.nc"}[modo]
    with open(out, "w", encoding="ascii", newline="\r\n") as fh:
        fh.write(gcode(furos, modo))
    print(f"gravado -> {out}")