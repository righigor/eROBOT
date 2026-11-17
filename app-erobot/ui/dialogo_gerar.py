
"""Janela de geração de G-code."""

import tkinter as tk

from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from ui.componente_pipetas import SeletorPipetas

from nucleo.config import carregar
from nucleo.gerador import gerar, sugerir_nome, MAX_NOME
from nucleo.ordem import ordenar_serpentina
from nucleo.movimentos_pipetagem import agrupar_pocos
from nucleo.seguranca import ErroSeguranca


class DialogoGerar(tk.Toplevel):

    def __init__(self, pai, protocolo, pocos):
        super().__init__(pai)

        self.title("Gerar G-code")
        self.transient(pai)
        self.resizable(False, True)
        self.geometry("500x620")
        self.minsize(460, 480)

        self.protocolo = protocolo
        self.pocos = list(pocos)

        if not self.pocos:
            messagebox.showerror(
                "Seleção vazia",
                "Selecione pelo menos um poço.",
                parent=self,
            )
            self.destroy()
            return

        # Carrega as configurações correspondentes ao protocolo.
        self.pipeta = carregar("pipeta")

        nome_placa = getattr(
            protocolo,
            "placa",
            "placa",
        )
        self.placa = carregar(nome_placa)

        provisorio = self.pipeta.get("provisorio", True)

        # Área principal com rolagem.
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            container,
            highlightthickness=0,
        )

        barra = ttk.Scrollbar(
            container,
            orient="vertical",
            command=canvas.yview,
        )

        corpo = ttk.Frame(canvas, padding=16)

        janela_corpo = canvas.create_window(
            (0, 0),
            window=corpo,
            anchor="nw",
        )

        corpo.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            ),
        )

        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(
                janela_corpo,
                width=e.width,
            ),
        )

        canvas.configure(yscrollcommand=barra.set)

        canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        ttk.Label(
            corpo,
            text=f"Protocolo: {protocolo.nome}",
            font=("Helvetica", 12, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            corpo,
            text=(
                f"Placa: {self.placa.get('modelo', nome_placa)} "
                f"({self.placa['linhas']} x {self.placa['colunas']})"
            ),
        ).pack(anchor="w")

        ordem = ordenar_serpentina(
            self.pocos,
            self.placa,
        )

        ttk.Label(
            corpo,
            text=(
                f"{len(ordem)} poço(s) selecionado(s) | "
                f"início {ordem[0]} | fim {ordem[-1]}"
            ),
        ).pack(anchor="w", pady=(0, 10))

        # Seletor de pontas.
        self.seletor_pipetas = SeletorPipetas(
            corpo,
            quantidade_inicial=3,
        )
        self.seletor_pipetas.pack(
            fill="x",
            pady=(8, 8),
        )

        self.resumo = ttk.Label(
            corpo,
            wraplength=410,
            justify="left",
        )
        self.resumo.pack(anchor="w", pady=(0, 10))

        self.seletor_pipetas.quantidade.trace_add(
            "write",
            lambda *_: self._atualizar_resumo(),
        )

        # Modo de execução.
        self.modo = tk.StringVar(value="dry")

        ttk.Label(
            corpo,
            text="Modo de operação:",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w", pady=(4, 2))

        ttk.Radiobutton(
            corpo,
            text="Teste no ar (dry-run)",
            value="dry",
            variable=self.modo,
        ).pack(anchor="w")

        ttk.Radiobutton(
            corpo,
            text="Real (pipeta entra nos poços)",
            value="real",
            variable=self.modo,
            state="disabled" if provisorio else "normal",
        ).pack(anchor="w")

        if provisorio:
            ttk.Label(
                corpo,
                foreground="#b9770e",
                wraplength=400,
                text=(
                    "Modo REAL bloqueado: os parâmetros físicos "
                    "da pipeta ainda são provisórios."
                ),
            ).pack(anchor="w", pady=(4, 0))

        # Nome do arquivo.
        linha = ttk.Frame(corpo)
        linha.pack(fill="x", pady=(12, 0))

        ttk.Label(
            linha,
            text="Nome do arquivo:",
        ).pack(side="left")

        self.nome = tk.StringVar()

        ttk.Entry(
            linha,
            textvariable=self.nome,
            width=20,
        ).pack(side="left", padx=4)

        ttk.Label(
            linha,
            text=".nc",
        ).pack(side="left")

        ttk.Label(
            corpo,
            foreground="gray",
            text=(
                f"Até {MAX_NOME} caracteres: "
                "letras, números, _ e -"
            ),
        ).pack(anchor="w")

        # Pasta de saída.
        linha2 = ttk.Frame(corpo)
        linha2.pack(fill="x", pady=(10, 0))

        ttk.Label(
            linha2,
            text="Pasta (pendrive):",
        ).pack(side="left")

        downloads = Path.home() / "Downloads"

        if not downloads.exists():
            downloads = Path.home()

        self.pasta = tk.StringVar(value=str(downloads))

        ttk.Entry(
            linha2,
            textvariable=self.pasta,
            width=30,
        ).pack(side="left", padx=4)

        ttk.Button(
            linha2,
            text="Escolher...",
            command=self._escolher_pasta,
        ).pack(side="left")

        ttk.Label(
            corpo,
            foreground="gray",
            wraplength=410,
            text=(
                "Lembrete: pendrive em FAT32. "
                "Ejete-o pelo sistema antes de retirar."
            ),
        ).pack(anchor="w", pady=(10, 0))

        # Rodapé fixo.
        rodape = ttk.Frame(self, padding=(16, 10))
        rodape.pack(side="bottom", fill="x")

        ttk.Separator(
            self,
            orient="horizontal",
        ).pack(side="bottom", fill="x")

        ttk.Button(
            rodape,
            text="Cancelar",
            command=self.destroy,
        ).pack(side="left")

        self.botao_gerar = ttk.Button(
            rodape,
            text="Gerar G-code",
            command=self._gerar,
        )
        self.botao_gerar.pack(side="right")

        # Sugestão de nome.
        self._sugestao = ""
        self._atualizar_sugestao()

        self.modo.trace_add(
            "write",
            lambda *_: self._atualizar_sugestao(),
        )

        self._atualizar_resumo()

        self.wait_visibility()
        self.grab_set()

    def _atualizar_resumo(self):
        """Valida e apresenta a estratégia selecionada."""

        try:
            quantidade = self.seletor_pipetas.get_quantidade()

            if quantidade == 1:
                texto = (
                    "Configuração: uma ponta.\n"
                    f"Posicionamentos: {len(self.pocos)}.\n"
                    "Cada poço será visitado individualmente."
                )

            else:
                grupos = agrupar_pocos(
                    pocos=self.pocos,
                    placa=self.placa,
                    pipeta=self.pipeta,
                    quantidade_pontas=quantidade,
                )

                total = sum(
                    len(grupo.pocos)
                    for grupo in grupos
                )

                texto = (
                    f"Configuração: {quantidade} pontas simultâneas.\n"
                    f"Grupos: {len(grupos)}.\n"
                    f"Poços atendidos: {total}.\n"
                    "Cada grupo será atendido em um único "
                    "posicionamento XY."
                )

            self.resumo.configure(
                text=texto,
                foreground="#247a45",
            )

            self.botao_gerar.configure(state="normal")

        except ValueError as erro:
            self.resumo.configure(
                text=f"Seleção incompatível:\n{erro}",
                foreground="#b9770e",
            )

            self.botao_gerar.configure(state="disabled")

    def _atualizar_sugestao(self):
        nova = sugerir_nome(
            self.protocolo.nome,
            len(self.pocos),
            self.modo.get(),
        )

        if self.nome.get() in ("", self._sugestao):
            self.nome.set(nova)

        self._sugestao = nova

    def _escolher_pasta(self):
        escolhida = filedialog.askdirectory(
            parent=self,
            initialdir=self.pasta.get(),
        )

        if escolhida:
            self.pasta.set(escolhida)

    def _gerar(self):
        modo = self.modo.get()
        nome = self.nome.get().strip()
        pasta = self.pasta.get().strip()

        try:
            quantidade_pontas = (
                self.seletor_pipetas.get_quantidade()
            )

        except ValueError as erro:
            messagebox.showerror(
                "Configuração inválida",
                str(erro),
                parent=self,
            )
            return

        if not nome:
            messagebox.showerror(
                "Nome inválido",
                "Informe um nome para o arquivo.",
                parent=self,
            )
            return

        destino = Path(pasta) / f"{nome}.nc"

        sobrescrever = False

        if destino.exists():
            if not messagebox.askyesno(
                "Arquivo existente",
                f"{destino.name} já existe nessa pasta.\n"
                "Substituir?",
                parent=self,
            ):
                return

            sobrescrever = True

        if modo == "real" and not messagebox.askyesno(
            "Modo REAL",
            "A pipeta vai entrar nos poços.\n"
            "Os parâmetros físicos foram conferidos?",
            parent=self,
        ):
            return

        try:
            resultado = gerar(
                self.protocolo.nome,
                self.pocos,
                modo,
                nome,
                pasta,
                sobrescrever=sobrescrever,
                quantidade_pontas=quantidade_pontas,
                pipeta=self.pipeta,
                placa=self.placa,
            )

        except (ErroSeguranca, ValueError, OSError) as erro:
            messagebox.showerror(
                "Não foi possível gerar",
                str(erro),
                parent=self,
            )
            return

        messagebox.showinfo(
            "G-code gerado",
            (
                f"Arquivo: {resultado.arquivo_nc.name}\n"
                f"Poços: {resultado.n_pocos}\n"
                f"Linhas G-code: {resultado.n_linhas}\n"
                f"Pontas: {quantidade_pontas}\n\n"
                f"Salvo em: {resultado.arquivo_nc.parent}\n\n"
                f"Relatório: {resultado.arquivo_relatorio}\n\n"
                "Ejete o pendrive pelo sistema antes de retirá-lo."
            ),
            parent=self,
        )

        self.destroy()
