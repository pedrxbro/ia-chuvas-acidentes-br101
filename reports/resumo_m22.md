# M2.2 — Integração e análise exploratória

## Recorte e rastreabilidade

- PRF: 4222 acidentes na BR-101/SC em 2025, com horário interpretado como `America/Sao_Paulo`.
- Associação principal: 4164 acidentes associados à estação mais próxima em até 50 km; 58 não associados.
- Estações representadas: 7.
- IDs duplicados sinalizados: 0; coordenadas inválidas: 0.
- Distância média dos acidentes associados: 17,50 km.
- Download dos ZIPs informado pelo usuário: **31/10/2026**.
- Unidade analítica: estação-data local. A análise principal exige pelo menos 23 horas válidas.

## Qualidade e perdas

O calendário contém 2555 estação-dias. O denominador principal é de **1653 estação-dias** com precipitação diária válida (64,70%). Neles ocorreram 2613 dos 4164 acidentes contabilizados no calendário.

Sensibilidade do critério de completude: 18 h = 1661 dias; 23 h = 1653 dias; 24 h = 1636 dias.

A alternativa restrita a estações com cobertura anual >=90% associou 3339 acidentes, trocou a estação de 1599 ocorrências comparáveis e alterou a distância média em 15,16 km. Sua amostra utilizável contém 3316 acidentes em 1087 estação-dias válidos, uma diferença de 703 acidentes em relação à associação principal. Ela é apresentada apenas como sensibilidade e não substitui a estação principal conforme a disponibilidade diária.

## Perguntas exploratórias

### A. Acidentes em função da precipitação

A correlação de Spearman usa 1653 estação-dias válidos: rho = -0,042; p-valor = 0,088. Esse resultado descreve associação monotônica no recorte e **não demonstra causalidade**.

### B. Distribuição por faixa de chuva

As faixas abaixo são critérios operacionais do projeto, não categorias oficiais de risco.

| Faixa | Estação-dias | Acidentes | Média de acidentes |
| --- | ---: | ---: | ---: |
| Sem chuva (0 mm) | 731 | 1226 | 1,677 |
| Chuva leve (>0 e <10 mm) | 700 | 1073 | 1,533 |
| Chuva moderada (10 a <30 mm) | 164 | 240 | 1,463 |
| Chuva intensa (>=30 mm) | 58 | 74 | 1,276 |

A maior média observada entre as faixas com dados foi em **Sem chuva (0 mm)**. Essa comparação usa estação-dias, não exposição por volume de veículos.

### C. Variação temporal e espacial

Entre os meses com dados válidos, o mês 4 apresentou a maior média de acidentes por estação-dia (1,957; n=163). A média foi 1,535 nos dias úteis e 1,696 no fim de semana. A estação com maior média foi **ITAJAI** (3,997; n=363).

Essas diferenças podem refletir sazonalidade, localização, dia da semana, cobertura desigual e exposição ao tráfego, além da precipitação.

## Limitações

- Não há informação de **volume de tráfego**, velocidade praticada, obras ou exposição por segmento.
- A estação é uma aproximação espacial; distância, relevo e microclimas reduzem a representatividade local.
- A condição medida pelo INMET não é idêntica à condição meteorológica declarada no registro do acidente.
- Dias incompletos não são tratados como dias secos, e acidentes sem estação ou sem chuva diária válida permanecem documentados.
- As comparações são exploratórias e não permitem afirmar que chuva causa acidentes.

## Preparação para M3

Uma eventual modelagem deverá usar separação temporal: período inicial para desenvolvimento e meses finais preservados como teste. Limiares, transformações e seleção de variáveis deverão ser ajustados sem consultar o período de teste.
