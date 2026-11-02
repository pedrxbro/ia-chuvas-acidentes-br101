# Diagnóstico de Fontes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar leitores reutilizáveis, diagnóstico calculado, amostras reais e documentação da atividade M2.1 para PRF e INMET de 2025.

**Architecture:** Dois leitores preservam os campos brutos e acrescentam colunas padronizadas. Uma camada de diagnóstico calcula indicadores e uma rotina de geração escreve amostras e relatório, sem associação espacial ou EDA.

**Tech Stack:** Python 3.11+, pandas, zipfile, pytest

**Spec:** `docs/superpowers/specs/2026-11-02-diagnostico-fontes-design.md`

## Global Constraints

- Ler ZIPs diretamente e não extrair os 594 membros do arquivo INMET.
- Não realizar associação espacial definitiva nem produzir conclusões de correlação.
- Não inventar licença, data de acesso ou informação ausente.
- Não versionar ZIPs ou dados intermediários volumosos.
- Preservar colunas originais e criar colunas padronizadas separadas.

## Review Focus

- Arquivo codificado em Windows-1252: detectar e decodificar acentos sem alterar os bytes de origem.
- Precipitação vazia versus `0`: classificar como ausente e zero válido, respectivamente.
- Decimal com vírgula: converter somente na coluna padronizada, mantendo a original.
- Hora INMET `0000 UTC` e data `AAAA/MM/DD`: produzir timestamp UTC válido.
- Duplicidade: contar IDs PRF e timestamps por estação sem remover registros silenciosamente.

---

### Task 1: Leitor e filtro PRF

**Files:**
- Create: `src/ia_chuvas_acidentes/formatos.py`
- Create: `src/ia_chuvas_acidentes/prf.py`
- Create: `tests/test_prf.py`

**Interfaces:**
- Produces: `detectar_formato_csv`, `ler_prf`, `filtrar_prf_sc_br101`.

- [ ] Escrever testes com ZIP mínimo para formato, preservação das colunas, datas e decimais.
- [ ] Executar os testes e confirmar falha por funções ausentes.
- [ ] Implementar as funções mínimas de leitura e filtro.
- [ ] Executar `pytest tests/test_prf.py -q` e confirmar sucesso.

### Task 2: Leitor e cobertura INMET

**Files:**
- Create: `src/ia_chuvas_acidentes/inmet.py`
- Create: `tests/test_inmet.py`

**Interfaces:**
- Consumes: `detectar_formato_csv`.
- Produces: `listar_membros_sc`, `ler_estacao_inmet`, `ler_inmet_sc`, `classificar_precipitacao`.

- [ ] Escrever testes com estações mínimas para metadados, timestamp e estados de precipitação.
- [ ] Executar os testes e confirmar falha por funções ausentes.
- [ ] Implementar seleção e leitura direta dos membros SC.
- [ ] Executar `pytest tests/test_inmet.py -q` e confirmar sucesso.

### Task 3: Diagnóstico e geração de artefatos

**Files:**
- Create: `src/ia_chuvas_acidentes/diagnostico.py`
- Create: `tests/test_diagnostico.py`
- Modify: `src/ia_chuvas_acidentes/__init__.py`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: leitores PRF e INMET.
- Produces: `diagnosticar_prf`, `diagnosticar_inmet`, `gerar_artefatos`, CLI do módulo.

- [ ] Escrever testes para nulos, duplicidades, cobertura e geração de amostras/Markdown.
- [ ] Executar os testes e confirmar falha por funções ausentes.
- [ ] Implementar diagnósticos, amostragem determinística e relatório.
- [ ] Executar `pytest tests/test_diagnostico.py -q` e confirmar sucesso.

### Task 4: Executar contra os dados reais e validar

**Files:**
- Create: `data/samples/Grupo_XX_Fonte_A.csv`
- Create: `data/samples/Grupo_XX_Fonte_B.csv`
- Create: `docs/diagnostico_fontes.md`

**Interfaces:**
- Consumes: `gerar_artefatos` e os dois ZIPs em `data/raw`.
- Produces: artefatos calculados de M2.1.

- [ ] Executar a geração contra os ZIPs fornecidos.
- [ ] Conferir os totais PRF 8.186/4.222 e 24 estações INMET.
- [ ] Conferir destaque de Florianópolis e Laguna e distinção zero/ausente.
- [ ] Executar a suíte completa e inspeções de Git para garantir que ZIPs não entraram no commit.
- [ ] Commitar com `feat: add dataset inspection and source samples`.
