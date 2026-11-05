# Arquitetura

```
Protocolo ──> movimentos ──> validação ──> emissor G-code ──> .nc
```

- `nucleo/` não importa Tkinter. `ui/` chama `nucleo/`, nunca o contrário.
- Configuração em `config/` (TOML). Geometria da placa = fonte da verdade.
- Parâmetros da pipeta marcados `provisorio = true` até a calibração.

(Atualizar este documento conforme as decisões forem tomadas.)
