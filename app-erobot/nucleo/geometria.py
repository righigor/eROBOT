
"""
Conversão de identificadores de poços em coordenadas da máquina.

A geometria é carregada a partir de um arquivo TOML.

Convenção:
- A primeira linha é a linha superior da placa.
- A última linha é a linha de referência Y = 0.
- A primeira coluna é a coluna de referência X = 0.
- O espaçamento X e Y é configurável independentemente.

Exemplo:
    H1 -> (0.0, 0.0)
"""

import re

from nucleo.config import carregar


def poco_para_xy(
    poco: str,
    placa: dict | None = None
) -> tuple[float, float]:
    """
    Converte o identificador de um poço em coordenadas XY.

    Args:
        poco: Identificador do poço (ex.: A1, H12, C7).
        placa: Dicionário de configuração da placa.
               Se omitido, carrega config/placa.toml.

    Returns:
        Tupla (x, y), em milímetros.

    Raises:
        ValueError: Se o identificador ou a configuração forem inválidos.
    """

    if placa is None:
        placa = carregar("placa")

    # --------------------------------------------------
    # 1. Validar configuração básica
    # --------------------------------------------------

    try:
        quantidade_linhas = int(placa["linhas"])
        quantidade_colunas = int(placa["colunas"])
        passo_x = float(placa["passo_x"])
        passo_y = float(placa["passo_y"])
    except (KeyError, TypeError, ValueError) as erro:
        raise ValueError(
            f"Configuração da placa incompleta ou inválida: {erro}"
        ) from erro

    if quantidade_linhas <= 0 or quantidade_colunas <= 0:
        raise ValueError("A quantidade de linhas e colunas deve ser positiva.")

    if passo_x <= 0 or passo_y <= 0:
        raise ValueError("Os passos X e Y devem ser maiores que zero.")

    # --------------------------------------------------
    # 2. Obter rótulos das linhas
    # --------------------------------------------------

    rotulos = placa.get("rotulos_linhas")

    if rotulos is None:
        # Compatibilidade com configurações antigas.
        # Exemplo: 8 linhas -> A, B, C, D, E, F, G, H.
        alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        if quantidade_linhas > len(alfabeto):
            raise ValueError(
                "A placa possui mais de 26 linhas. "
                "Configure rotulos_linhas explicitamente no TOML."
            )

        rotulos = list(alfabeto[:quantidade_linhas])

    if not isinstance(rotulos, (list, tuple)):
        raise ValueError("rotulos_linhas deve ser uma lista.")

    rotulos = [str(rotulo).strip().upper() for rotulo in rotulos]

    if len(rotulos) != quantidade_linhas:
        raise ValueError(
            "A quantidade de rótulos de linhas não corresponde "
            "à quantidade de linhas configurada."
        )

    if any(not re.fullmatch(r"[A-Z]+", rotulo) for rotulo in rotulos):
        raise ValueError("Os rótulos devem conter somente letras de A a Z.")

    if len(set(rotulos)) != len(rotulos):
        raise ValueError("Existem rótulos de linhas duplicados.")

    # --------------------------------------------------
    # 3. Interpretar identificador do poço
    # --------------------------------------------------

    identificador = str(poco).strip().upper()

    correspondencia = re.fullmatch(
        r"([A-Z]+)(\d+)",
        identificador
    )

    if not correspondencia:
        raise ValueError(
            f"Identificador de poço inválido: {poco!r}. "
            "Exemplo válido: A1 ou H12."
        )

    letra, numero_texto = correspondencia.groups()
    numero_coluna = int(numero_texto)

    # --------------------------------------------------
    # 4. Validar linha e coluna
    # --------------------------------------------------

    if letra not in rotulos:
        raise ValueError(
            f"Linha '{letra}' não existe na placa configurada."
        )

    if not 1 <= numero_coluna <= quantidade_colunas:
        raise ValueError(
            f"Coluna {numero_coluna} fora dos limites da placa. "
            f"Colunas válidas: 1 a {quantidade_colunas}."
        )

    # --------------------------------------------------
    # 5. Calcular coordenadas
    # --------------------------------------------------

    indice_linha = rotulos.index(letra)

    # A primeira linha fica no topo.
    # A última linha é a referência Y = 0.
    indice_y = quantidade_linhas - 1 - indice_linha

    indice_x = numero_coluna - 1

    x = indice_x * passo_x
    y = indice_y * passo_y

    return round(x, 3), round(y, 3)


def xy_para_poco(
    x: float,
    y: float,
    placa: dict | None = None,
    tolerancia: float = 0.05
) -> str:
    """
    Converte coordenadas XY no identificador do poço mais próximo.

    A conversão só é aceita se a coordenada estiver dentro da
    tolerância definida em relação ao centro de um poço.

    Args:
        x: Coordenada X em milímetros.
        y: Coordenada Y em milímetros.
        placa: Configuração da placa. Se omitida, carrega a padrão.
        tolerancia: Distância máxima permitida ao centro do poço.

    Returns:
        Identificador do poço, por exemplo H1 ou A12.

    Raises:
        ValueError: Se a coordenada não corresponder a um poço.
    """

    if placa is None:
        placa = carregar("placa")

    try:
        quantidade_linhas = int(placa["linhas"])
        quantidade_colunas = int(placa["colunas"])
        passo_x = float(placa["passo_x"])
        passo_y = float(placa["passo_y"])
        x = float(x)
        y = float(y)
        tolerancia = float(tolerancia)
    except (KeyError, TypeError, ValueError) as erro:
        raise ValueError(
            f"Coordenadas ou configuração inválidas: {erro}"
        ) from erro

    import math

    if not all(math.isfinite(v) for v in (x, y, passo_x, passo_y, tolerancia)):
        raise ValueError("As coordenadas e parâmetros devem ser finitos.")

    if quantidade_linhas <= 0 or quantidade_colunas <= 0:
        raise ValueError("A quantidade de linhas e colunas deve ser positiva.")

    if passo_x <= 0 or passo_y <= 0 or tolerancia < 0:
        raise ValueError("Passos devem ser positivos e tolerância não negativa.")

    rotulos = placa.get("rotulos_linhas")

    if rotulos is None:
        alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        if quantidade_linhas > len(alfabeto):
            raise ValueError(
                "Configure rotulos_linhas para placas com mais de 26 linhas."
            )

        rotulos = list(alfabeto[:quantidade_linhas])

    rotulos = [str(rotulo).strip().upper() for rotulo in rotulos]

    if (
        len(rotulos) != quantidade_linhas
        or len(set(rotulos)) != len(rotulos)
        or any(not re.fullmatch(r"[A-Z]+", r) for r in rotulos)
    ):
        raise ValueError("Configuração de rótulos de linhas inválida.")

    indice_x = round(x / passo_x)
    indice_y = round(y / passo_y)

    if not (0 <= indice_x < quantidade_colunas):
        raise ValueError("Coordenada X fora da área dos poços.")

    if not (0 <= indice_y < quantidade_linhas):
        raise ValueError("Coordenada Y fora da área dos poços.")

    centro_x = indice_x * passo_x
    centro_y = indice_y * passo_y

    distancia = math.hypot(x - centro_x, y - centro_y)

    if distancia > tolerancia:
        raise ValueError(
            f"A coordenada ({x}, {y}) não corresponde ao centro "
            f"de um poço dentro da tolerância de {tolerancia} mm."
        )

    indice_linha = quantidade_linhas - 1 - indice_y
    letra = rotulos[indice_linha]
    numero_coluna = indice_x + 1

    return f"{letra}{numero_coluna}"
