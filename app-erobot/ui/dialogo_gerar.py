"""Janela 'Gerar G-code': modo, nome do arquivo e pasta de saída."""
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from nucleo.config import carregar
from nucleo.gerador import gerar, sugerir_nome, MAX_NOME
from nucleo.ordem import ordenar_serpentina
from nucleo.seguranca import ErroSeguranca


class DialogoGerar(tk.Toplevel):
    def __init__(self, pai, protocolo, pocos):
        super().__init__(pai)
        self.title("Gerar G-code")
        self.transient(pai)
        self.resizable(False, False)
        self.protocolo = protocolo
        self.pocos = pocos

        ordem = ordenar_serpentina(pocos)
        provisorio = carregar("pipeta").get("provisorio", True)

        corpo = ttk.Frame(self, padding=16)
        corpo.pack(fill="both", expand=True)

        ttk.Label(corpo, text=f"Protocolo: {protocolo.nome}",
                  font=("Helvetica", 12, "bold")).pack(anchor="w")
        ttk.Label(corpo, text=f"{len(ordem)} poço(s) | início {ordem[0]} | fim {ordem[-1]}"
                  ).pack(anchor="w", pady=(0, 10))

        # Modo: o padrão é o seguro (teste no ar)
        self.modo = tk.StringVar(value="dry")
        ttk.Radiobutton(corpo, text="Teste no ar (dry-run)", value="dry",
                        variable=self.modo).pack(anchor="w")
        ttk.Radiobutton(corpo, text="Real (pipeta entra nos poços)", value="real",
                        variable=self.modo,
                        state="disabled" if provisorio else "normal").pack(anchor="w")
        if provisorio:
            ttk.Label(corpo, foreground="#b9770e", wraplength=380,
                      text="Modo real bloqueado: parâmetros da pipeta ainda são "
                           "provisórios (config/pipeta.toml).").pack(anchor="w", pady=(2, 0))

        # Nome do arquivo (curto, sem acentos)
        linha = ttk.Frame(corpo)
        linha.pack(fill="x", pady=(12, 0))
        ttk.Label(linha, text="Nome do arquivo:").pack(side="left")
        self.nome = tk.StringVar()
        ttk.Entry(linha, textvariable=self.nome, width=20).pack(side="left", padx=4)
        ttk.Label(linha, text=".nc").pack(side="left")
        ttk.Label(corpo, foreground="gray",
                  text=f"Até {MAX_NOME} caracteres: letras, números, _ e -").pack(anchor="w")

        # Pasta de saída
        linha2 = ttk.Frame(corpo)
        linha2.pack(fill="x", pady=(10, 0))
        ttk.Label(linha2, text="Pasta (pendrive):").pack(side="left")
        self.pasta = tk.StringVar(value=str(Path.home()))
        ttk.Entry(linha2, textvariable=self.pasta, width=30).pack(side="left", padx=4)
        ttk.Button(linha2, text="Escolher...", command=self._escolher_pasta).pack(side="left")

        ttk.Label(corpo, foreground="gray", wraplength=400,
                  text="Lembrete: pendrive em FAT32. Depois de gerar, ejete-o pelo "
                       "sistema antes de retirar.").pack(anchor="w", pady=(10, 0))

        rodape = ttk.Frame(corpo)
        rodape.pack(fill="x", pady=(14, 0))
        ttk.Button(rodape, text="Cancelar", command=self.destroy).pack(side="left")
        ttk.Button(rodape, text="Gerar", command=self._gerar).pack(side="right")

        # Sugestão de nome: acompanha o modo enquanto o usuário não editar
        self._sugestao = ""
        self._atualizar_sugestao()
        self.modo.trace_add("write", lambda *_: self._atualizar_sugestao())

        self.wait_visibility()
        self.grab_set()

    def _atualizar_sugestao(self):
        nova = sugerir_nome(self.protocolo.nome, len(self.pocos), self.modo.get())
        if self.nome.get() in ("", self._sugestao):
            self.nome.set(nova)
        self._sugestao = nova

    def _escolher_pasta(self):
        escolhida = filedialog.askdirectory(parent=self, initialdir=self.pasta.get())
        if escolhida:
            self.pasta.set(escolhida)

    def _gerar(self):
        modo = self.modo.get()
        nome = self.nome.get().strip()
        pasta = self.pasta.get().strip()

        sobrescrever = False
        destino = Path(pasta) / f"{nome}.nc"
        if destino.exists():
            if not messagebox.askyesno("Arquivo existente",
                                       f"{destino.name} já existe nessa pasta.\n"
                                       "Substituir?", parent=self):
                return
            sobrescrever = True

        if modo == "real" and not messagebox.askyesno(
                "Modo REAL", "A pipeta vai entrar nos poços.\n"
                             "Os parâmetros foram conferidos?", parent=self):
            return

        try:
            res = gerar(self.protocolo.nome, self.pocos, modo, nome, pasta,
                        sobrescrever=sobrescrever)
        except (ErroSeguranca, ValueError, OSError) as erro:
            messagebox.showerror("Não foi possível gerar", str(erro), parent=self)
            return

        messagebox.showinfo(
            "G-code gerado",
            f"{res.arquivo_nc.name} ({res.n_pocos} poços, {res.n_linhas} linhas)\n"
            f"Salvo em: {res.arquivo_nc.parent}\n\n"
            f"Relatório (no PC): {res.arquivo_relatorio}\n\n"
            "Ejete o pendrive pelo sistema antes de retirá-lo.", parent=self)
        self.destroy()
