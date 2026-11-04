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

## Executar a M2.2

Com os dois ZIPs em `data/raw/`, execute:

```bash
python run_m22.py
jupyter nbconvert --to notebook --execute --inplace notebooks/Grupo_R_M2_2_EDA.ipynb
```

O pipeline interpreta o horário PRF como `America/Sao_Paulo`, converte as horas UTC do INMET para a data local, agrega chuva com critério principal de 23 horas válidas, associa cada acidente à estação mais próxima em até 50 km e grava tabelas em `data/processed/`, figuras em `reports/figures/` e o resumo em `reports/resumo_m22.md`.

As faixas de chuva e a alternativa com estações de cobertura anual maior ou igual a 90% são sensibilidades exploratórias. Não representam categorias oficiais de risco nem permitem inferência causal.

