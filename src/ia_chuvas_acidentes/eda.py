"""Estatísticas, visualizações e relatório da análise exploratória M2.2."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr


ORDEM_FAIXAS = [
    "Sem chuva (0 mm)",
    "Chuva leve (>0 e <10 mm)",
    "Chuva moderada (10 a <30 mm)",
    "Chuva intensa (>=30 mm)",
    "Sem medição completa",
]


def classificar_faixa_chuva(precipitacao: pd.Series) -> pd.Series:
    """Aplica faixas exploratórias explícitas, sem converter ausência em zero."""

    valores = pd.to_numeric(precipitacao, errors="coerce")
    resultado = pd.Series(
        "Sem medição completa", index=precipitacao.index, dtype="object"
    )
    resultado.loc[valores.eq(0)] = "Sem chuva (0 mm)"
    resultado.loc[valores.gt(0) & valores.lt(10)] = "Chuva leve (>0 e <10 mm)"
    resultado.loc[valores.ge(10) & valores.lt(30)] = (
        "Chuva moderada (10 a <30 mm)"
    )
    resultado.loc[valores.ge(30)] = "Chuva intensa (>=30 mm)"
    return resultado


def calcular_resumo_eda(tabela: pd.DataFrame) -> dict:
    """Calcula denominadores e estatísticas apenas com chuva diária elegível."""

    obrigatorias = {"precipitacao_mm_dia", "acidentes"}
    ausentes = sorted(obrigatorias - set(tabela.columns))
    if ausentes:
        raise ValueError(f"Campos ausentes na tabela de EDA: {', '.join(ausentes)}")

    dados = tabela.copy()
    dados["precipitacao_mm_dia"] = pd.to_numeric(
        dados["precipitacao_mm_dia"], errors="coerce"
    )
    dados["acidentes"] = pd.to_numeric(dados["acidentes"], errors="coerce").fillna(0)
    dados["faixa_chuva"] = classificar_faixa_chuva(dados["precipitacao_mm_dia"])
    validos = dados.loc[dados["precipitacao_mm_dia"].notna()].copy()

    rho = np.nan
    p_valor = np.nan
    if (
        len(validos) >= 3
        and validos["precipitacao_mm_dia"].nunique() > 1
        and validos["acidentes"].nunique() > 1
    ):
        resultado_spearman = spearmanr(
            validos["precipitacao_mm_dia"], validos["acidentes"], nan_policy="omit"
        )
        rho = float(resultado_spearman.statistic)
        p_valor = float(resultado_spearman.pvalue)

    faixas: dict[str, dict[str, float | int]] = {}
    for faixa in ORDEM_FAIXAS[:-1]:
        grupo = validos.loc[validos["faixa_chuva"].eq(faixa)]
        faixas[faixa] = {
            "estacao_dias": int(len(grupo)),
            "acidentes": int(grupo["acidentes"].sum()),
            "media_acidentes": float(grupo["acidentes"].mean()) if len(grupo) else np.nan,
        }

    sensibilidade = {}
    for limite in (18, 23, 24):
        coluna = f"completo_{limite}h"
        sensibilidade[f"{limite}h"] = (
            int(dados[coluna].fillna(False).astype(bool).sum()) if coluna in dados else 0
        )

    def resumir_grupos(coluna: str, rotulos=None) -> dict:
        if coluna not in validos:
            return {}
        resultado = {}
        for chave, grupo in validos.groupby(coluna, observed=True, sort=True):
            rotulo = rotulos.get(chave, chave) if rotulos else chave
            resultado[rotulo] = {
                "estacao_dias": int(len(grupo)),
                "acidentes": int(grupo["acidentes"].sum()),
                "media_acidentes": float(grupo["acidentes"].mean()),
            }
        return resultado

    variacao_mensal = resumir_grupos("mes")
    variacao_fim_semana = resumir_grupos(
        "fim_semana", {False: "dias_uteis", True: "fim_de_semana"}
    )
    variacao_estacao = resumir_grupos("nome_estacao")

    return {
        "estacao_dias_total": int(len(dados)),
        "estacao_dias_validos_23h": int(len(validos)),
        "cobertura_principal_pct": float(100 * len(validos) / len(dados))
        if len(dados)
        else np.nan,
        "acidentes_total": int(dados["acidentes"].sum()),
        "acidentes_em_dias_validos_23h": int(validos["acidentes"].sum()),
        "sensibilidade_completude": sensibilidade,
        "spearman_n": int(len(validos)),
        "spearman_rho": rho,
        "spearman_p_valor": p_valor,
        "faixas": faixas,
        "variacao_mensal": variacao_mensal,
        "variacao_fim_semana": variacao_fim_semana,
        "variacao_estacao": variacao_estacao,
    }


def _salvar(figura, caminho: Path) -> Path:
    figura.tight_layout()
    figura.savefig(caminho, dpi=160, bbox_inches="tight")
    plt.close(figura)
    return caminho


def gerar_figuras(tabela: pd.DataFrame, pasta: str | Path) -> list[Path]:
    """Gera as figuras padronizadas da M2.2 e retorna seus caminhos."""

    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    dados = tabela.copy()
    dados["data_local"] = pd.to_datetime(dados["data_local"], errors="coerce")
    dados["faixa_chuva"] = classificar_faixa_chuva(dados["precipitacao_mm_dia"])
    validos = dados.loc[dados["precipitacao_mm_dia"].notna()].copy()
    caminhos: list[Path] = []

    figura, eixo = plt.subplots(figsize=(8, 5))
    sns.histplot(validos["precipitacao_mm_dia"], bins=30, ax=eixo)
    eixo.set(title="Distribuição da precipitação diária válida", xlabel="Precipitação (mm/dia)", ylabel="Estação-dias")
    caminhos.append(_salvar(figura, pasta / "01_distribuicao_precipitacao.png"))

    figura, eixo = plt.subplots(figsize=(8, 5))
    sns.histplot(dados["acidentes"], discrete=True, ax=eixo)
    eixo.set(title="Distribuição do número diário de acidentes", xlabel="Acidentes por estação-dia", ylabel="Estação-dias")
    caminhos.append(_salvar(figura, pasta / "02_distribuicao_acidentes.png"))

    serie = dados.groupby("data_local", as_index=False).agg(
        acidentes=("acidentes", "sum"),
        precipitacao_media_mm=("precipitacao_mm_dia", "mean"),
    )
    figura, eixo1 = plt.subplots(figsize=(11, 5))
    eixo1.plot(serie["data_local"], serie["acidentes"], color="#c44e52", label="Acidentes")
    eixo1.set(xlabel="Data local", ylabel="Acidentes", title="Séries temporais de chuva e acidentes")
    eixo2 = eixo1.twinx()
    eixo2.plot(serie["data_local"], serie["precipitacao_media_mm"], color="#4c72b0", alpha=0.65, label="Chuva média")
    eixo2.set_ylabel("Precipitação média das estações (mm/dia)")
    linhas = eixo1.get_lines() + eixo2.get_lines()
    eixo1.legend(linhas, [linha.get_label() for linha in linhas], loc="upper right")
    caminhos.append(_salvar(figura, pasta / "03_series_temporais.png"))

    figura, eixo = plt.subplots(figsize=(8, 5))
    sns.scatterplot(data=validos, x="precipitacao_mm_dia", y="acidentes", alpha=0.55, ax=eixo)
    eixo.set(title="Precipitação diária e número de acidentes", xlabel="Precipitação (mm/dia)", ylabel="Acidentes por estação-dia")
    caminhos.append(_salvar(figura, pasta / "04_dispersao_chuva_acidentes.png"))

    medias = validos.groupby("faixa_chuva", observed=True)["acidentes"].mean().reindex(ORDEM_FAIXAS[:-1]).dropna()
    figura, eixo = plt.subplots(figsize=(10, 5))
    sns.barplot(x=medias.index, y=medias.values, ax=eixo, color="#4c72b0")
    eixo.set(title="Média de acidentes por faixa operacional de chuva", xlabel="Faixa de precipitação", ylabel="Média de acidentes por estação-dia")
    eixo.tick_params(axis="x", rotation=20)
    caminhos.append(_salvar(figura, pasta / "05_media_acidentes_faixa_chuva.png"))

    validos["mes"] = validos["data_local"].dt.month
    mensal = validos.groupby("mes", as_index=False).agg(media_acidentes=("acidentes", "mean"))
    figura, eixo = plt.subplots(figsize=(9, 5))
    sns.lineplot(data=mensal, x="mes", y="media_acidentes", marker="o", ax=eixo)
    eixo.set(title="Média de acidentes por mês em estação-dias válidos", xlabel="Mês", ylabel="Média de acidentes por estação-dia", xticks=range(1, 13))
    caminhos.append(_salvar(figura, pasta / "06_media_acidentes_mes.png"))

    cobertura = dados.groupby(["codigo_wmo", "nome_estacao"], as_index=False).agg(
        estacao_dias=("data_local", "size"),
        dias_validos=("precipitacao_mm_dia", "count"),
    )
    cobertura["cobertura_pct"] = 100 * cobertura["dias_validos"] / cobertura["estacao_dias"]
    figura, eixo = plt.subplots(figsize=(10, max(4, 0.35 * len(cobertura))))
    sns.barplot(data=cobertura.sort_values("cobertura_pct"), x="cobertura_pct", y="nome_estacao", ax=eixo, color="#55a868")
    eixo.set(title="Cobertura de precipitação diária pelo critério de 23 horas", xlabel="Estação-dias válidos (%)", ylabel="Estação")
    caminhos.append(_salvar(figura, pasta / "07_cobertura_estacoes.png"))

    por_estacao = validos.groupby("nome_estacao", as_index=False).agg(media_acidentes=("acidentes", "mean"))
    figura, eixo = plt.subplots(figsize=(10, max(4, 0.35 * len(por_estacao))))
    sns.barplot(data=por_estacao.sort_values("media_acidentes"), x="media_acidentes", y="nome_estacao", ax=eixo, color="#8172b3")
    eixo.set(title="Média de acidentes por estação representada", xlabel="Média de acidentes por estação-dia válido", ylabel="Estação")
    caminhos.append(_salvar(figura, pasta / "08_media_acidentes_estacao.png"))
    return caminhos


def _formatar_float(valor: float, casas: int = 3) -> str:
    if pd.isna(valor):
        return "não calculado"
    return f"{valor:.{casas}f}".replace(".", ",")


def renderizar_resumo_m22(resumo: dict, metricas_integracao: dict) -> str:
    """Renderiza o relatório acadêmico com fatos, critérios e limitações."""

    faixas = resumo["faixas"]
    linhas_faixas = []
    for faixa in ORDEM_FAIXAS[:-1]:
        valores = faixas[faixa]
        linhas_faixas.append(
            f"| {faixa} | {valores['estacao_dias']} | {valores['acidentes']} | "
            f"{_formatar_float(valores['media_acidentes'], 3)} |"
        )
    alternativa = metricas_integracao.get("estrategia_alternativa", {})
    faixas_com_dados = {
        chave: valores
        for chave, valores in faixas.items()
        if valores["estacao_dias"] > 0
    }
    maior_faixa = max(
        faixas_com_dados,
        key=lambda chave: faixas_com_dados[chave]["media_acidentes"],
        default="sem faixa disponível",
    )
    meses = resumo.get("variacao_mensal", {})
    maior_mes = max(
        meses,
        key=lambda chave: meses[chave]["media_acidentes"],
        default="—",
    )
    estacoes = resumo.get("variacao_estacao", {})
    maior_estacao = max(
        estacoes,
        key=lambda chave: estacoes[chave]["media_acidentes"],
        default="—",
    )
    periodos_semana = resumo.get("variacao_fim_semana", {})
    media_uteis = periodos_semana.get("dias_uteis", {}).get("media_acidentes", np.nan)
    media_fim_semana = periodos_semana.get("fim_de_semana", {}).get(
        "media_acidentes", np.nan
    )
    return f"""# M2.2 — Integração e análise exploratória

## Recorte e rastreabilidade

- PRF: {metricas_integracao.get('acidentes_prf', 0)} acidentes na BR-101/SC em 2025, com horário interpretado como `America/Sao_Paulo`.
- Associação principal: {metricas_integracao.get('associados', 0)} acidentes associados à estação mais próxima em até 50 km; {metricas_integracao.get('sem_estacao', 0)} não associados.
- Estações representadas: {metricas_integracao.get('estacoes_representadas', 0)}.
- IDs duplicados sinalizados: {metricas_integracao.get('ids_duplicados', 0)}; coordenadas inválidas: {metricas_integracao.get('coordenadas_invalidas', 0)}.
- Distância média dos acidentes associados: {_formatar_float(metricas_integracao.get('distancia_media_km', np.nan), 2)} km.
- Download dos ZIPs informado pelo usuário: **31/10/2026**.
- Unidade analítica: estação-data local. A análise principal exige pelo menos 23 horas válidas.

## Qualidade e perdas

O calendário contém {resumo['estacao_dias_total']} estação-dias. O denominador principal é de **{resumo['estacao_dias_validos_23h']} estação-dias** com precipitação diária válida ({_formatar_float(resumo['cobertura_principal_pct'], 2)}%). Neles ocorreram {resumo['acidentes_em_dias_validos_23h']} dos {resumo['acidentes_total']} acidentes contabilizados no calendário.

Sensibilidade do critério de completude: 18 h = {resumo['sensibilidade_completude']['18h']} dias; 23 h = {resumo['sensibilidade_completude']['23h']} dias; 24 h = {resumo['sensibilidade_completude']['24h']} dias.

A alternativa restrita a estações com cobertura anual >=90% associou {alternativa.get('associados_alternativa', '—')} acidentes, trocou a estação de {alternativa.get('estacoes_trocadas', '—')} ocorrências comparáveis e alterou a distância média em {_formatar_float(alternativa.get('aumento_medio_distancia_km', np.nan), 2)} km. Sua amostra utilizável contém {alternativa.get('acidentes_com_chuva_valida', '—')} acidentes em {alternativa.get('estacao_dias_validos_23h', '—')} estação-dias válidos, uma diferença de {alternativa.get('ganho_acidentes_com_chuva_valida', '—')} acidentes em relação à associação principal. Ela é apresentada apenas como sensibilidade e não substitui a estação principal conforme a disponibilidade diária.

## Perguntas exploratórias

### A. Acidentes em função da precipitação

A correlação de Spearman usa {resumo['spearman_n']} estação-dias válidos: rho = {_formatar_float(resumo['spearman_rho'])}; p-valor = {_formatar_float(resumo['spearman_p_valor'])}. Esse resultado descreve associação monotônica no recorte e **não demonstra causalidade**.

### B. Distribuição por faixa de chuva

As faixas abaixo são critérios operacionais do projeto, não categorias oficiais de risco.

| Faixa | Estação-dias | Acidentes | Média de acidentes |
| --- | ---: | ---: | ---: |
{chr(10).join(linhas_faixas)}

A maior média observada entre as faixas com dados foi em **{maior_faixa}**. Essa comparação usa estação-dias, não exposição por volume de veículos.

### C. Variação temporal e espacial

Entre os meses com dados válidos, o mês {maior_mes} apresentou a maior média de acidentes por estação-dia ({_formatar_float(meses.get(maior_mes, {}).get('media_acidentes', np.nan), 3)}; n={meses.get(maior_mes, {}).get('estacao_dias', 0)}). A média foi {_formatar_float(media_uteis, 3)} nos dias úteis e {_formatar_float(media_fim_semana, 3)} no fim de semana. A estação com maior média foi **{maior_estacao}** ({_formatar_float(estacoes.get(maior_estacao, {}).get('media_acidentes', np.nan), 3)}; n={estacoes.get(maior_estacao, {}).get('estacao_dias', 0)}).

Essas diferenças podem refletir sazonalidade, localização, dia da semana, cobertura desigual e exposição ao tráfego, além da precipitação.

## Limitações

- Não há informação de **volume de tráfego**, velocidade praticada, obras ou exposição por segmento.
- A estação é uma aproximação espacial; distância, relevo e microclimas reduzem a representatividade local.
- A condição medida pelo INMET não é idêntica à condição meteorológica declarada no registro do acidente.
- Dias incompletos não são tratados como dias secos, e acidentes sem estação ou sem chuva diária válida permanecem documentados.
- As comparações são exploratórias e não permitem afirmar que chuva causa acidentes.

## Preparação para M3

Uma eventual modelagem deverá usar separação temporal: período inicial para desenvolvimento e meses finais preservados como teste. Limiares, transformações e seleção de variáveis deverão ser ajustados sem consultar o período de teste.
"""
