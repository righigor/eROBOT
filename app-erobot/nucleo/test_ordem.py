import pytest
from nucleo.ordem import ordenar_serpentina


def test_comeca_em_h1_e_sobe():
    assert ordenar_serpentina(["A1", "H3", "H1", "G2", "G5"]) == ["H1", "H3", "G5", "G2", "A1"]


def test_serpentina_alterna_sentido():
    # H (indice 0) sobe 1->21; G (indice 1) volta 21->1
    assert ordenar_serpentina(["G1", "G2", "H1", "H2"]) == ["H1", "H2", "G2", "G1"]


def test_duas_linhas_de_cima():
    assert ordenar_serpentina(["A1", "A2", "B1"]) == ["B1", "A2", "A1"]


def test_poco_invalido():
    with pytest.raises(ValueError):
        ordenar_serpentina(["Z1"])
