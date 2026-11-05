"""Validador: recusa gerar arquivo inseguro. O operador não confere nada,
então tudo precisa ser garantido aqui, antes de o .nc existir."""
from nucleo.config import carregar
from nucleo.movimentos import MoverZ, MoverXY, Esperar

EPS = 1e-9


class ErroSeguranca(Exception):
    """Lista de problemas encontrados (uma por linha)."""


def validar(movs, modo, pipeta=None, placa=None):
    pipeta = pipeta or carregar("pipeta")
    placa = placa or carregar("placa")
    erros = []

    # 1) Modo real só com parâmetros medidos (não provisórios)
    if modo == "real" and pipeta.get("provisorio", True):
        erros.append("Modo REAL bloqueado: parâmetros da pipeta ainda são provisórios "
                     "(config/pipeta.toml).")

    # 2) Coerência das alturas
    z_park, z_safe, z_aprox = pipeta["z_park"], pipeta["z_safe"], pipeta["z_aprox"]
    if not (0 < z_aprox <= z_safe <= z_park):
        erros.append(f"Alturas incoerentes: precisa 0 < z_aprox ({z_aprox}) <= "
                     f"z_safe ({z_safe}) <= z_park ({z_park}).")
    if pipeta["feed_z"] <= 0:
        erros.append("feed_z deve ser maior que zero.")

    # 3) Limite de profundidade: dry nunca abaixo da folha; real nunca no fundo do poço
    z_min = 0.0 if modo == "dry" else -placa["profundidade_poco"]
    curso_x = pipeta["maquina"]["curso_x"]
    curso_y = pipeta["maquina"]["curso_y"]

    # 4) Simula a lista: Z atual em cada deslocamento XY, e limites do curso
    z_atual = None
    for i, m in enumerate(movs):
        if isinstance(m, MoverZ):
            if m.z <= z_min + EPS:
                erros.append(f"Movimento {i}: Z={m.z} abaixo do limite permitido ({z_min}) "
                             f"no modo {modo}.")
            if m.avanco is not None and m.avanco <= 0:
                erros.append(f"Movimento {i}: avanço inválido ({m.avanco}).")
            z_atual = m.z
        elif isinstance(m, MoverXY):
            if z_atual is None or z_atual < z_safe - EPS:
                erros.append(f"Movimento {i} ({m.rotulo}): XY com Z={z_atual}, "
                             f"abaixo do Z seguro ({z_safe}).")
            if not (0 <= m.x <= curso_x and 0 <= m.y <= curso_y):
                erros.append(f"Movimento {i} ({m.rotulo}): X={m.x}, Y={m.y} fora do curso "
                             f"({curso_x} x {curso_y} mm).")
        elif isinstance(m, Esperar):
            if m.segundos < 0:
                erros.append(f"Movimento {i}: espera negativa.")

    if erros:
        raise ErroSeguranca("\n".join(erros))
