# ⚙️ CNC Module – G-code Generator

Este módulo é responsável por gerar **G-code** para controlar o movimento do CNC no sistema eROBOT.

Ele simula a movimentação de uma pipeta sobre uma placa ELISA de 96 poços.

---

## 🎯 Responsabilidade

* Gerar trajetórias no plano XY
* Controlar altura (eixo Z)
* Simular etapas de pipetagem
* Produzir arquivos `.gcode` executáveis

---

## 🧠 Visão geral

O módulo não controla diretamente o CNC.

Ele apenas gera instruções que podem ser executadas por controladores como:

* Candle
* Universal Gcode Sender

---

## 📁 Estrutura

```id="cz78u5"
gcode_generator/
├── main.c
├── config.h
│
├── gcode/
├── motion/
├── plate/
├── process/
├── Makefile
```

---

## ⚙️ Como compilar

```bash id="yz8cqs"
make
```

---

## ▶️ Como executar

```bash id="u1p1bp"
make run
```

---

## 📄 Saída

O programa gera:

```text id="6m4vzg"
output.gcode
```

---

## 🔁 Lógica de movimentação

O sistema percorre a placa ELISA usando padrão **zig-zag**:

```text id="nvc3q3"
A1 → A2 → ... → A12
← B12 ← B11 ← ... ← B1
→ C1 → C2 → ...
```

---

## 📐 Cálculo de posição

Cada poço é calculado com base em:

* posição inicial (A1)
* espaçamento fixo (pitch = 9 mm)

```c id="0tq8f9"
x = X0 + col * PITCH;
y = Y0 + row * PITCH;
```

---

## ⬆️ Controle de altura (Z)

* `Z_SAFE` → altura segura para movimentação
* `Z_WORK` → altura de pipetagem

Regra importante:

> Nunca mover em XY com Z baixo

---

## 🧪 Simulação

O G-code pode ser testado em:

* CAMotics
* ncviewer

---

## ⚠️ Limitações

* Não há controle real de hardware
* Pipeta ainda não integrada
* Sem sincronização com Arduino
* Parâmetros precisam de calibração real

---

## 🔮 Próximos passos

* adicionar reservatório (aspiração)
* integrar com Arduino (pipeta)
* comunicação com interface Python
* controle de tempo e volume

---

## 🧩 Integração no sistema

Este módulo será controlado futuramente por uma interface em Python que irá:

* enviar comandos ao CNC
* sincronizar com a pipeta
* executar protocolos completos

---

## 📌 Observação

Este módulo é focado em **simulação e validação de trajetória**, sendo uma base para o desenvolvimento do sistema completo.
