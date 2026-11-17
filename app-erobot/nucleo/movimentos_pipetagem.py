
"""
Movimentos abstratos para pipetagem com múltiplas pontas fixas.

A geometria da placa e os offsets da pipeta são obtidos dos arquivos TOML.

Convenções:
- A ponta 1 é a referência XY.
- Os offsets das demais pontas são positivos.
- A orientação pode ser X ou Y.
- Os grupos precisam conter todos os poços atendidos simultaneamente.
- A ordem de execução utiliza serpentina.
"""

from dataclasses import dataclass
import math
import re

from nucleo.config import carregar
from nucleo.geometria import poco_para_xy
from nucleo.movimentos import MoverZ, MoverXY, Esperar, MODOS


TOLERANCIA_ESPACAMENTO_MM = 0.05


@dataclass(frozen=True)
class GrupoPipetagem:
    """Representa um posicionamento da pipeta sobre um grupo de poços."""

    pocos: tuple
    x: float
    y: float

    @property
    def rotulo(self):
        return " / ".join(self.pocos)


def _obter_rotulos_linhas(placa):
    """Obtém os rótulos das linhas, mantendo compatibilidade com placas antigas."""

    quantidade = int(placa["linhas"])

    rotulos = placa.get("rotulos_linhas")

    if rotulos is None:
        alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        if quantidade > len(alfabeto):
            raise ValueError(
                "Configure rotulos_linhas para placas com mais de 26 linhas."
            )

        rotulos = list(alfabeto[:quantidade])

    rotulos = [str(r).strip().upper() for r in rotulos]

    if len(rotulos) != quantidade:
        raise ValueError(
            "Quantidade de rótulos diferente da quantidade de linhas."
        )

    if len(set(rotulos)) != len(rotulos):
        raise ValueError("Existem rótulos de linhas duplicados.")

    if any(not re.fullmatch(r"[A-Z]+", r) for r in rotulos):
        raise ValueError("Existem rótulos de linhas inválidos.")

    return rotulos


def _obter_offsets_pontas(pipeta, quantidade_pontas):
    """
    Obtém os offsets físicos da pipeta.

    Formato atual do TOML:
        espacamento_pontas = 9.53

    Para três pontas, gera:
        [0.0, 9.53, 19.06]

    Também aceita uma lista explícita:
        offsets_pontas = [0.0, 8.40, 16.80]
    """

    if not isinstance(quantidade_pontas, int) or quantidade_pontas < 1:
        raise ValueError("A quantidade de pontas deve ser um inteiro positivo.")

    geometria = pipeta["geometria"]

    offsets = geometria.get("offsets_pontas")

    if offsets is not None:
        offsets = tuple(float(v) for v in offsets)

        if len(offsets) != quantidade_pontas:
            raise ValueError(
                "A quantidade de offsets configurada não corresponde "
                "à quantidade de pontas selecionada."
            )
    elif quantidade_pontas == 1:
        offsets = (0.0,)
    else:
        espacamento = float(geometria["espacamento_pontas"])

        if not math.isfinite(espacamento) or espacamento <= 0:
            raise ValueError("Espaçamento das pontas inválido.")

        offsets = tuple(
            indice * espacamento
            for indice in range(quantidade_pontas)
        )

    if not all(math.isfinite(v) for v in offsets):
        raise ValueError("Existem offsets não finitos.")

    if abs(offsets[0]) > TOLERANCIA_ESPACAMENTO_MM:
        raise ValueError("O offset da primeira ponta deve ser zero.")

    if any(
        offsets[i] <= offsets[i - 1]
        for i in range(1, len(offsets))
    ):
        raise ValueError(
            "Os offsets devem ser crescentes e não podem se repetir."
        )

    return offsets


def _validar_compatibilidade_geometrica(
    placa,
    pipeta,
    offsets,
):
    """
    Verifica se os offsets da pipeta correspondem ao passo da placa.
    """

    geometria = pipeta["geometria"]

    orientacao = str(
        geometria.get("orientacao", "x")
    ).lower()

    if orientacao not in ("x", "y"):
        raise ValueError(
            "Orientação da pipeta inválida. Utilize 'x' ou 'y'."
        )

    passo = float(
        placa["passo_x"] if orientacao == "x"
        else placa["passo_y"]
    )

    if not math.isfinite(passo) or passo <= 0:
        raise ValueError("Passo da placa inválido.")

    for indice, offset in enumerate(offsets):
        esperado = indice * passo

        if abs(offset - esperado) > TOLERANCIA_ESPACAMENTO_MM:
            raise ValueError(
                f"Pipeta incompatível com a placa na orientação "
                f"{orientacao.upper()}.\n"
                f"Ponta {indice + 1}: offset físico de "
                f"{offset:.3f} mm.\n"
                f"Offset necessário: {esperado:.3f} mm.\n"
                f"Passo da placa: {passo:.3f} mm."
            )

    return orientacao


def agrupar_pocos(
    pocos,
    placa=None,
    pipeta=None,
    quantidade_pontas=1,
):
    """
    Agrupa poços de acordo com a geometria da placa e da pipeta.

    Args:
        pocos: Identificadores dos poços selecionados.
        placa: Configuração da placa.
        pipeta: Configuração física da pipeta.
        quantidade_pontas: Quantidade de pontas utilizadas.

    Returns:
        Lista de GrupoPipetagem ordenada em serpentina.
    """

    placa = placa or carregar("placa")
    pipeta = pipeta or carregar("pipeta")

    if not pocos:
        raise ValueError("Nenhum poço selecionado.")

    offsets = _obter_offsets_pontas(
        pipeta,
        quantidade_pontas,
    )

    orientacao = _validar_compatibilidade_geometrica(
        placa,
        pipeta,
        offsets,
    )

    linhas = _obter_rotulos_linhas(placa)
    colunas_total = int(placa["colunas"])
    linhas_total = int(placa["linhas"])

    selecionados = [
        str(p).strip().upper()
        for p in pocos
    ]

    if len(set(selecionados)) != len(selecionados):
        raise ValueError("A seleção contém poços duplicados.")

    # Mapeia cada poço para sua posição lógica.
    # O índice físico da linha cresce de baixo para cima.
    posicoes = {}

    for poco in selecionados:
        correspondencia = re.fullmatch(
            r"([A-Z]+)(\d+)",
            poco,
        )

        if not correspondencia:
            raise ValueError(f"Nome de poço inválido: {poco}")

        letra, numero_texto = correspondencia.groups()
        numero = int(numero_texto)

        if letra not in linhas:
            raise ValueError(f"Linha inválida: {poco}")

        if not 1 <= numero <= colunas_total:
            raise ValueError(f"Poço fora da placa: {poco}")

        x, y = poco_para_xy(poco, placa)

        indice_linha = linhas.index(letra)
        indice_y = linhas_total - 1 - indice_linha
        indice_x = numero - 1

        posicoes[poco] = {
            "x": x,
            "y": y,
            "indice_x": indice_x,
            "indice_y": indice_y,
        }

    # Define o eixo em que a pipeta trabalha.
    if orientacao == "x":
        tamanho_eixo = colunas_total
        indice_eixo = "indice_x"
        indice_linha = "indice_y"
    else:
        tamanho_eixo = linhas_total
        indice_eixo = "indice_y"
        indice_linha = "indice_x"

    # Impede grupos que ultrapassem os limites da placa.
    if tamanho_eixo % quantidade_pontas != 0:
        raise ValueError(
            f"A dimensão da placa na orientação {orientacao.upper()} "
            f"({tamanho_eixo}) não é divisível pela quantidade "
            f"de pontas ({quantidade_pontas})."
        )

    grupos_por_bloco = {}

    for poco, posicao in posicoes.items():
        indice = posicao[indice_eixo]

        inicio = (
            indice // quantidade_pontas
        ) * quantidade_pontas

        linha_oposta = posicao[indice_linha]

        chave = (linha_oposta, inicio)

        grupos_por_bloco.setdefault(
            chave,
            set(),
        ).add(poco)

    grupos = []

    for (linha_oposta, inicio), selecionados_bloco in grupos_por_bloco.items():

        esperados = []

        for deslocamento in range(quantidade_pontas):
            indice = inicio + deslocamento

            if orientacao == "x":
                indice_x = indice
                indice_y = linha_oposta
            else:
                indice_x = linha_oposta
                indice_y = indice

            indice_rotulo = linhas_total - 1 - indice_y

            letra = linhas[indice_rotulo]
            coluna = indice_x + 1

            esperados.append(f"{letra}{coluna}")

        esperados = tuple(esperados)

        if selecionados_bloco != set(esperados):
            faltantes = sorted(
                set(esperados) - selecionados_bloco
            )

            raise ValueError(
                f"Grupo incompleto ({', '.join(esperados)}). "
                f"Poços faltantes: {', '.join(faltantes)}."
            )

        x, y = poco_para_xy(esperados[0], placa)

        grupos.append(
            GrupoPipetagem(
                pocos=esperados,
                x=float(x),
                y=float(y),
            )
        )

    # Ordenação serpentina.
    grupos_ordenados = []

    linhas_fisicas = sorted({
        grupo.y if orientacao == "x" else grupo.x
        for grupo in grupos
    })

    for indice_linha, coordenada in enumerate(linhas_fisicas):

        if orientacao == "x":
            grupos_linha = [
                grupo for grupo in grupos
                if abs(grupo.y - coordenada) < 1e-6
            ]

            grupos_linha.sort(key=lambda grupo: grupo.x)

        else:
            grupos_linha = [
                grupo for grupo in grupos
                if abs(grupo.x - coordenada) < 1e-6
            ]

            grupos_linha.sort(key=lambda grupo: grupo.y)

        if indice_linha % 2 == 1:
            grupos_linha.reverse()

        grupos_ordenados.extend(grupos_linha)

    return grupos_ordenados


def agrupar_pocos_tripla(pocos, placa=None, pipeta=None):
    """
    Compatibilidade com chamadas antigas.

    Continua permitindo que a interface antiga utilize
    agrupar_pocos_tripla(), mas delega a lógica para agrupar_pocos().
    """

    return agrupar_pocos(
        pocos=pocos,
        placa=placa,
        pipeta=pipeta,
        quantidade_pontas=3,
    )


def montar_movimentos_pipetagem(
    grupos,
    modo,
    pipeta=None,
    placa=None,
):
    """
    Transforma grupos de poços em movimentos abstratos.

    Os movimentos são independentes da geração do G-code.
    """

    if modo not in MODOS:
        raise ValueError(f"Modo inválido: {modo}")

    if not grupos:
        raise ValueError(
            "Nenhum grupo de pipetagem foi informado."
        )

    pipeta = pipeta or carregar("pipeta")

    geometria = pipeta["geometria"]

    z_park = float(geometria["z_park"])
    z_safe = float(geometria["z_safe"])
    z_aprox = float(geometria["z_aprox"])
    feed_z = float(geometria["feed_z"])

    espera = float(
        geometria.get("espera_no_poco", 0.0)
    )

    z_alvo = float(
        geometria["z_descida_poco"]
        if modo == "real"
        else geometria["z_dry"]
    )

    parametros = (
        z_park,
        z_safe,
        z_aprox,
        feed_z,
        espera,
        z_alvo,
    )

    if not all(math.isfinite(v) for v in parametros):
        raise ValueError("Existem parâmetros Z inválidos na pipeta.")

    if z_park < z_safe or z_safe < z_aprox:
        raise ValueError(
            "Configuração Z inválida: "
            "esperado Z_PARK >= Z_SAFE >= Z_APROX."
        )

    if feed_z <= 0:
        raise ValueError("FEED_Z deve ser maior que zero.")

    if espera < 0:
        raise ValueError("A espera no poço não pode ser negativa.")

    movimentos = [
        MoverZ(z_park)
    ]

    for grupo in grupos:

        movimentos.append(
            MoverZ(z_safe)
        )

        movimentos.append(
            MoverXY(
                grupo.x,
                grupo.y,
                grupo.rotulo,
            )
        )

        if z_alvo < z_aprox:
            movimentos.append(
                MoverZ(z_aprox)
            )

        movimentos.append(
            MoverZ(z_alvo, feed_z)
        )

        if espera > 0:
            movimentos.append(
                Esperar(espera)
            )

        movimentos.append(
            MoverZ(z_safe)
        )

    movimentos.append(
        MoverZ(z_park)
    )

    # Origem atual da máquina: centro do poço H1.
    movimentos.append(
        MoverXY(0.0, 0.0, "origem")
    )

    return movimentos
