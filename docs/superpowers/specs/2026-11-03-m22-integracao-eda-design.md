# M2.2 — Integração e EDA Design

## Intenção

Transformar os leitores e o diagnóstico da M2.1 em uma análise reproduzível da relação entre precipitação diária e acidentes na BR-101/SC em 2025, sem treinar modelos e sem interpretar associação como causalidade.

## Decisões

- A PRF continua filtrada por `uf = SC`, `br = 101` e ano de 2025. O horário original é preservado, interpretado como `America/Sao_Paulo` e convertido para UTC.
- O INMET é convertido de UTC para `America/Sao_Paulo` antes da agregação diária. `0 mm` é válido; vazio, `Null`, `9999` e valor não numérico são ausentes.
- A precipitação diária principal exige pelo menos 23 horas válidas. Serão calculados também indicadores para limites de 18 e 24 horas, sem reclassificar ausência como dia seco.
- A associação principal escolhe a estação geograficamente mais próxima em até 50 km, independentemente da disponibilidade da chuva naquele dia. Cada acidente aparece no máximo uma vez.
- A sensibilidade espacial escolhe a estação mais próxima, em até 50 km, entre as estações com cobertura anual de pelo menos 90%, permitindo medir ganho de amostra e aumento de distância sem alterar a análise principal.
- A unidade analítica é `codigo_wmo`–`data_local`. O calendário contém somente as estações que representam ao menos um acidente na associação principal e inclui dias com zero acidentes.
- A junção estação-dia é um-para-um. Dias incompletos permanecem na tabela com `precipitacao_mm_dia = NA` para a análise principal.
- As tabelas finais versionáveis ficam em `data/processed/`; saídas temporárias continuam ignoradas em `data/interim/`.
- O notebook `Grupo_R_M2_2_EDA.ipynb` organiza objetivo, fontes, qualidade, preparação, integração, EDA, limitações e plano temporal para a M3.

## Componentes

- `src/ia_chuvas_acidentes/preparacao.py`: validação PRF, observações INMET e agregação diária.
- `src/ia_chuvas_acidentes/integracao.py`: Haversine, associação principal/alternativa e tabela estação-dia.
- `src/ia_chuvas_acidentes/eda.py`: estatísticas, faixas de chuva, figuras e resumo textual.
- `src/ia_chuvas_acidentes/pipeline_m22.py`: orquestra leitura, processamento e gravação determinística.
- `notebooks/Grupo_R_M2_2_EDA.ipynb`: narrativa executável que usa os módulos e apresenta os resultados reais.

## Saídas

- `data/processed/prf_sc_br101_2025.csv`
- `data/processed/inmet_precipitacao_diaria_2025.csv`
- `data/processed/associacao_acidente_estacao_2025.csv`
- `data/processed/acidentes_sem_estacao_2025.csv`
- `data/processed/tabela_estacao_dia_2025.csv`
- `data/processed/metricas_cobertura_2025.csv`
- `reports/figures/*.png`
- `reports/resumo_m22.md`

## Rastreabilidade e limites

As contagens antes/depois, duplicidades, não correspondências, cobertura e critérios serão gravados no resumo. Distância, relevo, microclimas, sazonalidade, dia da semana e ausência de volume de tráfego serão tratados como limitações. A data de download informada pelo usuário é 31/10/2026; a turma permanece sem preenchimento por solicitação.

## Alternativas consideradas

1. Usar somente a estação mais próxima: é a análise principal por ser espacialmente auditável, mas perde dias quando a estação falha.
2. Substituir diariamente pela estação com chuva disponível: rejeitada como principal porque muda silenciosamente a representação espacial conforme a data.
3. Restringir a estações com alta cobertura anual: adotada apenas como sensibilidade, com limiar explícito de 90% e comparação de distância e tamanho amostral.

## Fora do escopo

- Treinamento ou escolha definitiva de algoritmo de aprendizado de máquina.
- Afirmações causais.
- Uso de dados de tráfego não fornecidos.
- Expansão do recorte principal para outras rodovias de Santa Catarina.
