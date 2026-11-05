from tkinter import ttk

NOME_APP = "eROBOT"
VERSAO = "0.1.0"


class TelaInicial(ttk.Frame):
    """Tela de entrada com as duas ações principais."""

    def __init__(self, pai, ir_para):
        super().__init__(pai, padding=40)
        ttk.Label(self, text=NOME_APP, font=("Helvetica", 28, "bold")).pack(pady=(0, 4))
        ttk.Label(self, text="Gerador de movimentos para CNC").pack(pady=(0, 30))

        ttk.Button(self, text="Protocolos",
                   command=lambda: ir_para("protocolos")).pack(fill="x", pady=6, ipady=10)
        ttk.Button(self, text="Coletar Resultados",
                   command=lambda: ir_para("resultados")).pack(fill="x", pady=6, ipady=10)

        ttk.Label(self, text=f"v{VERSAO}", foreground="gray").pack(side="bottom", pady=(30, 0))
