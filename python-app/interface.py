import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

# Importações dos nossos outros módulos
from config import DEFAULT_CONFIG, LINHAS, COLUNAS
from gerador import carregar_config, salvar_config, gerar_gcode

class ErobotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("eRobot — Gerador ELISA")
        self.resizable(True, True)
        self.configure(bg="#0d1117")
        self.geometry("920x700")

        self.cfg = carregar_config()
        self.pocos_selecionados = set()

        self._build_ui()
        self._selecionar_todos()

    def _build_ui(self):
        # Configuração de Estilos Visuais (Dark Mode)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#0d1117", borderwidth=0)
        style.configure("TNotebook.Tab", background="#161b22", foreground="#8b949e",
                        padding=[14, 6], font=("Courier New", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#1f6feb")], foreground=[("selected", "#ffffff")])
        style.configure("TFrame", background="#0d1117")
        style.configure("TLabelframe", background="#161b22", foreground="#58a6ff",
                        bordercolor="#30363d", font=("Courier New", 9, "bold"))
        style.configure("TLabelframe.Label", background="#161b22", foreground="#58a6ff")

        # Cabeçalho Principal
        header = tk.Frame(self, bg="#0d1117")
        header.pack(fill="x", padx=20, pady=(16, 0))
        tk.Label(header, text="eROBOT", font=("Courier New", 22, "bold"), bg="#0d1117", fg="#1f6feb").pack(side="left")
        tk.Label(header, text=" // GERADOR DE PROTOCOLO ELISA", font=("Courier New", 11), bg="#0d1117", fg="#8b949e").pack(side="left", pady=6)
        tk.Label(header, text="CEFET-MG", font=("Courier New", 9), bg="#0d1117", fg="#3fb950").pack(side="right")

        tk.Frame(self, bg="#30363d", height=1).pack(fill="x", padx=20, pady=8)

        # Sistema de Abas (Notebook)
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=20, pady=0)

        self.tab_placa  = ttk.Frame(nb)
        self.tab_config = ttk.Frame(nb)
        self.tab_gcode  = ttk.Frame(nb)

        nb.add(self.tab_placa,  text="  PLACA 96 POÇOS  ")
        nb.add(self.tab_config, text="  CONFIGURAÇÕES  ")
        nb.add(self.tab_gcode,  text="  G-CODE  ")

        self._build_tab_placa()
        self._build_tab_config()
        self._build_tab_gcode()

        # Rodapé Estilizado
        tk.Frame(self, bg="#30363d", height=1).pack(fill="x", padx=20, pady=(8, 0))
        footer = tk.Frame(self, bg="#0d1117")
        footer.pack(fill="x", padx=20, pady=8)
        tk.Label(footer, text="eROBOT - FUNED x CEFET-MG", font=("Courier New", 8), bg="#0d1117", fg="#484f58").pack(side="left")

    def _build_tab_placa(self):
        frame = self.tab_placa
        frame.configure(style="TFrame")
        
        # Painel Superior de Comandos
        top = tk.Frame(frame, bg="#0d1117")
        top.pack(fill="x", padx=16, pady=10)

        # Bloco de Operações (Checkboxes)
        op_frame = tk.LabelFrame(top, text="OPERAÇÕES", bg="#161b22", fg="#58a6ff", font=("Courier New", 9, "bold"), bd=1, relief="solid", padx=10, pady=6)
        op_frame.pack(side="left", padx=(0, 16))

        self.var_dispensar = tk.BooleanVar(value=True)
        self.var_aspirar   = tk.BooleanVar(value=True)

        for var, label, color in [(self.var_dispensar, "⬇  Dispensar", "#3fb950"), (self.var_aspirar, "⬆  Aspirar", "#f78166")]:
            tk.Checkbutton(op_frame, text=label, variable=var, bg="#161b22", fg=color, selectcolor="#0d1117", activebackground="#161b22", activeforeground=color, font=("Courier New", 10, "bold")).pack(anchor="w")

        # Bloco de Seleção Rápida (Layout Horizontal Matriz 2x2)
        sel_frame = tk.LabelFrame(top, text="SELEÇÃO RÁPIDA", bg="#161b22", fg="#58a6ff", font=("Courier New", 9, "bold"), bd=1, relief="solid", padx=10, pady=6)
        sel_frame.pack(side="left", padx=(0, 16))

        opcoes_rapidas = [
            ("Todos", self._selecionar_todos),
            ("Nenhum", self._desselecionar_todos),
            ("Linhas pares", self._sel_linhas_pares),
            ("Linhas ímpares", self._sel_linhas_impares)
        ]

        for i, (texto, cmd) in enumerate(opcoes_rapidas):
            r = i // 2
            c = i % 2
            btn = tk.Button(
                sel_frame, 
                text=texto, 
                command=cmd, 
                bg="#21262d", 
                fg="#c9d1d9", 
                relief="flat", 
                font=("Courier New", 9), 
                width=14, 
                padx=8, 
                pady=4, 
                activebackground="#30363d", 
                cursor="hand2"
            )
            btn.grid(row=r, column=c, padx=4, pady=3, sticky="ew")

        # Texto de Contagem em Tempo Real
        self.lbl_contagem = tk.Label(top, text="", bg="#0d1117", fg="#8b949e", font=("Courier New", 9))
        self.lbl_contagem.pack(side="left", padx=16)

        # ─── GRADE DA PLACA DE 96 POÇOS ─────────────────────────────────────
        grade_outer = tk.Frame(frame, bg="#0d1117")
        grade_outer.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # Cabeçalho numérico (Colunas 1 a 12) centralizado com as colunas reais
        header_row = tk.Frame(grade_outer, bg="#0d1117")
        header_row.pack(fill="x", pady=(0, 4))
        
        # Espaço em branco no canto superior esquerdo para alinhar com a coluna de letras
        tk.Label(header_row, text="   ", bg="#0d1117", font=("Courier New", 10, "bold"), width=4).grid(row=0, column=0)
        
        # Posiciona cada número com precisão cirúrgica na sua coluna correspondente
        for c_idx, c_num in enumerate(COLUNAS):
            lbl = tk.Label(header_row, text=str(c_num), bg="#0d1117", fg="#8b949e", font=("Courier New", 9, "bold"), width=4)
            lbl.grid(row=0, column=c_idx + 1, padx=2)

        # Construção da Matriz de Botões Circulares
        self.botoes_pocos = {}
        for li, letra in enumerate(LINHAS):
            row_frame = tk.Frame(grade_outer, bg="#0d1117")
            row_frame.pack(fill="x", pady=1)
            
            # Identificador da linha (Letras A-H)
            tk.Label(row_frame, text=f" {letra} ", bg="#0d1117", fg="#8b949e", font=("Courier New", 10, "bold"), width=4).grid(row=0, column=0)

            for ci in range(12):
                btn = tk.Button(
                    row_frame, 
                    text="●", 
                    width=3, 
                    bg="#21262d", 
                    fg="#3fb950", 
                    relief="flat", 
                    font=("Courier New", 10), 
                    activebackground="#30363d", 
                    cursor="hand2", 
                    command=lambda l=li, c=ci: self._toggle_poco(l, c)
                )
                btn.grid(row=0, column=ci + 1, padx=2)
                self.botoes_pocos[(li, ci)] = btn

        # Botão Principal de Processamento
        tk.Button(frame, text="⚙  GERAR G-CODE", command=self._gerar, bg="#1f6feb", fg="#ffffff", relief="flat", font=("Courier New", 11, "bold"), padx=20, pady=8, cursor="hand2", activebackground="#388bfd").pack(pady=10)

    def _build_tab_config(self):
        frame = self.tab_config
        canvas = tk.Canvas(frame, bg="#0d1117", highlightthickness=0)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg="#0d1117")
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.cfg_vars = {}
        campos = [
            ("COORDENADAS DE REFERÊNCIA (mm)", [("x_origem", "X do poço A1"), ("y_origem", "Y do poço A1"), ("z_dispensar", "Z ao dispensar"), ("z_aspirar", "Z ao aspirar"), ("z_travel", "Z de deslocamento (segurança)")]),
            ("ESPAÇAMENTO ENTRE POÇOS (mm)", [("espacamento_x", "Espaçamento X (entre colunas)"), ("espacamento_y", "Espaçamento Y (entre linhas)")]),
            ("VELOCIDADES (mm/min)", [("feed_travel", "Velocidade de deslocamento"), ("feed_operacao", "Velocidade de operação")]),
            ("TEMPOS DE ESPERA (ms)", [("tempo_dispensar", "Tempo ao dispensar"), ("tempo_aspirar", "Tempo ao aspirar")]),
        ]

        for grupo, itens in campos:
            lf = tk.LabelFrame(inner, text=grupo, bg="#161b22", fg="#58a6ff", font=("Courier New", 9, "bold"), bd=1, relief="solid", padx=12, pady=8)
            lf.pack(fill="x", padx=16, pady=8)

            for key, label in itens:
                row = tk.Frame(lf, bg="#161b22")
                row.pack(fill="x", pady=3)
                tk.Label(row, text=label, bg="#161b22", fg="#c9d1d9", font=("Courier New", 9), width=32, anchor="w").pack(side="left")
                var = tk.StringVar(value=str(self.cfg[key]))
                self.cfg_vars[key] = var
                tk.Entry(row, textvariable=var, width=10, bg="#0d1117", fg="#3fb950", insertbackground="#3fb950", relief="flat", font=("Courier New", 10), bd=1).pack(side="left", padx=8)

        btn_row = tk.Frame(inner, bg="#0d1117")
        btn_row.pack(pady=12)
        tk.Button(btn_row, text="💾  SALVAR CONFIGURAÇÕES", command=self._salvar_cfg, bg="#238636", fg="#ffffff", relief="flat", font=("Courier New", 10, "bold"), padx=16, pady=6, cursor="hand2", activebackground="#2ea043").pack(side="left", padx=8)
        tk.Button(btn_row, text="↺  RESTAURAR PADRÕES", command=self._restaurar_cfg, bg="#21262d", fg="#8b949e", relief="flat", font=("Courier New", 10), padx=16, pady=6, cursor="hand2", activebackground="#30363d").pack(side="left")

    def _build_tab_gcode(self):
        frame = self.tab_gcode
        toolbar = tk.Frame(frame, bg="#161b22")
        toolbar.pack(fill="x", padx=0, pady=0)
        tk.Label(toolbar, text="G-CODE GERADO", bg="#161b22", fg="#58a6ff", font=("Courier New", 10, "bold"), padx=12, pady=8).pack(side="left")
        tk.Button(toolbar, text="💾 Salvar arquivo", command=self._salvar_arquivo, bg="#238636", fg="#ffffff", relief="flat", font=("Courier New", 9, "bold"), padx=12, pady=4, cursor="hand2").pack(side="right", padx=8, pady=4)
        tk.Button(toolbar, text="📋 Copiar", command=self._copiar_gcode, bg="#21262d", fg="#c9d1d9", relief="flat", font=("Courier New", 9), padx=12, pady=4, cursor="hand2").pack(side="right", padx=(0, 4), pady=4)

        tk.Frame(frame, bg="#30363d", height=1).pack(fill="x")

        self.txt_gcode = tk.Text(frame, bg="#0d1117", fg="#3fb950", font=("Courier New", 10), relief="flat", insertbackground="#3fb950", selectbackground="#1f6feb", padx=12, pady=12, wrap="none")
        sb_y = ttk.Scrollbar(frame, orient="vertical", command=self.txt_gcode.yview)
        sb_x = ttk.Scrollbar(frame, orient="horizontal", command=self.txt_gcode.xview)
        self.txt_gcode.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.txt_gcode.pack(fill="both", expand=True)

        self.txt_gcode.insert("end", "; O G-code aparecerá aqui após você clicar em GERAR G-CODE\n")
        self.txt_gcode.configure(state="disabled")

    def _toggle_poco(self, li, ci):
        key = (li, ci)
        if key in self.pocos_selecionados:
            self.pocos_selecionados.discard(key)
            self.botoes_pocos[key].configure(fg="#30363d")
        else:
            self.pocos_selecionados.add(key)
            self.botoes_pocos[key].configure(fg="#3fb950")
        self._atualizar_contagem()

    def _selecionar_todos(self):
        for li in range(8):
            for ci in range(12):
                self.pocos_selecionados.add((li, ci))
                self.botoes_pocos[(li, ci)].configure(fg="#3fb950")
        self._atualizar_contagem()

    def _desselecionar_todos(self):
        self.pocos_selecionados.clear()
        for btn in self.botoes_pocos.values():
            btn.configure(fg="#30363d")
        self._atualizar_contagem()

    def _sel_linhas_pares(self):
        self._desselecionar_todos()
        for li in [1, 3, 5, 7]:
            for ci in range(12):
                self.pocos_selecionados.add((li, ci))
                self.botoes_pocos[(li, ci)].configure(fg="#3fb950")
        self._atualizar_contagem()

    def _sel_linhas_impares(self):
        self._desselecionar_todos()
        for li in [0, 2, 4, 6]:
            for ci in range(12):
                self.pocos_selecionados.add((li, ci))
                self.botoes_pocos[(li, ci)].configure(fg="#3fb950")
        self._atualizar_contagem()

    def _atualizar_contagem(self):
        n = len(self.pocos_selecionados)
        self.lbl_contagem.configure(text=f"{n} poço{'s' if n != 1 else ''} selecionado{'s' if n != 1 else ''}")

    def _gerar(self):
        if not self.pocos_selecionados:
            messagebox.showwarning("Atenção", "Selecione ao menos um poço.")
            return

        operacoes = []
        if self.var_dispensar.get(): operacoes.append("dispensar")
        if self.var_aspirar.get(): operacoes.append("aspirar")

        if not operacoes:
            messagebox.showwarning("Atenção", "Selecione ao menos uma operação.")
            return

        # Algoritmo Snake (Zig-zag pelas trilhas da placa)
        pocos_por_linha = {}
        for li, ci in self.pocos_selecionados:
            if li not in pocos_por_linha: pocos_por_linha[li] = []
            pocos_por_linha[li].append((li, ci))

        pocos_ordenados = []
        for li in sorted(pocos_por_linha.keys()):
            pocos_da_linha = sorted(pocos_por_linha[li], key=lambda x: x[1])
            if li % 2 != 0:
                pocos_da_linha.reverse()
            pocos_ordenados.extend(pocos_da_linha)

        gcode = gerar_gcode(self.cfg, operacoes, pocos_ordenados)

        self.txt_gcode.configure(state="normal")
        self.txt_gcode.delete("1.0", "end")
        self.txt_gcode.insert("end", gcode)
        self.txt_gcode.configure(state="disabled")

        for widget in self.winfo_children():
            if isinstance(widget, ttk.Notebook): widget.select(2)

        messagebox.showinfo("G-code gerado!", f"✓ {len(pocos_ordenados)} poços | Operações: {', '.join(operacoes)}\n\nSalve o arquivo e carregue no Mach3.")

    def _salvar_arquivo(self):
        conteudo = self.txt_gcode.get("1.0", "end").strip()
        if not conteudo or conteudo.startswith("; O G-code aparecerá"):
            messagebox.showwarning("Atenção", "Gere o G-code primeiro.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".nc",
            filetypes=[("G-code", "*.nc *.gcode *.txt"), ("Todos", "*.*")],
            initialfile=f"elisa_{datetime.now().strftime('%Y%m%d_%H%M')}.gcode"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(conteudo)
            messagebox.showinfo("Salvo!", f"Arquivo salvo em:\n{path}")

    def _copiar_gcode(self):
        conteudo = self.txt_gcode.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(conteudo)
        messagebox.showinfo("Copiado!", "G-code copiado para a área de transferência.")

    def _salvar_cfg(self):
        try:
            for key, var in self.cfg_vars.items():
                self.cfg[key] = float(var.get())
            salvar_config(self.cfg)
            messagebox.showinfo("Salvo!", "Configurações salvas com sucesso.")
        except ValueError:
            messagebox.showerror("Erro", "Todos os campos devem ser números.")

    def _restaurar_cfg(self):
        if messagebox.askyesno("Restaurar", "Restaurar todos os valores padrão?"):
            self.cfg = DEFAULT_CONFIG.copy()
            for key, var in self.cfg_vars.items():
                var.set(str(self.cfg[key]))