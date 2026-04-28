# 🤖 eROBOT – Automated ELISA Pipetting System

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Language](https://img.shields.io/badge/language-C-blue)
![Platform](https://img.shields.io/badge/platform-CNC%20%2B%20Arduino-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🧪 Sobre o projeto

O **eROBOT** é um sistema de automação laboratorial desenvolvido no CEFET-MG com o objetivo de automatizar ensaios **ELISA (Enzyme-Linked Immunosorbent Assay)** utilizando um CNC adaptado com uma pipeta.

O projeto integra:

* 🧭 Controle de movimento (CNC)
* 💧 Sistema de pipetagem (Arduino)
* 🖥️ Interface touch (Python - futura implementação)

---

## 🎯 Objetivo atual

Gerar **G-code** para simular o movimento de uma pipeta em uma placa ELISA de 96 poços, garantindo:

* Precisão no posicionamento
* Segurança no movimento (controle de altura Z)
* Eficiência na trajetória (zig-zag)

---

## ⚙️ Como funciona

O sistema gera instruções G-code que:

1. Movem o CNC até o centro de cada poço
2. Descem até a altura de trabalho
3. Simulam a dispensação de líquido
4. Retornam à altura segura
5. Repetem o processo para toda a placa (8x12)

---

## 📐 Padrão da placa ELISA

* 96 poços (8 linhas x 12 colunas)
* Espaçamento entre centros: **9 mm**

```text
A1 A2 A3 ... A12
B1 B2 B3 ... B12
...
H1 H2 H3 ... H12
```

---

## 🔁 Estratégia de movimentação

Utilizamos um padrão **zig-zag (serpente)** para otimizar o percurso:

```text
A1 → A2 → ... → A12
← B12 ← B11 ← ... ← B1
→ C1 → C2 → ...
```

### ✅ Vantagens

* Reduz deslocamento desnecessário
* Diminui tempo de execução
* Menor desgaste mecânico

---

## 🗂️ Estrutura do projeto

```
eROBOT/
│
├── README.md
├── .gitignore
│
├── cnc/
│   ├── gcode_generator/
│   │   ├── main.c
│   │   ├── get_position.c
│   │   └── get_position.h
│   │
│   └── output/
│
├── docs/
│   └── images/
│
└── simulations/
```

---

## 🚀 Como executar

### 1. Compilar o código

```bash
gcc main.c -o cnc-test
```

### 2. Executar

```bash
./cnc-test
```

### 3. Resultado

Será gerado um arquivo:

```text
output.gcode
```

---

## 🧪 Simulação

O G-code pode ser visualizado em:

* CAMotics
* ncviewer

---

## 📄 Exemplo de G-code

```gcode
; Poco A1
G1 X10.00 Y20.00 F800
G1 Z-3 F100
G4 P1
; DISPENSE
G1 Z5 F200
```

---

## ⚠️ Limitações atuais

* ❌ Sem integração com a pipeta
* ❌ Sem controle de volume
* ❌ Alturas (Z) não calibradas fisicamente
* ❌ Posição inicial (A1) ainda fixa

---

## 🔮 Próximos passos

* Integração com Arduino (pipeta)
* Implementação de reservatório (aspiração)
* Interface touch em Python
* Controle de volume por poço
* Execução de protocolos ELISA completos

---

## 🧠 Arquitetura futura

```text
[ Interface Python ]
        ↓
  (Orquestrador)
   ↓        ↓
[CNC]    [Pipeta]
```

---

## 👨‍🔧 Boas práticas

* Validar sempre no simulador antes do CNC real
* Nunca mover em XY com Z baixo
* Ajustar velocidades gradualmente
* Calibrar posição inicial (A1) na máquina real

---

## 📜 Licença

MIT License

---

## 👨‍💻 Autor

Projeto desenvolvido no CEFET-MG com o projeto de extensão eROBOT em parceria com a FUNED.
