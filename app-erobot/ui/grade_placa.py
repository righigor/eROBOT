
"""Grade clicável de placas de poços.

Desenha e gerencia a seleção. Não conhece G-code nem movimentos.
A geometria pode ser configurada dinamicamente.
"""
import tkinter as tk

LETRAS_PADRAO = list("ABCDEFGH")

COR_VAZIA = "#f0f0f0"
COR_SELECIONADO = "#2e86de"
COR_BORDA = "#888888"
COR_INICIO = "#e67e22"


class GradePlaca(tk.Canvas):
    MARGEM_E = 26
    MARGEM_T = 22

    def __init__(
        self,
        pai,
        linhas=8,
        colunas=21,
        tamanho=22,
        ao_mudar=None,
        rotulos_linhas=None,
    ):
        self.tamanho = tamanho
        self.ao_mudar = ao_mudar

        self.linhas = 0
        self.colunas = 0
        self.rotulos_linhas = []

        self._sel = set()
        self._ids = {}
        self._modo = None

        super().__init__(
            pai,
            highlightthickness=0,
        )

        self.configurar(
            linhas=linhas,
            colunas=colunas,
            rotulos_linhas=rotulos_linhas,
            notificar=False,
        )

        self.bind("<Button-1>", lambda e: self._pressionar(e, "auto"))
        self.bind("<B1-Motion>", self._arrastar)
        self.bind("<Button-3>", lambda e: self._pressionar(e, "remove"))
        self.bind("<B3-Motion>", self._arrastar)
        self.bind("<ButtonRelease-1>", self._soltar)
        self.bind("<ButtonRelease-3>", self._soltar)

    # ---------- configuração ----------

    def configurar(
        self,
        linhas,
        colunas,
        rotulos_linhas=None,
        notificar=True,
    ):
        """Configura a geometria visual da grade."""

        if isinstance(linhas, bool) or not isinstance(linhas, int) or linhas < 1:
            raise ValueError("Quantidade de linhas inválida.")

        if isinstance(colunas, bool) or not isinstance(colunas, int) or colunas < 1:
            raise ValueError("Quantidade de colunas inválida.")

        rotulos = list(rotulos_linhas or LETRAS_PADRAO[:linhas])

        if len(rotulos) != linhas:
            raise ValueError(
                "A quantidade de rótulos deve corresponder às linhas."
            )

        if (
            any(not isinstance(r, str) or not r.strip() for r in rotulos)
            or len(set(rotulos)) != len(rotulos)
        ):
            raise ValueError("Rótulos de linhas inválidos ou duplicados.")

        self.linhas = linhas
        self.colunas = colunas
        self.rotulos_linhas = [r.strip().upper() for r in rotulos]

        self._sel.clear()
        self._ids.clear()
        self._modo = None

        largura = self.MARGEM_E + colunas * self.tamanho + 6
        altura = self.MARGEM_T + linhas * self.tamanho + 6

        self.configure(width=largura, height=altura)
        self.delete("all")

        self._desenhar()

        if notificar:
            self._notificar()

    # ---------- desenho ----------

    def _desenhar(self):
        t = self.tamanho

        for c in range(self.colunas):
            self.create_text(
                self.MARGEM_E + c * t + t / 2,
                self.MARGEM_T / 2,
                text=str(c + 1),
                font=("Helvetica", 7),
            )

        for r in range(self.linhas):
            self.create_text(
                self.MARGEM_E / 2,
                self.MARGEM_T + r * t + t / 2,
                text=self.rotulos_linhas[r],
                font=("Helvetica", 9, "bold"),
            )

            for c in range(self.colunas):
                x0 = self.MARGEM_E + c * t
                y0 = self.MARGEM_T + r * t

                self._ids[(r, c)] = self.create_rectangle(
                    x0 + 1,
                    y0 + 1,
                    x0 + t - 1,
                    y0 + t - 1,
                    fill=COR_VAZIA,
                    outline=COR_BORDA,
                )

        # Origem da CNC: primeiro poço da última linha.
        self.itemconfig(
            self._ids[(self.linhas - 1, 0)],
            outline=COR_INICIO,
            width=3,
        )

    def _atualizar_cor(self, celula):
        cor = COR_SELECIONADO if celula in self._sel else COR_VAZIA
        self.itemconfig(self._ids[celula], fill=cor)

    # ---------- interação ----------

    def _celula_em(self, x, y):
        c = (x - self.MARGEM_E) // self.tamanho
        r = (y - self.MARGEM_T) // self.tamanho

        if 0 <= r < self.linhas and 0 <= c < self.colunas:
            return int(r), int(c)

        return None

    def _pressionar(self, evento, modo):
        x, y = evento.x, evento.y

        r = (y - self.MARGEM_T) // self.tamanho

        # Clique na letra da linha.
        if x < self.MARGEM_E and 0 <= r < self.linhas:
            self._modo = None
            self._alternar_grupo(
                [(int(r), c) for c in range(self.colunas)],
                modo,
            )
            return

        # Clique no número da coluna.
        c = (x - self.MARGEM_E) // self.tamanho

        if y < self.MARGEM_T and 0 <= c < self.colunas:
            self._modo = None
            self._alternar_grupo(
                [(r2, int(c)) for r2 in range(self.linhas)],
                modo,
            )
            return

        celula = self._celula_em(x, y)

        if celula is None:
            return

        if modo == "auto":
            self._modo = "remove" if celula in self._sel else "add"
        else:
            self._modo = modo

        self._aplicar(celula)
        self._notificar()

    def _arrastar(self, evento):
        celula = self._celula_em(evento.x, evento.y)

        if celula is not None and self._modo:
            self._aplicar(celula)
            self._notificar()

    def _soltar(self, _evento):
        self._modo = None

    def _aplicar(self, celula):
        if self._modo == "add":
            self._sel.add(celula)
        else:
            self._sel.discard(celula)

        self._atualizar_cor(celula)

    def _alternar_grupo(self, celulas, modo):
        if modo == "remove":
            adicionar = False
        else:
            adicionar = not all(c in self._sel for c in celulas)

        for celula in celulas:
            if adicionar:
                self._sel.add(celula)
            else:
                self._sel.discard(celula)

            self._atualizar_cor(celula)

        self._notificar()

    def _notificar(self):
        if self.ao_mudar:
            self.ao_mudar()

    # ---------- API pública ----------

    def selecionados(self):
        """Retorna os nomes dos poços selecionados."""
        return [
            f"{self.rotulos_linhas[r]}{c + 1}"
            for r, c in sorted(self._sel)
        ]

    def definir(self, pocos):
        """Substitui a seleção por uma lista de nomes de poços."""
        nova_selecao = set()

        for poco in pocos:
            nome = str(poco).strip().upper()

            rotulo = next(
                (
                    r for r in self.rotulos_linhas
                    if nome.startswith(r)
                ),
                None,
            )

            if rotulo is None:
                raise ValueError(f"Poço inválido: {poco}")

            numero = nome[len(rotulo):]

            if not numero.isdigit():
                raise ValueError(f"Poço inválido: {poco}")

            r = self.rotulos_linhas.index(rotulo)
            c = int(numero) - 1

            if not 0 <= c < self.colunas:
                raise ValueError(f"Poço fora da placa: {poco}")

            nova_selecao.add((r, c))

        self._sel = nova_selecao

        for celula in self._ids:
            self._atualizar_cor(celula)

        self._notificar()

    def limpar(self):
        self.definir([])

    def selecionar_tudo(self):
        self.definir([
            f"{self.rotulos_linhas[r]}{c + 1}"
            for r in range(self.linhas)
            for c in range(self.colunas)
        ])
