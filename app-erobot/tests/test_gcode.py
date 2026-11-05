import copy
import pytest
from nucleo.config import carregar
from nucleo.gcode import emitir
from nucleo.movimentos import MoverXY, MoverZ, montar_movimentos
from nucleo.seguranca import ErroSeguranca, validar

POCOS = ["H1", "H2", "G2", "G1"]
PERMITIDOS = {"G0", "G1", "G4", "G17", "G21", "G90", "M5", "M30"}


@pytest.fixture
def pipeta():
    return copy.deepcopy(carregar("pipeta"))


@pytest.fixture
def placa():
    return copy.deepcopy(carregar("placa"))


def gerar_texto(modo, pipeta, placa, comentarios=False):
    movs = montar_movimentos(POCOS, modo, pipeta, placa)
    validar(movs, modo, pipeta, placa)
    return emitir(movs, comentarios, ["teste"])


def test_so_comandos_permitidos(pipeta, placa):
    texto = gerar_texto("dry", pipeta, placa)
    for linha in texto.split("\r\n"):
        if linha:
            assert linha.split()[0] in PERMITIDOS, linha


def test_ascii_e_crlf(pipeta, placa):
    texto = gerar_texto("dry", pipeta, placa, comentarios=True)
    texto.encode("ascii")
    assert texto.endswith("\r\n")
    assert "\n" not in texto.replace("\r\n", "")


def test_comeca_e_termina_com_m5(pipeta, placa):
    linhas = gerar_texto("dry", pipeta, placa).split("\r\n")[:-1]
    assert linhas[:4] == ["G21", "G90", "G17", "M5"]
    assert linhas[-2:] == ["M5", "M30"]
    assert linhas[-3] == "G0 X0.000 Y0.000"      # volta à origem
    assert linhas[-4] == "G0 Z35.000"            # com Z_PARK


def test_primeiro_poco_e_h1_e_serpentina(pipeta, placa):
    texto = gerar_texto("dry", pipeta, placa)
    xy = [l for l in texto.split("\r\n") if l.startswith("G0 X")]
    assert xy[:4] == ["G0 X0.000 Y0.000", "G0 X9.530 Y0.000",
                      "G0 X9.530 Y33.720", "G0 X0.000 Y33.720"]


def test_dry_nunca_abaixo_da_folha(pipeta, placa):
    texto = gerar_texto("dry", pipeta, placa)
    zs = [float(l.split("Z")[1].split()[0]) for l in texto.split("\r\n") if " Z" in l]
    assert min(zs) > 0


def test_espera_no_poco(pipeta, placa):
    pipeta["espera_no_poco"] = 1.5
    texto = gerar_texto("dry", pipeta, placa)
    assert texto.count("G4 P1.5") == len(POCOS)


def test_real_bloqueado_com_parametros_provisorios(pipeta, placa):
    assert pipeta["provisorio"] is True
    movs = montar_movimentos(POCOS, "real", pipeta, placa)
    with pytest.raises(ErroSeguranca, match="provis"):
        validar(movs, "real", pipeta, placa)


def test_real_liberado_quando_nao_provisorio(pipeta, placa):
    pipeta["provisorio"] = False
    movs = montar_movimentos(POCOS, "real", pipeta, placa)
    validar(movs, "real", pipeta, placa)


def test_real_recusa_fundo_do_poco(pipeta, placa):
    pipeta["provisorio"] = False
    pipeta["z_descida_poco"] = -placa["profundidade_poco"]
    movs = montar_movimentos(POCOS, "real", pipeta, placa)
    with pytest.raises(ErroSeguranca, match="abaixo do limite"):
        validar(movs, "real", pipeta, placa)


def test_xy_com_z_baixo_e_recusado(pipeta, placa):
    movs = [MoverZ(35.0), MoverZ(1.0), MoverXY(10.0, 10.0, "X")]
    with pytest.raises(ErroSeguranca, match="Z seguro"):
        validar(movs, "dry", pipeta, placa)


def test_xy_sem_z_definido_e_recusado(pipeta, placa):
    with pytest.raises(ErroSeguranca, match="Z seguro"):
        validar([MoverXY(0.0, 0.0, "X")], "dry", pipeta, placa)


def test_fora_do_curso(pipeta, placa):
    placa["passo_y"] = 100.0          # A1 iria para Y = 700 mm
    movs = montar_movimentos(["A1"], "dry", pipeta, placa)
    with pytest.raises(ErroSeguranca, match="fora do curso"):
        validar(movs, "dry", pipeta, placa)


def test_alturas_incoerentes(pipeta, placa):
    pipeta["z_safe"] = 50.0           # acima do z_park
    movs = montar_movimentos(POCOS, "dry", pipeta, placa)
    with pytest.raises(ErroSeguranca, match="incoerentes"):
        validar(movs, "dry", pipeta, placa)
