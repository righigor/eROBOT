import copy
import hashlib
import json
import pytest
from nucleo.config import carregar
from nucleo.gerador import gerar, nome_valido, sugerir_nome
from nucleo.seguranca import ErroSeguranca

POCOS = ["H1", "H2", "G2", "G1"]


def test_gera_nc_e_relatorio(tmp_path):
    res = gerar("ELISA básico", POCOS, "dry", "ELISA_4P_T", tmp_path / "pen"
                if False else tmp_path, pasta_relatorios=tmp_path / "rel")
    dados = res.arquivo_nc.read_bytes()
    dados.decode("ascii")
    assert hashlib.sha256(dados).hexdigest() == res.sha256
    rel = json.loads(res.arquivo_relatorio.read_text(encoding="utf-8"))
    assert rel["sha256"] == res.sha256
    assert rel["pocos_na_ordem"] == POCOS
    assert rel["modo"] == "dry" and rel["parametros_provisorios"] is True
    assert res.arquivo_relatorio.parent == tmp_path / "rel"


def test_real_bloqueado_nao_cria_arquivo(tmp_path):
    with pytest.raises(ErroSeguranca):
        gerar("X", POCOS, "real", "X_4P", tmp_path, pasta_relatorios=tmp_path / "rel")
    assert not list(tmp_path.glob("*.nc"))


def test_nao_sobrescreve_sem_permissao(tmp_path):
    gerar("X", POCOS, "dry", "X_4P_T", tmp_path, pasta_relatorios=tmp_path / "rel")
    with pytest.raises(FileExistsError):
        gerar("X", POCOS, "dry", "X_4P_T", tmp_path, pasta_relatorios=tmp_path / "rel")
    gerar("X", POCOS, "dry", "X_4P_T", tmp_path, sobrescrever=True,
          pasta_relatorios=tmp_path / "rel")


def test_sem_pocos_e_pasta_inexistente(tmp_path):
    with pytest.raises(ValueError):
        gerar("X", [], "dry", "X", tmp_path)
    with pytest.raises(ValueError):
        gerar("X", POCOS, "dry", "X", tmp_path / "nao_existe")


@pytest.mark.parametrize("nome,ok", [("ELISA_16P", True), ("ELISA 16P", False),
                                     ("ELISÁ", False), ("", False),
                                     ("A" * 17, False), ("A" * 16, True)])
def test_nome_valido(nome, ok):
    assert nome_valido(nome) is ok


def test_sugestao_de_nome():
    assert sugerir_nome("ELISA básico", 16, "real") == "ELISA_16P"
    assert sugerir_nome("ELISA básico", 16, "dry") == "ELISA_16P_T"
    assert nome_valido(sugerir_nome("Protocolo Açaí", 168, "dry"))
