import tkinter as tk
from tkinter import ttk
from nucleo.protocolos import listar_protocolos


class TelaProtocolos(ttk.Frame):
    """Lista os protocolos cadastrados e abre o detalhe do escolhido."""

    def __init__(self, pai, ir_para, abrir_detalhe):
        super().__init__(pai, padding=20)
        self.abrir_detalhe = abrir_detalhe
        ttk.Label(self, text="Protocolos", font=("Helvetica", 20, "bold")).pack(anchor="w")

        self.lista = tk.Listbox(self, height=10)
        self.lista.pack(fill="both", expand=True, pady=10)
        self.lista.bind("<<ListboxSelect>>", self._ao_selecionar)
        self.lista.bind("<Double-Button-1>", lambda e: self._abrir())

        self.detalhe = ttk.Label(self, text="", wraplength=500, foreground="gray")
        self.detalhe.pack(anchor="w")

        rodape = ttk.Frame(self)
        rodape.pack(fill="x", pady=(10, 0))
        ttk.Button(rodape, text="Voltar",
                   command=lambda: ir_para("inicial")).pack(side="left")
        ttk.Button(rodape, text="Abrir", command=self._abrir).pack(side="right")

        self.protocolos = []
        self.atualizar()

    def atualizar(self):
        """Relê a pasta de protocolos."""
        self.protocolos = listar_protocolos()
        self.lista.delete(0, tk.END)
        for p in self.protocolos:
            self.lista.insert(tk.END, p.nome)

    def _ao_selecionar(self, _evento):
        selecao = self.lista.curselection()
        if selecao:
            self.detalhe.config(text=self.protocolos[selecao[0]].descricao)

    def _abrir(self):
        selecao = self.lista.curselection()
        if selecao:
            self.abrir_detalhe(self.protocolos[selecao[0]])
