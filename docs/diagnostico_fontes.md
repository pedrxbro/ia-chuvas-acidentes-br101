# Diagnóstico inicial das fontes — M2.1

Este documento registra a leitura e o diagnóstico calculado dos arquivos fornecidos para 2025. Ele não realiza associação espacial definitiva, EDA completa nem inferência de correlação.

## Fonte A — Polícia Rodoviária Federal (PRF)

- Arquivo analisado: `data/raw/datatran2025.zip` → `datatran2025.csv`.
- Instituição: Polícia Rodoviária Federal.
- Período declarado e observado no recorte: 2025; 2025-01-01 a 2025-12-31.
- Unidade original: ocorrência de acidente.
- Separador detectado: `;`.
- Codificação detectada: `cp1252`.
- Cabeçalho: primeira linha do CSV.
- Data: `AAAA-MM-DD`; horário: `HH:MM:SS`; decimais: vírgula.
- Licença de uso: **pendente de validação**.
- Data de acesso: **pendente de registro**.

### Quantidade e qualidade

- Registros no arquivo nacional: **72.529**.
- Registros com `uf = SC`: **8.186**.
- Registros com `uf = SC` e `br = 101`: **4.222**.
- Dias com acidentes no recorte: **365**.
- IDs duplicados no recorte: **0**.
- Datas inválidas: **0**; combinações data/hora inválidas: **0**.

| Campo | Nulos/NA no recorte |
| --- | --- |
| id | 0 |
| data_inversa | 0 |
| horario | 0 |
| uf | 0 |
| br | 0 |
| municipio | 0 |
| km | 0 |
| latitude | 0 |
| longitude | 0 |
| mortos | 0 |
| feridos | 0 |
| classificacao_acidente | 0 |
| condicao_metereologica | 0 |

### Esquema relevante

| Campo original | Uso no diagnóstico | Campo padronizado |
| --- | --- | --- |
| id | Identificador e duplicidade | — |
| data_inversa + horario | Data e hora da ocorrência | data_acidente; data_hora_acidente |
| uf + br | Filtro SC/BR-101 | br_num |
| municipio | Localidade declarada | — |
| km | Posição quilométrica | km_num |
| latitude + longitude | Coordenadas da ocorrência | latitude_num; longitude_num |
| mortos + feridos | Gravidade quantitativa | mortos_num; feridos_num |
| classificacao_acidente | Classificação da ocorrência | — |
| condicao_metereologica | Condição declarada pela PRF | — |

Os campos originais são preservados como texto. Sufixos `_num` e os campos temporais são derivados e não substituem o conteúdo de origem. A grafia `condicao_metereologica` é mantida porque é o nome fornecido pela PRF.

## Fonte B — Instituto Nacional de Meteorologia (INMET)

- Arquivo analisado: `data/raw/2025.zip`.
- Instituição: Instituto Nacional de Meteorologia.
- Recorte: membros CSV cujo nome contém `_SC_`.
- Período observado: 2025-01-01 a 2025-12-31.
- Unidade original: observação meteorológica horária.
- Quantidade de arquivos/estações SC: **24**.
- Separador detectado: ';'; codificação detectada: cp1252.
- Metadados lidos das oito linhas iniciais: código WMO, nome, latitude e longitude (além dos valores originais de região, UF, altitude e data de fundação quando presentes).
- Data: `AAAA/MM/DD`; hora: `HHMM UTC`; precipitação: milímetros com vírgula decimal.
- Licença de uso: **pendente de validação**.
- Data de acesso: **pendente de registro**.

### Quantidade, localização e cobertura

- Observações horárias (linhas): **210.240**.
- Medições de precipitação válidas: **115.119**.
- Medições iguais a zero: **103.389**.
- Medições positivas: **11.730**.
- Medições ausentes: **95.121**.
- Medições não vazias mas inválidas: **0**.
- Timestamps duplicados dentro da mesma estação: **0**.
- Extensão espacial das estações: latitude -28.931353 a -26.08138888; longitude -53.633114 a -48.61999999.

Uma linha horária com precipitação vazia é **medição ausente**, não ausência de chuva. O valor numérico `0` é preservado como **medição válida sem precipitação**. A cobertura abaixo usa medições válidas divididas pelas 8.760 horas de 2025.

| WMO | Estação | Latitude | Longitude | Linhas | Horas únicas | Duplicadas | Medições válidas (linhas) | Horas com medição válida | Zero | Positivas | Ausentes | Inválidas | Cobertura |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A806 | FLORIANOPOLIS | -27.6025 | -48.61999999 | 8760 | 8760 | 0 | 3258 | 3258 | 2936 | 322 | 5502 | 0 | 37,19% |
| A814 | URUSSANGA | -28.53249999 | -49.31527777 | 8760 | 8760 | 0 | 4047 | 4047 | 3714 | 333 | 4713 | 0 | 46,20% |
| A815 | SAO JOAQUIM | -28.27555554 | -49.93472221 | 8760 | 8760 | 0 | 6120 | 6120 | 5597 | 523 | 2640 | 0 | 69,86% |
| A816 | NOVO HORIZONTE | -26.40638888 | -52.85027777 | 8760 | 8760 | 0 | 2208 | 2208 | 2125 | 83 | 6552 | 0 | 25,21% |
| A817 | INDAIAL | -26.91361111 | -49.26805554 | 8760 | 8760 | 0 | 1859 | 1859 | 1748 | 111 | 6901 | 0 | 21,22% |
| A841 | JOACABA | -27.16916666 | -51.55888888 | 8760 | 8760 | 0 | 431 | 431 | 368 | 63 | 8329 | 0 | 4,92% |
| A845 | BOM JARDIM DA SERRA - MORRO DA IGREJA | -28.12694443 | -49.47972221 | 8760 | 8760 | 0 | 0 | 0 | 0 | 0 | 8760 | 0 | 0,00% |
| A848 | DIONISIO CERQUEIRA | -26.286562 | -53.633114 | 8760 | 8760 | 0 | 6592 | 6592 | 5975 | 617 | 2168 | 0 | 75,25% |
| A851 | ITAPOA | -26.08138888 | -48.64166666 | 8760 | 8760 | 0 | 6810 | 6810 | 5871 | 939 | 1950 | 0 | 77,74% |
| A857 | SAO MIGUEL DO OESTE | -26.78638888 | -53.51416666 | 8760 | 8760 | 0 | 455 | 455 | 430 | 25 | 8305 | 0 | 5,19% |
| A858 | XANXERE | -26.9386111 | -52.39805555 | 8760 | 8760 | 0 | 743 | 743 | 715 | 28 | 8017 | 0 | 8,48% |
| A859 | CACADOR | -26.81916666 | -50.98555555 | 8760 | 8760 | 0 | 0 | 0 | 0 | 0 | 8760 | 0 | 0,00% |
| A860 | CURITIBANOS | -27.2886111 | -50.60416666 | 8760 | 8760 | 0 | 5832 | 5832 | 5082 | 750 | 2928 | 0 | 66,58% |
| A861 | RIO DO CAMPO | -26.93749999 | -50.14555555 | 8760 | 8760 | 0 | 5831 | 5831 | 5220 | 611 | 2929 | 0 | 66,56% |
| A862 | RIO NEGRINHO | -26.2486111 | -49.57416666 | 8760 | 8760 | 0 | 8737 | 8737 | 8027 | 710 | 23 | 0 | 99,74% |
| A863 | ITUPORANGA | -27.41833332 | -49.64694444 | 8760 | 8760 | 0 | 8666 | 8666 | 7739 | 927 | 94 | 0 | 98,93% |
| A864 | MAJOR VIEIRA | -26.3936111 | -50.36333333 | 8760 | 8760 | 0 | 1436 | 1436 | 1388 | 48 | 7324 | 0 | 16,39% |
| A865 | LAGES | -27.80222222 | -50.33555555 | 8760 | 8760 | 0 | 8757 | 8757 | 7856 | 901 | 3 | 0 | 99,97% |
| A866 | Laguna  - Farol de Santa Marta | -28.60444444 | -48.81333333 | 8760 | 8760 | 0 | 0 | 0 | 0 | 0 | 8760 | 0 | 0,00% |
| A867 | ARARANGUA | -28.931353 | -49.49792 | 8760 | 8760 | 0 | 8746 | 8746 | 7974 | 772 | 14 | 0 | 99,84% |
| A868 | ITAJAI | -26.95083333 | -48.76194444 | 8760 | 8760 | 0 | 8739 | 8739 | 7789 | 950 | 21 | 0 | 99,76% |
| A870 | RANCHO QUEIMADO | -27.6786111 | -49.04194444 | 8760 | 8760 | 0 | 8742 | 8742 | 7289 | 1453 | 18 | 0 | 99,79% |
| A895 | CHAPECO | -27.0853111 | -52.6357111 | 8760 | 8760 | 0 | 8633 | 8633 | 7888 | 745 | 127 | 0 | 98,55% |
| A898 | CAMPOS NOVOS | -27.3886111 | -51.21583333 | 8760 | 8760 | 0 | 8477 | 8477 | 7658 | 819 | 283 | 0 | 96,77% |

### Florianópolis e Laguna

- **FLORIANOPOLIS (A806)**: 3.258 horas com medição válida, 5.502 ausentes, 2.936 iguais a zero; cobertura de 37,19% das 8.760 horas esperadas.
- **Laguna  - Farol de Santa Marta (A866)**: 0 horas com medição válida, 8.760 ausentes, 0 iguais a zero; cobertura de 0,00% das 8.760 horas esperadas.

## Amostras preparadas

- `data/samples/Grupo_XX_Fonte_A.csv`: até 8 ocorrências reais do recorte SC/BR-101, com campos originais relevantes e derivados padronizados.
- `data/samples/Grupo_XX_Fonte_B.csv`: até 8 observações reais, escolhidas deterministicamente por estação e estado da precipitação para representar zero, valor positivo e lacunas quando disponíveis.

`XX` permanece como marcador porque o número do grupo não foi informado.

## Limitações e pendências

- Validar e registrar a licença/termos de uso de cada instituição e a data de acesso dos arquivos; essas informações não constam nos dados fornecidos.
- O fuso de `horario` da PRF não está marcado no CSV. O INMET declara UTC; uma regra explícita de conversão temporal será necessária antes da integração.
- Ausência de medição INMET não pode ser interpretada como precipitação zero. Lacunas extensas podem impedir o uso de uma estação em etapas posteriores.
- A causa operacional das lacunas de cada estação não está presente nos arquivos e não foi inferida.
- Coordenadas e km são declarações das fontes; este diagnóstico valida conversão e disponibilidade, não precisão geográfica.
- Os resultados descrevem a versão local dos ZIPs disponibilizados. Data de publicação, revisão do arquivo e URL de origem permanecem pendentes de documentação.
- Nenhuma associação espacial entre acidentes e estações foi feita nesta etapa e nenhuma conclusão sobre correlação foi produzida.

Relatório gerado de forma reproduzível em 2026-11-02 a partir dos arquivos locais. Essa data é a data de processamento, não uma data de acesso às fontes.
