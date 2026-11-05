"""Fluxo completo: poços escolhidos -> ordem -> movimentos -> validação ->
.nc (pendrive) + relatório (.json, fica no PC). Sem Tkinter."""
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
from nucleo.ordem import ordenar_serpentina
from nucleo.seguranca import validar
from nucleo.versao import VERSAO

MAX_NOME = 16   # palpite: ajustar depois de testar o limite real do A11
PASTA_RELATORIOS = RAIZ / "saida" / "relatorios"


def _ascii(texto):
    """Remove acentos (para comentários e nomes)."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def nome_valido(nome):
    """Curto, sem acentos, sem espaços: só letras, números, '_' e '-'."""
    return re.fullmatch(rf"[A-Za-z0-9_-]{{1,{MAX_NOME}}}", nome) is not None


def sugerir_nome(protocolo_nome, n_pocos, modo):
    """Ex.: 'ELISA_16P' (real) ou 'ELISA_16P_T' (teste no ar)."""
    base = re.sub(r"[^A-Za-z0-9]", "", _ascii(protocolo_nome)).upper()[:5] or "PROT"
    return f"{base}_{n_pocos}P" + ("_T" if modo == "dry" else "")


@dataclass
class Resultado:
    arquivo_nc: Path
    arquivo_relatorio: Path
    n_pocos: int
    n_linhas: int
    sha256: str


def gerar(protocolo_nome, pocos, modo, nome_arquivo, pasta_saida,
          sobrescrever=False, pipeta=None, placa=None,
          comentarios=None, pasta_relatorios=None):
    """Gera o .nc na pasta de saída (pendrive) e o relatório no PC."""
    if not pocos:
        raise ValueError("Nenhum poço selecionado.")
    if not nome_valido(nome_arquivo):
        raise ValueError(f"Nome inválido: use só letras, números, _ e - "
                         f"(máx. {MAX_NOME} caracteres, sem acentos).")
    pasta = Path(pasta_saida)
    if not pasta.is_dir():
        raise ValueError(f"Pasta de saída não existe: {pasta}")
    destino = pasta / f"{nome_arquivo}.nc"
    if destino.exists() and not sobrescrever:
        raise FileExistsError(f"Já existe: {destino}")

    pipeta = pipeta or carregar("pipeta")
    placa = placa or carregar("placa")
    if comentarios is None:
        comentarios = pipeta.get("saida", {}).get("comentarios", False)

    ordem = ordenar_serpentina(pocos, placa)
    movs = montar_movimentos(ordem, modo, pipeta, placa)
    validar(movs, modo, pipeta, placa)          # levanta ErroSeguranca se inseguro

    agora = datetime.now()
    cabecalho = [f"eROBOT v{VERSAO}", f"protocolo: {_ascii(protocolo_nome)}",
                 f"modo: {modo.upper()} | {len(ordem)} pocos",
                 f"gerado em {agora:%Y-%m-%d %H:%M}"]
    if pipeta.get("provisorio", True):
        cabecalho.append("PARAMETROS PROVISORIOS")
    texto = emitir(movs, comentarios, cabecalho)
    dados = texto.encode("ascii")

    destino.write_bytes(dados)
    sha = hashlib.sha256(dados).hexdigest()

    relatorio = {
        "arquivo": destino.name, "sha256": sha, "protocolo": protocolo_nome,
        "modo": modo, "gerado_em": agora.isoformat(timespec="seconds"),
        "versao_software": VERSAO, "n_pocos": len(ordem), "pocos_na_ordem": ordem,
        "parametros_provisorios": pipeta.get("provisorio", True),
        "pipeta": pipeta, "placa": placa,
    }
    pasta_rel = Path(pasta_relatorios) if pasta_relatorios else PASTA_RELATORIOS
    pasta_rel.mkdir(parents=True, exist_ok=True)
    arq_rel = pasta_rel / f"{nome_arquivo}_{agora:%Y%m%d-%H%M%S}.json"
    arq_rel.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False), encoding="utf-8")

    return Resultado(destino, arq_rel, len(ordem), len(texto.splitlines()), sha)
