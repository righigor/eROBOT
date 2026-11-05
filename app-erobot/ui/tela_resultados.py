from tkinter import ttk


class TelaResultados(ttk.Frame):
    """Movimento até a posição de leitura óptica (placeholder)."""

    def __init__(self, pai, ir_para):
        super().__init__(pai, padding=40)
        ttk.Label(self, text="Coletar Resultados", font=("Helvetica", 20, "bold")).pack(pady=20)
        ttk.Label(self, text="Em desenvolvimento.", foreground="gray").pack()
        ttk.Button(self, text="Voltar",
                   command=lambda: ir_para("inicial")).pack(pady=20)
