import pytest
from nucleo.geometria import poco_para_xy


def test_h1_e_a_origem():
    assert poco_para_xy("H1") == (0.0, 0.0)


def test_a1_e_h21():
    assert poco_para_xy("A1") == (0.0, 236.04)     # 7 * 33,72
    assert poco_para_xy("H21") == (190.6, 0.0)     # 20 * 9,53


def test_poco_invalido():
    with pytest.raises(ValueError):
        poco_para_xy("Z9")
