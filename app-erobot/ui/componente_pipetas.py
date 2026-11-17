
"""Seletor visual da configuração de pontas."""
import tkinter as tk
from tkinter import ttk


class SeletorPipetas(ttk.LabelFrame):
    """Seleciona e desenha a configuração de uma ou três pontas."""

    ESPACAMENTO_MM = 9.53
    ESCALA = 5
    OPCOES = (1, 3)

    def __init__(self, pai, quantidade_inicial=3):
        super().__init__(
            pai,
            text="Configuração da pipeta",
            padding=10,
        )

        if quantidade_inicial not in self.OPCOES:
            quantidade_inicial = 3

        self.quantidade = tk.StringVar(
            value=str(quantidade_inicial)
        )

        linha = ttk.Frame(self)
        linha.pack(fill="x")

        ttk.Label(
            linha,
            text="Quantidade de pontas:",
        ).pack(side="left")

        self.seletor = ttk.Combobox(
            linha,
            state="readonly",
            width=8,
            textvariable=self.quantidade,
            values=[str(n) for n in self.OPCOES],
        )
        self.seletor.pack(side="left", padx=(8, 0))

        ttk.Label(
            linha,
            text=f"Espaçamento: {self.ESPACAMENTO_MM:.2f} mm",
        ).pack(side="left", padx=12)

        area = ttk.Frame(self)
        area.pack(fill="x", pady=(12, 4))

        self.canvas = tk.Canvas(
            area,
            height=125,
            background="#f5f5f5",
            highlightthickness=1,
            highlightbackground="#cccccc",
        )

        barra = ttk.Scrollbar(
            area,
            orient="horizontal",
            command=self.canvas.xview,
        )

        self.canvas.configure(xscrollcommand=barra.set)
        self.canvas.pack(fill="x")
        barra.pack(fill="x")

        ttk.Label(
            self,
            text="A primeira ponta, à esquerda, define a referência XY.",
            foreground="gray",
        ).pack(anchor="w", pady=(4, 0))

        self.quantidade.trace_add(
            "write",
            lambda *_: self._atualizar_desenho(),
        )

        self._atualizar_desenho()

    def get_quantidade(self):
        try:
            valor = int(self.quantidade.get())
        except (ValueError, TypeError):
            raise ValueError("Selecione uma quantidade válida.")

        if valor not in self.OPCOES:
            raise ValueError("Selecione uma ou três pontas.")

        return valor

    def _atualizar_desenho(self):
        try:
            quantidade = self.get_quantidade()
        except ValueError:
            return

        self.canvas.delete("all")

        espacamento_px = (
            self.ESPACAMENTO_MM * self.ESCALA
        )

        margem = 35
        largura = (
            margem * 2
            + (quantidade - 1) * espacamento_px
            + 50
        )

        self.canvas.configure(
            scrollregion=(0, 0, largura, 125)
        )

        y_base = 85

        self.canvas.create_line(
            margem - 10,
            y_base,
            largura - 15,
            y_base,
            fill="#999999",
            dash=(3, 3),
        )

        for indice in range(quantidade):
            x = margem + indice * espacamento_px

            self.canvas.create_rectangle(
                x - 13, 15,
                x + 13, 55,
                fill="#dceeff",
                outline="#2878b5",
                width=2,
            )

            self.canvas.create_polygon(
                x - 9, 55,
                x + 9, 55,
                x + 3, 76,
                x - 3, 76,
                fill="#a8cbe8",
                outline="#2878b5",
            )

            self.canvas.create_oval(
                x - 3, 76,
                x + 3, 82,
                fill="#2878b5",
                outline="#2878b5",
            )

            self.canvas.create_text(
                x,
                7,
                text=str(indice + 1),
                fill="#222222",
                font=("Arial", 9, "bold"),
            )

        self.canvas.create_text(
            margem,
            103,
            text="Referência",
            fill="#2878b5",
            font=("Arial", 8, "bold"),
        )

        self.canvas.xview_moveto(0)
