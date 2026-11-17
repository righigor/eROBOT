
"""Validador de segurança dos movimentos da máquina."""

import math

from nucleo.config import carregar
from nucleo.movimentos import MoverZ, MoverXY, Esperar


EPS = 1e-9


class ErroSeguranca(Exception):
    """Indica que a geração produziria movimentos inseguros."""


def validar(
    movs,
    modo,
    pipeta=None,
    placa=None,
    offsets_pontas=(0.0,),
    orientacao_pontas="x",
):
    """
    Valida os movimentos antes da geração do G-code.

    Args:
        movs: Sequência de movimentos abstratos.
        modo: 'dry' ou 'real'.
        pipeta: Configuração da pipeta.
        placa: Configuração da placa.
        offsets_pontas: Offsets físicos das pontas.
        orientacao_pontas: Eixo dos offsets ('x' ou 'y').
    """

    pipeta = pipeta or carregar("pipeta")
    placa = placa or carregar("placa")

    erros = []

    # --------------------------------------------------
    # 1. Configurações
    # --------------------------------------------------

    try:
        geometria = pipeta["geometria"]
        maquina = pipeta["maquina"]
    except (KeyError, TypeError):
        raise ErroSeguranca(
            "Configuração da pipeta incompleta."
        )

    if modo not in ("dry", "real"):
        erros.append(f"Modo inválido: {modo}")

    orientacao = str(orientacao_pontas).lower()

    if orientacao not in ("x", "y"):
        erros.append(
            "Orientação das pontas inválida. Utilize 'x' ou 'y'."
        )
        orientacao = "x"

    # --------------------------------------------------
    # 2. Validação dos offsets
    # --------------------------------------------------

    try:
        offsets = tuple(
            float(offset)
            for offset in offsets_pontas
        )

    except (TypeError, ValueError):
        offsets = ()
        erros.append("Offsets das pontas inválidos.")

    if not offsets:
        erros.append("Nenhuma ponta foi configurada.")

    elif (
        not all(math.isfinite(offset) for offset in offsets)
        or abs(offsets[0]) > EPS
        or any(offset < 0 for offset in offsets)
        or any(
            offsets[i] >= offsets[i + 1]
            for i in range(len(offsets) - 1)
        )
    ):
        erros.append(
            "Offsets inválidos: devem começar em zero, "
            "ser finitos e crescentes."
        )

    # --------------------------------------------------
    # 3. Bloqueio de modo real
    # --------------------------------------------------

    if modo == "real" and pipeta.get("provisorio", True):
        erros.append(
            "Modo REAL bloqueado: parâmetros da pipeta "
            "ainda são provisórios."
        )

    # --------------------------------------------------
    # 4. Parâmetros geométricos da pipeta
    # --------------------------------------------------

    z_safe = None

    try:
        z_park = float(geometria["z_park"])
        z_safe = float(geometria["z_safe"])
        z_aprox = float(geometria["z_aprox"])
        feed_z = float(geometria["feed_z"])

        parametros_z = (
            z_park,
            z_safe,
            z_aprox,
            feed_z,
        )

        if not all(math.isfinite(v) for v in parametros_z):
            erros.append(
                "Parâmetros Z e feed_z devem ser finitos."
            )

        else:
            if not (
                0 < z_aprox <= z_safe <= z_park
            ):
                erros.append(
                    f"Alturas incoerentes: precisa "
                    f"0 < z_aprox ({z_aprox}) "
                    f"<= z_safe ({z_safe}) "
                    f"<= z_park ({z_park})."
                )

            if feed_z <= 0:
                erros.append(
                    "feed_z deve ser maior que zero."
                )

    except (KeyError, TypeError, ValueError):
        erros.append(
            "Configuração geométrica da pipeta incompleta "
            "ou inválida."
        )

    # --------------------------------------------------
    # 5. Limites físicos da máquina
    # --------------------------------------------------

    curso_x = 0.0
    curso_y = 0.0
    z_min = 0.0

    try:
        curso_x = float(maquina["curso_x"])
        curso_y = float(maquina["curso_y"])

        if not (
            math.isfinite(curso_x)
            and math.isfinite(curso_y)
            and curso_x > 0
            and curso_y > 0
        ):
            erros.append(
                "Cursos X e Y da máquina inválidos."
            )

        # A profundidade só é obrigatória no modo REAL.
        if modo == "real":
            profundidade = float(
                placa["profundidade_poco"]
            )

            if (
                not math.isfinite(profundidade)
                or profundidade <= 0
            ):
                erros.append(
                    "Profundidade do poço inválida. "
                    "Não é possível executar em modo REAL."
                )
            else:
                z_min = -profundidade

    except (KeyError, TypeError, ValueError):
        erros.append(
            "Configuração da máquina ou da placa incompleta."
        )

    # --------------------------------------------------
    # 6. Simulação da sequência de movimentos
    # --------------------------------------------------

    z_atual = None

    for i, movimento in enumerate(movs):

        if isinstance(movimento, MoverZ):

            try:
                z = float(movimento.z)
            except (TypeError, ValueError):
                erros.append(
                    f"Movimento {i}: coordenada Z inválida."
                )
                continue

            if not math.isfinite(z):
                erros.append(
                    f"Movimento {i}: coordenada Z não finita."
                )
                continue

            if z <= z_min + EPS:
                erros.append(
                    f"Movimento {i}: Z={z} "
                    f"abaixo do limite permitido ({z_min}) "
                    f"no modo {modo}."
                )

            if movimento.avanco is not None:
                try:
                    avanco = float(movimento.avanco)

                    if (
                        not math.isfinite(avanco)
                        or avanco <= 0
                    ):
                        erros.append(
                            f"Movimento {i}: avanço inválido "
                            f"({movimento.avanco})."
                        )

                except (TypeError, ValueError):
                    erros.append(
                        f"Movimento {i}: avanço inválido."
                    )

            z_atual = z

        elif isinstance(movimento, MoverXY):

            if (
                z_safe is None
                or z_atual is None
                or z_atual < z_safe - EPS
            ):
                erros.append(
                    f"Movimento {i} ({movimento.rotulo}): "
                    f"XY com Z={z_atual}, abaixo do Z seguro "
                    f"({z_safe})."
                )

            try:
                x = float(movimento.x)
                y = float(movimento.y)

            except (TypeError, ValueError):
                erros.append(
                    f"Movimento {i}: coordenadas XY inválidas."
                )
                continue

            if not (
                math.isfinite(x)
                and math.isfinite(y)
            ):
                erros.append(
                    f"Movimento {i}: coordenadas XY não finitas."
                )
                continue

            # Cada ponta precisa permanecer dentro do curso.
            for numero, offset in enumerate(
                offsets,
                start=1,
            ):

                if orientacao == "x":
                    x_ponta = x + offset
                    y_ponta = y
                else:
                    x_ponta = x
                    y_ponta = y + offset

                if not (
                    -EPS <= x_ponta <= curso_x + EPS
                    and -EPS <= y_ponta <= curso_y + EPS
                ):
                    erros.append(
                        f"Movimento {i} ({movimento.rotulo}): "
                        f"Ponta {numero} fora do curso. "
                        f"X={x_ponta:.3f}, "
                        f"Y={y_ponta:.3f}; "
                        f"limite={curso_x} x {curso_y} mm."
                    )

        elif isinstance(movimento, Esperar):

            try:
                segundos = float(movimento.segundos)

                if (
                    not math.isfinite(segundos)
                    or segundos < 0
                ):
                    erros.append(
                        f"Movimento {i}: espera inválida."
                    )

            except (TypeError, ValueError):
                erros.append(
                    f"Movimento {i}: espera inválida."
                )

        else:
            erros.append(
                f"Movimento {i}: tipo desconhecido "
                f"({type(movimento).__name__})."
            )

    if erros:
        raise ErroSeguranca("\n".join(erros))
