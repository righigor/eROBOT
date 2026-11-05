from nucleo.protocolos import listar_protocolos


def test_lista_protocolo_exemplo():
    nomes = [p.nome for p in listar_protocolos()]
    assert "ELISA básico" in nomes
