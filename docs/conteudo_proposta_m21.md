# Conteúdo-base da proposta M2.1

Este texto serviu de apoio ao preenchimento das seções 1 a 3 de `docs/Grupo_R_Projeto_IA.docx`. O código do grupo e os integrantes já foram informados; antes da entrega, falta confirmar a turma e, se recuperável, a data original de download dos arquivos. O documento final respeita o limite de duas páginas de conteúdo da M2.1, além das amostras.

## 1. Problema e escopo

O projeto investiga como a ocorrência e a intensidade da precipitação se relacionam com a quantidade e as características dos acidentes registrados na BR-101 em Santa Catarina ao longo de 2025. A questão interessa a gestores de segurança viária, órgãos públicos e usuários da rodovia, pois pode apoiar a descrição de períodos e locais que exigem maior atenção operacional. Nesta etapa não se afirma causalidade nem correlação; apenas se verifica se as fontes são adequadas e integráveis.

O recorte principal será `uf = SC` e `br = 101`. A base PRF contém 72.529 ocorrências nacionais em 2025, 8.186 em Santa Catarina e 4.222 no recorte principal. A quantidade é suficiente para a continuação do trabalho e não há necessidade de ampliar agora a análise principal para todas as rodovias do estado. Os 8.186 acidentes de SC podem ser usados posteriormente como análise de robustez ou plano alternativo, sem alterar a pergunta central.

Uma linha da PRF representa uma ocorrência de acidente. Uma linha do INMET representa uma observação meteorológica de uma estação em uma hora UTC. Na integração preliminar, a unidade será o acidente enriquecido com a observação horária de uma única estação elegível. Para análises de frequência, os dados poderão ser agregados depois por estação e hora, incluindo horas sem acidente, desde que haja medição meteorológica válida.

## 2. Fontes de dados

| Fonte | Produtor e acesso | Período e unidade | Contribuição e condições de uso |
| --- | --- | --- | --- |
| PRF — `datatran2025.csv` em `datatran2025.zip` | Polícia Rodoviária Federal. https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf | 2025; uma ocorrência de acidente por linha. | Fornece data, horário, localização, classificação, mortos, feridos e condição meteorológica declarada. A página oficial informa livre utilização, reutilização e redistribuição; nenhuma licença nominal específica foi identificada. |
| INMET — 24 arquivos `_SC_` em `2025.zip` | Instituto Nacional de Meteorologia. Dados históricos: https://portal.inmet.gov.br/dadoshistoricos/. Orientação oficial: https://portal.inmet.gov.br/noticias/saiba-como-acessar-os-dados-meteorol%C3%B3gicos-dispon%C3%ADveis-no-site-do-inmet | 2025; uma observação meteorológica horária por linha. | Fornece código WMO, nome e coordenadas da estação e precipitação total horária em milímetros. O INMET informa acesso público e gratuito e atribui ao usuário a responsabilidade pelo uso; os dados automáticos são brutos e não validados previamente quanto à consistência. |

As páginas oficiais foram verificadas em 03/11/2026. Essa é a data de verificação documental, não a data original de download dos ZIPs, que não foi registrada e permanece pendente. As amostras reais estão em `data/samples/Grupo_R_Fonte_A.csv` e `data/samples/Grupo_R_Fonte_B.csv`, com oito registros e cabeçalhos em cada arquivo.

A PRF usa ponto e vírgula, codificação CP1252, data `AAAA-MM-DD`, horário `HH:MM:SS` e vírgula decimal. O horário é tratado por decisão metodológica como `America/Sao_Paulo`, mantendo o valor original e uma versão convertida para UTC. O INMET usa ponto e vírgula, CP1252, data `AAAA/MM/DD`, hora `HHMM UTC` e vírgula decimal. Precipitação `0` é uma medição válida sem chuva; vazio, `Null` e `9999` são ausência de medição.

## 3. Integração, viabilidade e riscos

A chave temporal padronizada será a hora UTC. Cada acidente terá seu horário PRF localizado em `America/Sao_Paulo` e convertido para UTC. A seleção espacial ainda será definida na etapa seguinte: cada acidente poderá ser associado a uma única estação elegível, considerando distância e cobertura. A tabela meteorológica deve ser única por `(codigo_wmo, data_hora_utc)`. Assim, a junção será muitos-para-um e deverá preservar no máximo uma linha de saída por acidente; não será feita uma junção de cada acidente com todas as estações.

Os arquivos são tecnicamente legíveis e cobrem todo o ano, mas a precipitação apresenta lacunas importantes. Das 210.240 linhas do INMET, 115.119 têm medição válida, 103.389 têm precipitação zero, 11.730 têm valor positivo e 95.121 não têm medição. Florianópolis (A806) tem 3.258 horas válidas de 8.760 (37,19%), enquanto Laguna (A866), Morro da Igreja (A845) e Caçador (A859) não têm medição válida no arquivo de 2025. Portanto, presença de uma linha horária não garante disponibilidade da precipitação.

Os principais riscos são lacunas meteorológicas, distância entre acidente e estação, a suposição de fuso da PRF, possível imprecisão das coordenadas declaradas e a cobertura de apenas um ano. O plano principal é excluir estações sem cobertura útil, selecionar uma única estação elegível por acidente e registrar distância e disponibilidade. Como alternativas, pode-se usar a próxima estação com cobertura adequada, agregar precipitação por dia quando justificável ou ampliar a PRF para todos os acidentes de Santa Catarina como análise secundária. Nenhuma dessas escolhas deve substituir ausência por zero.

Foi utilizada assistência de IA para apoiar a inspeção dos arquivos, a implementação dos leitores e testes e a redação inicial. Os totais foram recalculados diretamente dos ZIPs locais; as condições de acesso foram verificadas nas páginas oficiais; e as transformações foram verificadas por testes automatizados. Decisões metodológicas e o texto final devem ser revisados pelos integrantes do grupo.

## Pendências antes da entrega

- Confirmar a turma dos integrantes.
- Registrar a data original de download dos dois ZIPs, se recuperável.
