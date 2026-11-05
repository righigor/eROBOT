"""Janela principal: empilha as telas e troca entre elas."""
import tkinter as tk
from ui.tela_inicial import TelaInicial
from ui.tela_protocolos import TelaProtocolos
from ui.tela_detalhe_protocolo import TelaDetalheProtocolo
from ui.tela_resultados import TelaResultados

NOME_APP = "eROBOT"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(NOME_APP)
        self.geometry("660x660")

        self.telas = {
            "inicial": TelaInicial(self, self.ir_para),
            "protocolos": TelaProtocolos(self, self.ir_para, self.abrir_detalhe),
            "detalhe": TelaDetalheProtocolo(self, self.ir_para),
            "resultados": TelaResultados(self, self.ir_para),
        }
        for tela in self.telas.values():
            tela.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.ir_para("inicial")

    def ir_para(self, nome: str):
        """Traz a tela desejada para a frente."""
        self.telas[nome].tkraise()

    def abrir_detalhe(self, protocolo):
        """Carrega o protocolo na tela de detalhe e a exibe."""
        self.telas["detalhe"].carregar(protocolo)
        self.ir_para("detalhe")
