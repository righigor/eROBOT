from tkinter import ttk
from nucleo.ordem import ordenar_serpentina
from ui.dialogo_gerar import DialogoGerar
from ui.grade_placa import GradePlaca


class TelaDetalheProtocolo(ttk.Frame):
    """Nome, descrição e seleção dos poços de um protocolo."""

    def __init__(self, pai, ir_para):
        super().__init__(pai, padding=20)
        self.protocolo = None

        self.titulo = ttk.Label(self, text="", font=("Helvetica", 20, "bold"))
        self.titulo.pack(anchor="w")
        self.descricao = ttk.Label(self, text="", wraplength=580, foreground="gray")
        self.descricao.pack(anchor="w", pady=(2, 10))

        ttk.Separator(self).pack(fill="x", pady=4)
        ttk.Label(self, text="Poços utilizados").pack(anchor="w", pady=(6, 4))

        self.resumo = ttk.Label(self, text="")
        self.grade = GradePlaca(self, ao_mudar=self._ao_mudar)
        self.grade.pack(anchor="w")

        barra = ttk.Frame(self)
        barra.pack(anchor="w", pady=6)
        ttk.Button(barra, text="Limpar", command=self.grade.limpar).pack(side="left")
        ttk.Button(barra, text="Selecionar tudo",
                   command=self.grade.selecionar_tudo).pack(side="left", padx=6)

        ttk.Label(self, foreground="gray", wraplength=580,
                  text="Clique ou arraste para selecionar; botão direito desmarca; "
                       "clique na letra/número para linha/coluna inteira. "
                       "Contorno laranja = H1, onde a CNC começa.").pack(anchor="w")

        self.resumo.pack(anchor="w", pady=(8, 0))

        rodape = ttk.Frame(self)
        rodape.pack(fill="x", side="bottom", pady=(14, 0))
        ttk.Button(rodape, text="Voltar",
                   command=lambda: ir_para("protocolos")).pack(side="left")
        self.botao_gerar = ttk.Button(rodape, text="Gerar G-code", state="disabled",
                                      command=self._abrir_dialogo)
        self.botao_gerar.pack(side="right")

    def carregar(self, protocolo):
        """Mostra um protocolo (chamado ao abrir a tela)."""
        self.protocolo = protocolo
        self.titulo.config(text=protocolo.nome)
        self.descricao.config(text=protocolo.descricao)
        self.grade.limpar()

    def _abrir_dialogo(self):
        pocos = self.grade.selecionados()
        if self.protocolo and pocos:
            DialogoGerar(self, self.protocolo, pocos)

    def _ao_mudar(self):
        ordem = ordenar_serpentina(self.grade.selecionados())
        # O botão só vale com pelo menos um poço selecionado
        self.botao_gerar.config(state="normal" if ordem else "disabled")
        if not ordem:
            self.resumo.config(text="Nenhum poço selecionado.")
            return
        previa = " → ".join(ordem[:10]) + (" → ..." if len(ordem) > 10 else "")
        self.resumo.config(
            text=f"{len(ordem)} poço(s) | início: {ordem[0]} | fim: {ordem[-1]}\n"
                 f"Ordem da CNC: {previa}")
