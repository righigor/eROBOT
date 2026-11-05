"""Grade clicável da placa de poços (8 x 21). Só desenha e seleciona;
não conhece G-code.

Interação:
  - clique / arrastar com botão esquerdo: seleciona (ou desmarca, se começar
    em um poço já selecionado)
  - botão direito (clicar/arrastar): desmarca
  - clicar na letra de uma linha ou no número de uma coluna: alterna a linha/coluna
"""
import tkinter as tk

LETRAS = "ABCDEFGH"
COR_VAZIA = "#f0f0f0"
COR_SELECIONADO = "#2e86de"
COR_BORDA = "#888888"
COR_INICIO = "#e67e22"      # contorno do poço H1 (origem da CNC)


class GradePlaca(tk.Canvas):
    MARGEM_E = 26   # espaço das letras (esquerda)
    MARGEM_T = 22   # espaço dos números (topo)

    def __init__(self, pai, linhas=8, colunas=21, tamanho=22, ao_mudar=None):
        self.linhas = linhas
        self.colunas = colunas
        self.tamanho = tamanho
        self.ao_mudar = ao_mudar
        largura = self.MARGEM_E + colunas * tamanho + 6
        altura = self.MARGEM_T + linhas * tamanho + 6
        super().__init__(pai, width=largura, height=altura, highlightthickness=0)

        self._sel = set()        # {(linha, coluna)}, linha 0 = A (topo)
        self._ids = {}           # (linha, coluna) -> id do retângulo
        self._modo = None        # "add" ou "remove" durante o arrasto
        self._desenhar()

        self.bind("<Button-1>", lambda e: self._pressionar(e, "auto"))
        self.bind("<B1-Motion>", self._arrastar)
        self.bind("<Button-3>", lambda e: self._pressionar(e, "remove"))
        self.bind("<B3-Motion>", self._arrastar)
        self.bind("<ButtonRelease-1>", self._soltar)
        self.bind("<ButtonRelease-3>", self._soltar)

    # ---------- desenho ----------
    def _desenhar(self):
        t = self.tamanho
        for c in range(self.colunas):
            self.create_text(self.MARGEM_E + c * t + t / 2, self.MARGEM_T / 2,
                             text=str(c + 1), font=("Helvetica", 7))
        for r in range(self.linhas):
            self.create_text(self.MARGEM_E / 2, self.MARGEM_T + r * t + t / 2,
                             text=LETRAS[r], font=("Helvetica", 9, "bold"))
            for c in range(self.colunas):
                x0 = self.MARGEM_E + c * t
                y0 = self.MARGEM_T + r * t
                self._ids[(r, c)] = self.create_rectangle(
                    x0 + 1, y0 + 1, x0 + t - 1, y0 + t - 1,
                    fill=COR_VAZIA, outline=COR_BORDA)
        # Destaca H1 (canto inferior esquerdo): onde a CNC começa
        self.itemconfig(self._ids[(self.linhas - 1, 0)], outline=COR_INICIO, width=3)

    def _atualizar_cor(self, celula):
        cor = COR_SELECIONADO if celula in self._sel else COR_VAZIA
        self.itemconfig(self._ids[celula], fill=cor)

    # ---------- interação ----------
    def _celula_em(self, x, y):
        c = (x - self.MARGEM_E) // self.tamanho
        r = (y - self.MARGEM_T) // self.tamanho
        if 0 <= r < self.linhas and 0 <= c < self.colunas:
            return (int(r), int(c))
        return None

    def _pressionar(self, evento, modo):
        x, y = evento.x, evento.y
        # Clique na letra de uma linha
        r = (y - self.MARGEM_T) // self.tamanho
        if x < self.MARGEM_E and 0 <= r < self.linhas:
            self._alternar_grupo([(int(r), c) for c in range(self.colunas)], modo)
            return
        # Clique no número de uma coluna
        c = (x - self.MARGEM_E) // self.tamanho
        if y < self.MARGEM_T and 0 <= c < self.colunas:
            self._alternar_grupo([(r2, int(c)) for r2 in range(self.linhas)], modo)
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
        """Nomes dos poços selecionados (ex.: ['A1', 'A2']), de cima para baixo."""
        return [f"{LETRAS[r]}{c + 1}" for r, c in sorted(self._sel)]

    def definir(self, pocos):
        """Substitui a seleção por uma lista de nomes de poços."""
        self._sel = {(LETRAS.index(p[0].upper()), int(p[1:]) - 1) for p in pocos}
        for celula in self._ids:
            self._atualizar_cor(celula)
        self._notificar()

    def limpar(self):
        self.definir([])

    def selecionar_tudo(self):
        self.definir([f"{LETRAS[r]}{c + 1}"
                      for r in range(self.linhas) for c in range(self.colunas)])
