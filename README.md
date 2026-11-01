# IA Chuvas e Acidentes na BR-101

Projeto acadêmico da disciplina Inteligência Artificial I, desenvolvido em Python para investigar a relação entre precipitação e acidentes de trânsito na BR-101, em Santa Catarina, durante 2025.

## Pergunta investigável

Como a ocorrência e a intensidade da precipitação se relacionam com a quantidade e as características dos acidentes registrados na BR-101 em Santa Catarina ao longo de 2025?

Esta pergunta será avaliada posteriormente, após a preparação, integração e análise dos dados. Nenhum resultado é apresentado nesta etapa inicial.

## Fontes planejadas

- INMET: `2025.zip`, com dados meteorológicos de 2025.
- PRF: `datatran2025.zip`, com registros de acidentes de trânsito.

Os arquivos devem ser colocados em `data/raw/` e não são versionados por serem datasets brutos. Amostras pequenas e anonimizadas, quando preparadas, poderão ser mantidas em `data/samples/`.

## Estrutura

```text
data/                Dados brutos, intermediários, processados e amostras
notebooks/           Notebooks para exploração posterior
src/ia_chuvas_acidentes/  Código-fonte do projeto
tests/               Testes automatizados
docs/                Documentação de apoio
reports/figures/     Figuras geradas nas análises
```

## Ambiente de desenvolvimento

Requer Python 3.11 ou superior. No diretório do projeto:

```bash
python -m venv .venv
```

Ative o ambiente virtual e instale as dependências:

```bash
# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# Linux/macOS
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Esta etapa contém somente a estrutura inicial; o processamento dos datasets, a integração, a análise exploratória e os gráficos serão desenvolvidos posteriormente.

