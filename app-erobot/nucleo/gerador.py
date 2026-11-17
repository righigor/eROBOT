
"""Fluxo completo: seleção -> movimentos -> validação -> G-code + relatório."""

import hashlib
import json
import re
import unicodedata

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from nucleo.config import RAIZ, carregar
from nucleo.gcode import emitir
from nucleo.movimentos import montar_movimentos

from nucleo.movimentos_pipetagem import (
    agrupar_pocos,
    montar_movimentos_pipetagem,
    _obter_offsets_pontas,
)

from nucleo.ordem import ordenar_serpentina
from nucleo.seguranca import validar
from nucleo.versao import VERSAO


MAX_NOME = 16
PASTA_RELATORIOS = RAIZ / "saida" / "relatorios"


def _ascii(texto):
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode()
    )


def nome_valido(nome):
    return re.fullmatch(
        rf"[A-Za-z0-9_-]{{1,{MAX_NOME}}}",
        nome,
    ) is not None


def sugerir_nome(protocolo_nome, n_pocos, modo):
    base = (
        re.sub(
            r"[^A-Za-z0-9]",
            "",
            _ascii(protocolo_nome),
        ).upper()[:5]
        or "PROT"
    )

    return f"{base}_{n_pocos}P" + (
        "_T" if modo == "dry" else ""
    )


@dataclass
class Resultado:
    arquivo_nc: Path
    arquivo_relatorio: Path
    n_pocos: int
    n_linhas: int
    sha256: str


def gerar(
    protocolo_nome,
    pocos,
    modo,
    nome_arquivo,
    pasta_saida,
    sobrescrever=False,
    pipeta=None,
    placa=None,
    comentarios=None,
    pasta_relatorios=None,
    quantidade_pontas=1,
):
    """
    Gera o arquivo NC e seu relatório JSON.

    quantidade_pontas:
        1 = uma ponta.
        3 = pipetagem tripla.

    A geometria da placa e os offsets das pontas são
    obtidos das configurações TOML.
    """

    # --------------------------------------------------
    # 1. Validações iniciais
    # --------------------------------------------------

    if not pocos:
        raise ValueError("Nenhum poço selecionado.")

    if modo not in ("dry", "real"):
        raise ValueError(f"Modo inválido: {modo}")

    if quantidade_pontas not in (1, 3):
        raise ValueError(
            "Quantidade de pontas não suportada. "
            "Use 1 ou 3."
        )

    if not nome_valido(nome_arquivo):
        raise ValueError(
            f"Nome inválido: use só letras, números, _ e - "
            f"(máx. {MAX_NOME} caracteres, sem acentos)."
        )

    pasta = Path(pasta_saida)

    if not pasta.is_dir():
        raise ValueError(
            f"Pasta de saída não existe: {pasta}"
        )

    destino = pasta / f"{nome_arquivo}.nc"

    if destino.exists() and not sobrescrever:
        raise FileExistsError(
            f"Já existe: {destino}"
        )

    # --------------------------------------------------
    # 2. Carregar configurações
    # --------------------------------------------------

    pipeta = pipeta or carregar("pipeta")
    placa = placa or carregar("placa")

    geometria = pipeta["geometria"]

    orientacao = str(
        geometria.get("orientacao", "x")
    ).lower()

    if orientacao not in ("x", "y"):
        raise ValueError(
            "Orientação da pipeta inválida. "
            "Utilize 'x' ou 'y'."
        )

    if comentarios is None:
        comentarios = pipeta.get(
            "saida", {}
        ).get(
            "comentarios",
            False,
        )

    # --------------------------------------------------
    # 3. Obter offsets físicos
    # --------------------------------------------------

    offsets_pontas = _obter_offsets_pontas(
        pipeta,
        quantidade_pontas,
    )

    # --------------------------------------------------
    # 4. Agrupamento e movimentos
    # --------------------------------------------------

    if quantidade_pontas == 3:

        grupos = agrupar_pocos(
            pocos=pocos,
            placa=placa,
            pipeta=pipeta,
            quantidade_pontas=quantidade_pontas,
        )

        ordem = [
            poco
            for grupo in grupos
            for poco in grupo.pocos
        ]

        movs = montar_movimentos_pipetagem(
            grupos=grupos,
            modo=modo,
            pipeta=pipeta,
            placa=placa,
        )

        n_grupos = len(grupos)

    else:

        ordem = ordenar_serpentina(
            pocos,
            placa,
        )

        movs = montar_movimentos(
            ordem,
            modo,
            pipeta,
            placa,
        )

        n_grupos = len(ordem)

    # --------------------------------------------------
    # 5. Validação de segurança
    # --------------------------------------------------

    validar(
        movs=movs,
        modo=modo,
        pipeta=pipeta,
        placa=placa,
        offsets_pontas=offsets_pontas,
        orientacao_pontas=orientacao,
    )

    # --------------------------------------------------
    # 6. Cabeçalho do G-code
    # --------------------------------------------------

    agora = datetime.now()

    cabecalho = [
        f"eROBOT v{VERSAO}",
        f"protocolo: {_ascii(protocolo_nome)}",
        f"modo: {modo.upper()} | {len(ordem)} pocos",
        f"pontas: {quantidade_pontas}",
        f"orientacao: {orientacao.upper()}",
        f"grupos: {n_grupos}",
        f"gerado em {agora:%Y-%m-%d %H:%M}",
    ]

    if pipeta.get("provisorio", True):
        cabecalho.append(
            "PARAMETROS PROVISORIOS"
        )

    # --------------------------------------------------
    # 7. Emissão do G-code
    # --------------------------------------------------

    texto = emitir(
        movs,
        comentarios,
        cabecalho,
    )

    dados = texto.encode("ascii")

    # --------------------------------------------------
    # 8. Relatório de rastreabilidade
    # --------------------------------------------------

    sha = hashlib.sha256(dados).hexdigest()

    espacamento = (
        offsets_pontas[1] - offsets_pontas[0]
        if len(offsets_pontas) > 1
        else None
    )

    relatorio = {
        "arquivo": destino.name,
        "sha256": sha,
        "protocolo": protocolo_nome,
        "modo": modo,
        "quantidade_pontas": quantidade_pontas,
        "orientacao_pontas": orientacao,
        "offsets_pontas_mm": list(offsets_pontas),
        "espacamento_pontas_mm": espacamento,
        "n_grupos": n_grupos,
        "gerado_em": agora.isoformat(
            timespec="seconds"
        ),
        "versao_software": VERSAO,
        "n_pocos": len(ordem),
        "pocos_na_ordem": ordem,
        "parametros_provisorios": pipeta.get(
            "provisorio",
            True,
        ),
        "pipeta": pipeta,
        "placa": placa,
    }

    # --------------------------------------------------
    # 9. Preparar relatório
    # --------------------------------------------------

    pasta_rel = (
        Path(pasta_relatorios)
        if pasta_relatorios
        else PASTA_RELATORIOS
    )

    pasta_rel.mkdir(
        parents=True,
        exist_ok=True,
    )

    arq_rel = pasta_rel / (
        f"{nome_arquivo}_{agora:%Y%m%d-%H%M%S}.json"
    )

    # --------------------------------------------------
    # 10. Gravação dos arquivos
    # --------------------------------------------------

    # O G-code só é gravado depois da validação.
    destino.write_bytes(dados)

    arq_rel.write_text(
        json.dumps(
            relatorio,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return Resultado(
        destino,
        arq_rel,
        len(ordem),
        len(texto.splitlines()),
        sha,
    )
