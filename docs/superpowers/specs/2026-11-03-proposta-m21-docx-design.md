# Proposta M2.1 em DOCX Design

## Intenção

Produzir a proposta acadêmica da atividade M2.1 a partir do modelo oficial, usando os resultados efetivamente calculados no projeto e mantendo a estrutura destinada às etapas posteriores.

## Conteúdo autorizado

- Grupo: R.
- Integrantes: Flávia Schnaider; Gregori da Luz Maciel; João Victor da Silva; Pedro Henrique de Paula Cordeiro.
- Turma: não informada; manter marcador explícito para preenchimento.
- Pergunta: “Existe associação entre o volume diário de precipitação e o número de acidentes registrados na BR-101, em Santa Catarina, durante 2025?”
- Recorte principal: acidentes PRF em SC na BR-101 durante 2025.
- Fontes: PRF `datatran2025.zip` e INMET `2025.zip`, com URLs e condições oficiais verificadas em 03/11/2026.

## Decisões de conteúdo

- Preencher a identificação e as seções 2 e 3 do modelo.
- Manter a distinção entre resultados já calculados, método planejado e limitações.
- Planejar a unidade final como estação-data local, com precipitação diária e contagem de acidentes.
- Converter horários UTC e `America/Sao_Paulo` antes da agregação por data local.
- Mapear cada acidente a no máximo uma estação elegível por Haversine, estudando limite inicial de 50 km e análise de sensibilidade posterior.
- Não interpretar medição ausente como zero e não afirmar causalidade.
- Manter as seções 4 a 8 e seus marcadores inalterados.

## Fidelidade e entrega

- Editar uma cópia de `C:\Users\joaov\Downloads\Modelo_atividade (1).docx`.
- Preservar página A4, margens, cabeçalho, rodapé, estilos, numeração e tabelas do modelo.
- Manter a M2.1 em até duas páginas de conteúdo, além dos CSVs de amostra.
- Gerar `docs/Grupo_R_Projeto_IA.docx`.
- Renomear as amostras para `Grupo_R_Fonte_A.csv` e `Grupo_R_Fonte_B.csv`.
- Deixar a turma como `[preencher]`; não inventar dados pessoais ou resultados.

## Fora do escopo

- EDA da M2.2, notebook, HTML, gráficos e associação espacial executada.
- Seleção de algoritmo de aprendizado de máquina.
- Conclusões estatísticas ou causais.
