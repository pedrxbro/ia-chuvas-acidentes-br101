# Alinhamento da entrega M2.1

## Intenção

Alinhar o projeto já implementado ao enunciado oficial da M2.1, sem iniciar a EDA da M2.2. O diagnóstico técnico e as amostras continuam como evidências; a entrega acadêmica precisa também responder, de forma concisa, às seções 1 a 3 do template do projeto.

## Abordagens consideradas

1. **Atualizar somente o relatório técnico.** Não atende, porque o enunciado exige o `Template_Projeto_IA.docx` e respostas sobre problema, integração e viabilidade.
2. **Recriar um DOCX sem o template original.** Rejeitada porque pode divergir da estrutura exigida e ainda faltam código do grupo e nomes dos integrantes.
3. **Preparar o conteúdo das seções 1 a 3 e completar a base técnica (escolhida).** Gera um texto pronto para transposição ao template, registra pendências verdadeiras e implementa as decisões técnicas já tomadas sobre fuso e valores ausentes.

## Escopo

- Tratar horários PRF como `America/Sao_Paulo`, preservando o timestamp sem fuso e criando versões timezone-aware local e UTC.
- Interpretar os sentinelas INMET `9999`, `Null` e vazio como medição ausente, sem confundi-los com zero.
- Documentar URLs oficiais, produtor, período, unidade, condições de uso verificadas em 03/11/2026 e a diferença entre verificação da página e data original de download.
- Preparar `docs/conteudo_proposta_m21.md` com problema, beneficiários, recorte, fontes, unidade de observação, integração, cardinalidade, riscos, alternativa e declaração de assistência de IA.
- Manter BR-101/SC como recorte principal e todos os acidentes de SC apenas como alternativa de robustez.

## Fora de escopo

- EDA, notebook e HTML da M2.2.
- Associação espacial definitiva ou conclusões sobre correlação.
- Criação do DOCX final sem o `Template_Projeto_IA.docx`.
- Preenchimento do código do grupo, nomes dos integrantes ou data original de download sem informação do usuário.

## Fontes documentais

- Enunciado local `C:\Users\joaov\Downloads\Enunciado_m2-1 (1).docx`.
- PRF: `https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf`.
- INMET: `https://portal.inmet.gov.br/dadoshistoricos/` e orientação institucional sobre dados meteorológicos publicada no portal do INMET.
