# M2.2 — Integração e EDA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produzir a base estação-dia auditável, a EDA executável e os artefatos acadêmicos da M2.2 para BR-101/SC em 2025.

**Architecture:** Leitores existentes alimentam módulos pequenos de preparação, integração e análise. Um pipeline grava tabelas determinísticas; o notebook apenas organiza e apresenta o mesmo processamento reutilizável.

**Tech Stack:** Python 3.11+, pandas, NumPy, SciPy, Matplotlib, Seaborn, Jupyter/nbconvert, pytest

**Spec:** `docs/superpowers/specs/2026-11-03-m22-integracao-eda-design.md`

## Global Constraints

- Tratar PRF como `America/Sao_Paulo` e INMET como UTC convertido para data local.
- Preservar zero de precipitação e nunca convertê-lo em ausência, ou vice-versa.
- Completude principal: 23/24 horas; sensibilidades: 18/24 e 24/24.
- Associação principal: estação mais próxima em até 50 km, no máximo uma por acidente.
- Alternativa de cobertura: estações com cobertura anual >= 90%, reportada separadamente.
- Não treinar modelos nem afirmar causalidade.
- Não usar caminhos absolutos nem versionar ZIPs.

## Review Focus

- Acidente sem coordenadas deve receber status explícito e nunca entrar no cálculo Haversine.
- Empates de distância devem ser resolvidos deterministicamente pelo código WMO.
- Dia incompleto com chuva observada deve manter a soma bruta, mas ter precipitação principal ausente.
- Conversão UTC→São Paulo deve poder mover observações para o dia civil anterior.
- Junção estação-dia deve rejeitar chaves repetidas e manter dias completos sem acidentes.

---

### Task 1: Preparação temporal e precipitação diária

**Files:**
- Create: `src/ia_chuvas_acidentes/preparacao.py`
- Create: `tests/test_preparacao.py`

**Interfaces:**
- Consumes: `list[LeituraEstacao]` e o recorte retornado por `filtrar_prf_sc_br101`.
- Produces: `validar_prf_m22(df, ano=2025)` e `agregar_precipitacao_diaria(estacoes, min_horas=23)`.

- [x] Escrever testes para filtro temporal, IDs/coordenadas inválidos, UTC→São Paulo, zero válido, soma diária e completude 18/23/24.
- [x] Executar `pytest tests/test_preparacao.py -q` e confirmar falha por módulo ausente.
- [x] Implementar as funções e campos derivados documentados.
- [x] Executar `pytest tests/test_preparacao.py -q` e confirmar aprovação.

### Task 2: Associação espacial auditável

**Files:**
- Create: `src/ia_chuvas_acidentes/integracao.py`
- Create: `tests/test_integracao.py`

**Interfaces:**
- Consumes: PRF validada, metadados únicos das estações e precipitação diária.
- Produces: `haversine_km`, `associar_estacoes`, `construir_tabela_estacao_dia` e `comparar_estrategia_cobertura`.

- [x] Escrever testes para distância conhecida, limite de 50 km, coordenada ausente, desempate WMO, unicidade e calendário com zero acidentes.
- [x] Executar `pytest tests/test_integracao.py -q` e confirmar falha por módulo ausente.
- [x] Implementar associação principal, alternativa >=90% e junção um-para-um.
- [x] Executar `pytest tests/test_integracao.py -q` e confirmar aprovação.

### Task 3: Estatísticas, figuras e resumo

**Files:**
- Create: `src/ia_chuvas_acidentes/eda.py`
- Create: `tests/test_eda.py`

**Interfaces:**
- Consumes: tabela estação-dia e métricas de integração.
- Produces: `classificar_faixa_chuva`, `calcular_resumo_eda`, `gerar_figuras` e `renderizar_resumo_m22`.

- [x] Escrever testes para faixas de chuva, denominadores, Spearman insuficiente e contagens por completude.
- [x] Executar `pytest tests/test_eda.py -q` e confirmar falha por módulo ausente.
- [x] Implementar estatísticas, gráficos legíveis e relatório sem linguagem causal.
- [x] Executar `pytest tests/test_eda.py -q` e confirmar aprovação.

### Task 4: Pipeline e saídas reproduzíveis

**Files:**
- Create: `src/ia_chuvas_acidentes/pipeline_m22.py`
- Create: `tests/test_pipeline_m22.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: funções das Tasks 1–3.
- Produces: `executar_pipeline_m22(...) -> ResultadoM22` e CLI `python -m ia_chuvas_acidentes.pipeline_m22`.

- [x] Escrever teste de integração com ZIPs mínimos e caminhos relativos.
- [x] Executar `pytest tests/test_pipeline_m22.py -q` e confirmar falha por módulo ausente.
- [x] Implementar gravação das seis tabelas, figuras e resumo com diretórios configuráveis.
- [x] Executar `pytest tests/test_pipeline_m22.py -q` e confirmar aprovação.

### Task 5: Notebook executável e dados reais

**Files:**
- Create: `notebooks/Grupo_R_M2_2_EDA.ipynb`
- Create: `data/processed/*.csv`
- Create: `reports/figures/*.png`
- Create: `reports/resumo_m22.md`
- Modify: `docs/diagnostico_fontes.md`
- Modify: `docs/conteudo_proposta_m21.md`

**Interfaces:**
- Consumes: CLI e tabelas da Task 4.
- Produces: notebook executado, resultados reais e registro de download em 31/10/2026.

- [x] Executar o pipeline nos ZIPs reais e validar contagens, chaves e não correspondências.
- [x] Criar o notebook com as sete seções exigidas e células que leem/expõem os artefatos reproduzíveis.
- [x] Executar o notebook do início ao fim com `jupyter nbconvert --execute --inplace`.
- [x] Atualizar a documentação da data de download, mantendo a turma sem preenchimento.

### Task 6: Verificação e commit

**Files:**
- Verify: todos os arquivos anteriores.

**Interfaces:**
- Produces: branch verificável e commit local sem trailers.

- [x] Executar `pytest -q`, `python -m compileall -q src tests`, `git diff --check` e validar o notebook executado.
- [x] Revisar resultados e limitações contra a especificação.
- [x] Commitar como `feat: implement M2.2 data integration and EDA`.
