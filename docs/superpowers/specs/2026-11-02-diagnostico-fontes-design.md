# Diagnóstico inicial das fontes PRF e INMET

## Intenção

Implementar a atividade M2.1 como uma inspeção reproduzível dos arquivos brutos de 2025, registrando formato, esquema, qualidade e cobertura antes de qualquer EDA ou associação espacial entre acidentes e estações.

## Escopo

- Ler os ZIPs diretamente, sem extração em massa.
- Manter as colunas originais e acrescentar campos padronizados necessários ao diagnóstico.
- Filtrar PRF por Santa Catarina e BR-101.
- Selecionar os 24 arquivos INMET de Santa Catarina pelo marcador `_SC_`.
- Distinguir precipitação zero, positiva, ausente e inválida.
- Calcular registros, duplicidades, nulos, intervalo temporal e cobertura por estação, com destaque para Florianópolis e Laguna.
- Gerar amostras reais e um relatório Markdown com resultados calculados.
- Cobrir leitura, filtros, datas e campos numéricos com testes unitários de ZIPs mínimos.

## Fora de escopo

- Associação espacial definitiva entre acidentes e estações.
- EDA completa, gráficos ou conclusões de correlação.
- Inferência de licença, data de acesso ou metadados não presentes nos arquivos.
- Versionamento dos ZIPs ou de dados intermediários volumosos.

## Abordagens consideradas

1. **Leitores separados e diagnóstico compartilhado (escolhida).** `prf.py` e `inmet.py` encapsulam os formatos próprios de cada fonte; `diagnostico.py` calcula os indicadores e gera os artefatos. Mantém responsabilidades pequenas e testáveis.
2. **Script monolítico.** Seria mais curto inicialmente, mas acoplaria leitura, regras de qualidade e escrita de arquivos, dificultando reuso na M2.2.
3. **Notebook-first.** Facilitaria inspeção manual, porém reduziria reprodutibilidade e misturaria M2.1 com a futura análise exploratória.

## Decisões técnicas

- Python 3.11+, `zipfile` e `pandas`.
- Detecção de codificação e separador a partir de amostra dos membros do ZIP; os resultados detectados entram no relatório.
- Colunas originais são lidas como texto. Colunas padronizadas recebem nomes explícitos e tipos numéricos ou temporais.
- Valores vazios de precipitação permanecem ausentes; `0` permanece medição válida igual a zero.
- As amostras terão 8 linhas por fonte. O nome `Grupo_XX` será mantido literalmente até o identificador do grupo ser informado.
- Licença de uso e data de acesso serão registradas como pendências, sem preenchimento especulativo.

## Restrições e risco principal

O diagnóstico reflete o conteúdo dos ZIPs disponibilizados. A presença de 8.760 linhas de timestamp por estação não significa 100% de cobertura: a cobertura de precipitação é calculada pelos valores efetivamente medidos. Florianópolis e Laguna precisam aparecer individualmente no relatório para que lacunas extensas não sejam mascaradas por totais agregados.
