import json
import os
from datetime import datetime
from config import CONFIG_FILE, DEFAULT_CONFIG, LINHAS

def calcular_posicao(linha, coluna, cfg):
    x = cfg["x_origem"] + coluna * cfg["espacamento_x"]
    y = cfg["y_origem"] + linha * cfg["espacamento_y"]
    return x, y

def gerar_gcode(cfg, operacoes, pocos_selecionados):
    linhas_gc = []
    def add(cmd): linhas_gc.append(cmd)

    add(f"; eRobot — CEFET-MG")
    add(f"; Protocolo ELISA — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    add(f"; Poços: {len(pocos_selecionados)} | Operações: {', '.join(operacoes)}")
    add(f";")
    add("G21        ; unidades em mm")
    add("G90        ; coordenadas absolutas")
    add("G17        ; plano XY")
    add(f"G0 Z{cfg['z_travel']:.3f}  ; sobe para altura de segurança")
    add("")

    for (li, ci) in pocos_selecionados:
        x, y = calcular_posicao(li, ci, cfg)
        poco_nome = f"{LINHAS[li]}{ci+1}"

        add(f"; ── Poço {poco_nome} ──")
        add(f"G0 X{x:.3f} Y{y:.3f} F{cfg['feed_travel']}  ; move para {poco_nome}")

        if "dispensar" in operacoes:
            add(f"G0 Z{cfg['z_dispensar']:.3f}               ; desce para dispensar")
            add(f"G4 P{cfg['tempo_dispensar']}               ; aguarda {cfg['tempo_dispensar']}ms")
            add(f"G0 Z{cfg['z_travel']:.3f}                  ; sobe")

        if "aspirar" in operacoes:
            add(f"G0 Z{cfg['z_aspirar']:.3f}                 ; desce para aspirar")
            add(f"G4 P{cfg['tempo_aspirar']}                 ; aguarda {cfg['tempo_aspirar']}ms")
            add(f"G0 Z{cfg['z_travel']:.3f}                  ; sobe")
        add("")

    add("; ── Fim do protocolo ──")
    add(f"G0 Z{cfg['z_travel']:.3f}   ; altura de segurança final")
    add("G0 X0 Y0          ; retorna à origem")
    add("M30               ; fim do programa")

    return "\n".join(linhas_gc)

def carregar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                salvo = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(salvo)
            return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def salvar_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)