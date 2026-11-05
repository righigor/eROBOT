# eROBOT — Gerador de movimentos para CNC

Software que traduz protocolos laboratoriais (ex.: ELISA) em movimentos
da CNC (G-code para o pendant RichAuto A11), seguindo a geometria da placa
de poços do projeto eROBOT.

> **Status:** em desenvolvimento (v0.1.0). Fase atual: somente movimento
> da pipeta; o acionamento da pipetagem ainda não faz parte do escopo.

> **Confidencial:** manter este repositório PRIVADO até decisão sobre
> proteção da propriedade intelectual (consultar o NIT do CEFET-MG).

## Requisitos
- Ubuntu/Linux, Python 3.11+
- Tkinter: `sudo apt install python3-tk`

## Instalação
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso
```bash
python3 main.py
```
O G-code gerado é salvo em um pendrive FAT32 e executado no A11.

## Estrutura
```
config/      geometria da placa e parâmetros da pipeta (TOML)
protocolos/  um arquivo .toml por protocolo cadastrado
nucleo/      lógica pura (SEM Tkinter): geometria, movimentos, G-code
ui/          interface Tkinter (nunca contém lógica de G-code)
docs/        diário de desenvolvimento e arquitetura
tests/       testes automatizados (pytest)
```

## Regras de segurança da máquina
- Sobe Z primeiro, anda XY depois.
- Arquivo sempre começa e termina em Z_PARK, com M5 no início e no fim.
- Somente G0/G1/G21/G90/G17/G4/M3/M5/M30 (o A11 não aceita G81).
- ASCII puro, CRLF, nome de arquivo curto e sem acentos.
- Parâmetros provisórios da pipeta bloqueiam a geração em modo real.
