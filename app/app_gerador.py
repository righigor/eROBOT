#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_gerador.py — Gerador de G-code de pocos (Cobra CNC WK-3030 / DSP RichAuto A11)

App desktop Tkinter. Se faltar no Ubuntu:  sudo apt install python3-tk
Rodar:  python3 app_gerador.py

Recursos:
  - Matriz configuravel (linhas, colunas, passos, profundidade)
  - Grade clicavel: clique alterna, arrastar pinta, botao direito apaga
  - Todos / Limpar / Inverter
  - Protocolos (presets) salvos em presets.json, incluindo a selecao de pocos
  - Geracao com escolha de local + dialogo final (lembrete do pendrive)
  - Padrao seguro: MARCAR (nao gira). FURAR REAL pede confirmacao.
"""

import json
import os
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PRESETS_FILE = os.path.join(APP_DIR, "presets.json")

NOME_MODO = {"mark": "marcacao", "dry": "teste_no_ar", "real": "FURA_de_verdade"}
LETRAS = "ABCDEFGHIJKLMNOPQRSTUVW"


# ============================== NUCLEO (G-code) ==============================
def gerar_gcode(rows, cols, pitch_x, pitch_y, depth, selecionados, modo,
                serpentina=True):
    """Zero da peca = canto INFERIOR esquerdo; Z0 = superficie da folha.
    Ordem: de baixo para cima. Gera apenas os pocos em `selecionados`."""
    letras = LETRAS[:rows]
    L = ["; gerado pelo app_gerador",
         f"; {datetime.now().strftime('%Y-%m-%d %H:%M')}",
         f"; modo: {modo.upper()}  |  matriz {rows}x{cols}",
         "; zero = canto inferior esquerdo, Z0 = superficie da FOLHA",
         "G21", "G90", "G17", "M5", "G0 Z5.0"]
    if modo == "real":
        L += ["M3 S10000", "G4 P3"]

    n = 0
    for k, j in enumerate(range(rows - 1, -1, -1)):      # de baixo p/ cima
        ordem = reversed(range(cols)) if (serpentina and k % 2 == 1) else range(cols)
        for c in ordem:
            nome = f"{letras[j]}{c + 1}"
            if nome not in selecionados:
                continue
            n += 1
            x, y = c * pitch_x, (rows - 1 - j) * pitch_y
            L.append(f"; poco {nome}")
            L.append(f"G0 X{x:.3f} Y{y:.3f}")
            if modo == "mark":
                L += ["G0 Z1.0", "G1 Z0.000 F60", "G4 P2.0", "G0 Z10.0"]
            elif modo == "dry":
                L += ["G1 Z2.000 F60", "G0 Z5.0"]
            else:
                if depth <= -2.0:                        # peck se for fundo
                    zp = -2.0
                    while zp > depth + 1e-9:
                        L += ["G0 Z1.0", f"G1 Z{zp:.3f} F150", "G0 Z5.0"]
                        zp -= 2.0
                L += ["G0 Z1.0", f"G1 Z{depth:.3f} F150", "G0 Z5.0"]
    L += ["M5", "G0 X0 Y0", "M30"]
    return "\n".join(L) + "\n", n


# =================================== APP =====================================
class App(tk.Tk):
    CELL, MARG = 38, 34

    def __init__(self):
        super().__init__()
        self.title("Gerador de G-code — Placa de pocos (Cobra WK-3030)")
        self.presets = self._carregar_presets()
        self.selecao = set()
        self._ovals = {}
        self._modo_pintura = None
        self._montar_ui()
        self._redesenhar()

    # ------------------------------ UI -----------------------------------
    def _montar_ui(self):
        esq = ttk.Frame(self, padding=10)
        esq.pack(side="left", fill="y")

        p = ttk.LabelFrame(esq, text="Parametros da matriz", padding=8)
        p.pack(fill="x")
        self.v_rows, self.v_cols = tk.StringVar(value="8"), tk.StringVar(value="21")
        self.v_px, self.v_py = tk.StringVar(value="9.53"), tk.StringVar(value="33.72")
        self.v_depth = tk.StringVar(value="-1.5")
        for i, (rot, var) in enumerate([
                ("Linhas (A...):", self.v_rows), ("Colunas (1...):", self.v_cols),
                ("Passo X (mm):", self.v_px), ("Passo Y (mm):", self.v_py),
                ("Profund. real (mm):", self.v_depth)]):
            ttk.Label(p, text=rot).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(p, textvariable=var, width=9).grid(row=i, column=1, padx=4)
        ttk.Button(p, text="Atualizar grade",
                   command=self._redesenhar).grid(row=5, column=0, columnspan=2,
                                                  sticky="ew", pady=(6, 0))

        m = ttk.LabelFrame(esq, text="Modo de saida", padding=8)
        m.pack(fill="x", pady=8)
        self.v_modo = tk.StringVar(value="mark")
        for val, rot in [("mark", "MARCAR (toca, nao gira)"),
                         ("dry", "TESTE NO AR"),
                         ("real", "FURAR REAL (spindle liga!)")]:
            ttk.Radiobutton(m, text=rot, value=val,
                            variable=self.v_modo).pack(anchor="w")
        self.v_serp = tk.BooleanVar(value=True)
        ttk.Checkbutton(m, text="Serpentina (mais rapido)",
                        variable=self.v_serp).pack(anchor="w", pady=(4, 0))

        s = ttk.LabelFrame(esq, text="Selecao", padding=8)
        s.pack(fill="x")
        row = ttk.Frame(s)
        row.pack(fill="x")
        ttk.Button(row, text="Todos", width=7, command=self._todos).pack(side="left", padx=2)
        ttk.Button(row, text="Limpar", width=7, command=self._limpar).pack(side="left", padx=2)
        ttk.Button(row, text="Inverter", width=8, command=self._inverter).pack(side="left", padx=2)
        self.lbl_cont = ttk.Label(s, text="0 pocos selecionados")
        self.lbl_cont.pack(anchor="w", pady=(4, 0))

        pr = ttk.LabelFrame(esq, text="Protocolos (presets)", padding=8)
        pr.pack(fill="x", pady=8)
        self.combo = ttk.Combobox(pr, state="readonly",
                                  values=sorted(self.presets))
        self.combo.pack(fill="x")
        self.v_nome = tk.StringVar()
        ttk.Entry(pr, textvariable=self.v_nome).pack(fill="x", pady=4)
        row2 = ttk.Frame(pr)
        row2.pack(fill="x")
        ttk.Button(row2, text="Salvar", width=7,
                   command=self._preset_salvar).pack(side="left", padx=2)
        ttk.Button(row2, text="Carregar", width=8,
                   command=self._preset_carregar).pack(side="left", padx=2)
        ttk.Button(row2, text="Excluir", width=7,
                   command=self._preset_excluir).pack(side="left", padx=2)

        ttk.Button(esq, text="GERAR G-CODE", command=self._gerar)\
            .pack(fill="x", pady=10, ipady=6)

        dir_ = ttk.Frame(self)
        dir_.pack(side="right", fill="both", expand=True)
        self.canvas = tk.Canvas(dir_, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<B1-Motion>", self._motion)
        self.canvas.bind("<ButtonRelease-1>",
                         lambda e: setattr(self, "_modo_pintura", None))
        self.canvas.bind("<Button-3>", self._click_apaga)
        self.canvas.bind("<B3-Motion>", self._motion_apaga)

    # ---------------------------- grade ----------------------------------
    def _redesenhar(self):
        try:
            self._rows = max(1, int(self.v_rows.get()))
            self._cols = max(1, int(self.v_cols.get()))
        except ValueError:
            messagebox.showerror("Parametros", "Linhas e colunas devem ser inteiros.")
            return
        self._letras = LETRAS[:self._rows]
        validos = {f"{self._letras[j]}{c+1}"
                   for j in range(self._rows) for c in range(self._cols)}
        self.selecao &= validos                      # descarta nomes obsoletos

        cv = self.canvas
        cv.delete("all")
        self._ovals.clear()
        w = self.MARG * 2 + self._cols * self.CELL
        h = self.MARG * 2 + self._rows * self.CELL
        cv.config(width=w, height=h, scrollregion=(0, 0, w, h))
        for j in range(self._rows):
            for c in range(self._cols):
                x1, y1 = self.MARG + c * self.CELL, self.MARG + j * self.CELL
                nome = f"{self._letras[j]}{c+1}"
                cv.create_text(x1 + 2, y1 + 2, text=nome, anchor="nw",
                               font=("TkDefaultFont", 7), fill="#666")
                r = self.CELL * 0.30
                cx, cy = x1 + self.CELL / 2, y1 + self.CELL / 2 + 4
                o = cv.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#444",
                                   fill="#c0392b" if nome in self.selecao else "#bdc3c7")
                self._ovals[nome] = o
        self._contagem()

    def _nome_em(self, x, y):
        c = (x - self.MARG) // self.CELL
        j = (y - self.MARG) // self.CELL
        if 0 <= j < self._rows and 0 <= c < self._cols:
            return f"{self._letras[int(j)]}{int(c)+1}"
        return None

    def _pinta(self, nome):
        self.canvas.itemconfig(self._ovals[nome],
                               fill="#c0392b" if nome in self.selecao else "#bdc3c7")

    def _contagem(self):
        self.lbl_cont.config(text=f"{len(self.selecao)} pocos selecionados")

    # --------------------------- interacao --------------------------------
    def _click(self, e):
        nome = self._nome_em(e.x, e.y)
        if not nome:
            return
        if nome in self.selecao:
            self.selecao.discard(nome)
            self._modo_pintura = "apagar"
        else:
            self.selecao.add(nome)
            self._modo_pintura = "pintar"
        self._pinta(nome)
        self._contagem()

    def _motion(self, e):
        if not self._modo_pintura:
            return
        nome = self._nome_em(e.x, e.y)
        if nome:
            (self.selecao.add if self._modo_pintura == "pintar"
             else self.selecao.discard)(nome)
            self._pinta(nome)
            self._contagem()

    def _click_apaga(self, e):
        self._modo_pintura = "apagar"
        nome = self._nome_em(e.x, e.y)
        if nome:
            self.selecao.discard(nome)
            self._pinta(nome)
            self._contagem()

    def _motion_apaga(self, e):
        if self._modo_pintura != "apagar":
            return
        nome = self._nome_em(e.x, e.y)
        if nome:
            self.selecao.discard(nome)
            self._pinta(nome)
            self._contagem()

    def _nomes_validos(self):
        return {f"{self._letras[j]}{c+1}"
                for j in range(self._rows) for c in range(self._cols)}

    def _repintar_tudo(self):
        for nome in self._ovals:
            self._pinta(nome)
        self._contagem()

    def _todos(self):
        self.selecao |= self._nomes_validos()
        self._repintar_tudo()

    def _limpar(self):
        self.selecao.clear()
        self._repintar_tudo()

    def _inverter(self):
        self.selecao = self._nomes_validos() - self.selecao
        self._repintar_tudo()

    # ---------------------------- presets ---------------------------------
    def _carregar_presets(self):
        if os.path.exists(PRESETS_FILE):
            try:
                with open(PRESETS_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, ValueError):
                messagebox.showwarning("Presets", "presets.json invalido — sera recriado.")
        return {}

    def _gravar_presets(self):
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.presets, f, indent=2, ensure_ascii=False)

    def _preset_salvar(self):
        nome = self.v_nome.get().strip()
        if not nome:
            messagebox.showwarning("Presets", "Escreva um nome para o protocolo.")
            return
        try:
            dados = {"rows": self._rows, "cols": self._cols,
                     "pitch_x": float(self.v_px.get()),
                     "pitch_y": float(self.v_py.get()),
                     "depth": float(self.v_depth.get()),
                     "serpentina": bool(self.v_serp.get()),
                     "selecao": sorted(self.selecao)}
        except ValueError:
            messagebox.showerror("Presets", "Passos/profundidade invalidos.")
            return
        if nome in self.presets and not messagebox.askyesno(
                "Presets", f"'{nome}' ja existe. Sobrescrever?"):
            return
        self.presets[nome] = dados
        self._gravar_presets()
        self._refresh_combo()
        self.combo.set(nome)
        messagebox.showinfo("Presets", f"Protocolo '{nome}' salvo.")

    def _preset_carregar(self):
        nome = self.combo.get()
        if not nome:
            messagebox.showwarning("Presets", "Selecione um protocolo na lista.")
            return
        d = self.presets[nome]
        self.v_rows.set(str(d["rows"]))
        self.v_cols.set(str(d["cols"]))
        self.v_px.set(str(d["pitch_x"]))
        self.v_py.set(str(d["pitch_y"]))
        self.v_depth.set(str(d["depth"]))
        self.v_serp.set(d.get("serpentina", True))
        self.selecao = set(d.get("selecao", []))
        self._redesenhar()

    def _preset_excluir(self):
        nome = self.combo.get()
        if not nome:
            messagebox.showwarning("Presets", "Selecione um protocolo na lista.")
            return
        if messagebox.askyesno("Presets", f"Excluir '{nome}'?"):
            self.presets.pop(nome)
            self._gravar_presets()
            self._refresh_combo()

    def _refresh_combo(self):
        self.combo["values"] = sorted(self.presets)

    # ----------------------------- gerar ----------------------------------
    def _gerar(self):
        modo = self.v_modo.get()
        try:
            px, py = float(self.v_px.get()), float(self.v_py.get())
            depth = float(self.v_depth.get())
        except ValueError:
            messagebox.showerror("Parametros", "Passos e profundidade devem ser numeros.")
            return
        if not self.selecao:
            if messagebox.askyesno("Selecao vazia",
                                   "Nenhum poco selecionado.\nSelecionar TODOS?"):
                self._todos()
            else:
                return
        if modo == "real" and not messagebox.askyesno(
                "Confirmacao",
                f"FURACAO REAL:\n- spindle vai LIGAR\n- profundidade {depth} mm\n\nContinuar?"):
            return
        inicial = f"{NOME_MODO[modo]}_{datetime.now():%Y%m%d_%H%M}.nc"
        caminho = filedialog.asksaveasfilename(
            title="Salvar G-code", defaultextension=".nc", initialfile=inicial,
            filetypes=[("G-code", "*.nc *.tap *.gcode"), ("Todos", "*.*")])
        if not caminho:
            return
        texto, n = gerar_gcode(self._rows, self._cols, px, py, depth,
                               self.selecao, modo, self.v_serp.get())
        try:
            with open(caminho, "w", encoding="ascii", newline="\r\n") as f:
                f.write(texto)
        except OSError as err:
            messagebox.showerror("Erro", f"Nao consegui salvar:\n{err}")
            return
        messagebox.showinfo(
            "G-code gerado",
            f"{n} pocos gravados em:\n{caminho}\n\n"
            "Proximos passos:\n"
            "1) Copie o arquivo para o PENDRIVE (FAT32)\n"
            "2) No pendant A11, selecione o arquivo e rode\n"
            "3) Use feed reduzido nos primeiros pocos")
        if messagebox.askyesno("Abrir pasta",
                               "Abrir a pasta onde o arquivo foi salvo?"):
            subprocess.Popen(["xdg-open", os.path.dirname(os.path.abspath(caminho))])


if __name__ == "__main__":
    App().mainloop()