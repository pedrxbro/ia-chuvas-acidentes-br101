# Proposta M2.1 em DOCX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gerar a proposta acadêmica M2.1 no modelo oficial, pronta para revisão do grupo.

**Architecture:** O modelo original permanece como autoridade visual. Uma cópia recebe alterações somente no `word/document.xml`, preservando os demais componentes do pacote DOCX; as seções posteriores ficam intactas.

**Tech Stack:** OOXML, Python empacotado, lxml, zipfile, Microsoft Word para inspeção visual

**Spec:** `docs/superpowers/specs/2026-11-03-proposta-m21-docx-design.md`

## Global Constraints

- Preencher somente identificação e seções 2 e 3.
- Preservar a estrutura e os estilos do modelo.
- Não inventar turma, dados pessoais, resultados ou causalidade.
- Não iniciar a EDA da M2.2.
- Não alterar ou versionar os ZIPs de dados.

## Review Focus

- O conteúdo da M2.1 deve ocupar no máximo as duas primeiras páginas.
- As seções 4 a 8 devem manter o mesmo texto e a mesma organização.
- Cada acidente deve ser planejado para no máximo uma estação.
- Zero de precipitação deve permanecer distinto de medição ausente.
- O DOCX deve abrir sem reparos e preservar cabeçalho, tabelas e estilos.

---

### Task 1: Preparar conteúdo e amostras

**Files:**
- Create: `data/samples/Grupo_R_Fonte_A.csv`
- Create: `data/samples/Grupo_R_Fonte_B.csv`

**Interfaces:**
- Consumes: amostras `Grupo_XX_Fonte_A.csv` e `Grupo_XX_Fonte_B.csv` já validadas.
- Produces: nomes finais citados na proposta.

- [x] Copiar as amostras preservando conteúdo e cabeçalhos.
- [x] Verificar oito registros em cada arquivo e ausência de dados brutos volumosos no índice.

### Task 2: Gerar o DOCX a partir do modelo

**Files:**
- Create: `docs/Grupo_R_Projeto_IA.docx`

**Interfaces:**
- Consumes: modelo original, diagnóstico calculado e conteúdo aprovado no design.
- Produces: proposta preenchida nas seções 1 a 3.

- [x] Verificar o hash do modelo contra o contrato de fidelidade.
- [x] Marcar o início da operação de edição de artefato.
- [x] Substituir identificação, respostas e tabela de fontes na cópia.
- [x] Manter as seções 4 a 8 inalteradas.

### Task 3: Verificar documento e repositório

**Files:**
- Verify: `docs/Grupo_R_Projeto_IA.docx`
- Verify: `data/samples/Grupo_R_Fonte_A.csv`
- Verify: `data/samples/Grupo_R_Fonte_B.csv`

**Interfaces:**
- Produces: artefato visualmente revisado e commit local.

- [x] Auditar seções, estilos, cabeçalho e partes preservadas do pacote.
- [x] Inspecionar visualmente todas as páginas no Word a 100%.
- [x] Confirmar duas páginas para a M2.1 e nenhuma alteração de conteúdo nas seções 4 a 8.
- [x] Executar testes do projeto, `git diff --check` e verificar ausência de ZIPs staged.
- [x] Commitar sem trailers de coautoria.
