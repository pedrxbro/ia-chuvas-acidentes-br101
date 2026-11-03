# Alinhamento da Entrega M2.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completar as lacunas técnicas e documentais identificadas pela comparação do projeto com o enunciado oficial da M2.1.

**Architecture:** Os leitores continuam preservando campos originais e acrescentam derivados explícitos. O gerador reproduz o diagnóstico com metadados de origem, enquanto um documento Markdown separado concentra o texto curto das seções 1 a 3 para futura transposição ao template oficial.

**Tech Stack:** Python 3.11+, pandas, zoneinfo/IANA time zones, pytest, Markdown

**Spec:** `docs/superpowers/specs/2026-11-03-alinhamento-entrega-m21-design.md`

## Global Constraints

- Não iniciar a EDA da M2.2.
- Não inventar código do grupo, integrantes ou data original de download.
- Preservar os campos brutos PRF e INMET.
- Não versionar os ZIPs.
- Manter o recorte principal `uf = SC` e `br = 101`.

## Review Focus

- Horário PRF local deve permanecer 2025-01-01 06:20 em São Paulo e converter para 09:20 UTC.
- Timestamp PRF inválido deve permanecer `NaT` nas colunas derivadas timezone-aware.
- `0` e `0,0` do INMET devem continuar válidos e distintos de vazio, `Null` e `9999`.
- A documentação deve distinguir acesso às páginas oficiais em 03/11/2026 da data desconhecida de download dos ZIPs locais.
- A integração proposta deve declarar granularidade e evitar multiplicação de linhas por estação/hora.

---

### Task 1: Fuso horário PRF

**Files:**
- Modify: `tests/test_prf.py`
- Modify: `src/ia_chuvas_acidentes/prf.py`

**Interfaces:**
- Produces: colunas `data_hora_acidente_sp` e `data_hora_acidente_utc` em `ler_prf`.

- [x] Escrever testes para localização em São Paulo, conversão UTC e timestamp inválido.
- [x] Executar os testes e confirmar falha por colunas ausentes.
- [x] Implementar as colunas derivadas sem substituir `data_hora_acidente`.
- [x] Executar `pytest tests/test_prf.py -q`.

### Task 2: Sentinelas de ausência INMET

**Files:**
- Modify: `tests/test_inmet.py`
- Modify: `src/ia_chuvas_acidentes/inmet.py`

**Interfaces:**
- Produces: `classificar_precipitacao` e `precipitacao_mm` tratando vazio, `Null` e `9999` como ausentes.

- [x] Escrever teste que diferencia sentinelas de zero e valor positivo.
- [x] Executar o teste e observar a falha atual.
- [x] Implementar normalização compartilhada de sentinelas.
- [x] Executar `pytest tests/test_inmet.py -q`.

### Task 3: Metadados e conteúdo da proposta

**Files:**
- Modify: `src/ia_chuvas_acidentes/diagnostico.py`
- Modify: `tests/test_diagnostico.py`
- Modify: `docs/diagnostico_fontes.md`
- Create: `docs/conteudo_proposta_m21.md`

**Interfaces:**
- Consumes: novas colunas PRF e classificação INMET.
- Produces: relatório reproduzível e conteúdo pronto para as seções 1 a 3.

- [x] Atualizar o teste de geração para verificar colunas timezone-aware nas amostras.
- [x] Executar o teste e confirmar falha.
- [x] Incluir URLs, condições verificadas, fuso e pendências precisas no gerador.
- [x] Regenerar relatório e amostras com os ZIPs reais.
- [x] Redigir o conteúdo conciso da proposta, incluindo cardinalidade, riscos, alternativa e uso de IA.
- [x] Executar a suíte completa e asserções dos dados reais.

### Task 4: Verificação e commit

**Files:**
- Verify: todos os arquivos modificados/criados acima.

**Interfaces:**
- Produces: commit local sem ZIPs e com testes verdes.

- [x] Executar `pytest -q`, `compileall`, `git diff --check` e verificar que nenhum ZIP está staged.
- [x] Revisar o diff contra o enunciado e o plano.
- [x] Commitar usando a identidade Git existente, sem trailers de coautoria.
