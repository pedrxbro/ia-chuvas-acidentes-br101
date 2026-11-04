"""Pipeline reproduzível de preparação, integração e EDA da M2.2."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .diagnostico import diagnosticar_inmet
from .eda import calcular_resumo_eda, gerar_figuras, renderizar_resumo_m22
from .inmet import LeituraEstacao, ler_inmet_sc
from .integracao import (
    associar_estacoes,
    comparar_estrategia_cobertura,
    construir_tabela_estacao_dia,
)
from .preparacao import agregar_precipitacao_diaria, validar_prf_m22
from .prf import filtrar_prf_sc_br101, ler_prf


@dataclass(frozen=True)
class ResultadoM22:
    """Caminhos e métricas produzidos por uma execução completa."""

    tabelas: dict[str, Path]
    figuras: tuple[Path, ...]
    relatorio: Path
    metricas: dict
    resumo_eda: dict


def _metadados_estacoes(
    estacoes: list[LeituraEstacao], cobertura: pd.DataFrame
) -> pd.DataFrame:
    linhas = [
        {
            "codigo_wmo": estacao.metadados.codigo_wmo,
            "nome_estacao": estacao.metadados.nome,
            "latitude_estacao": estacao.metadados.latitude,
            "longitude_estacao": estacao.metadados.longitude,
        }
        for estacao in estacoes
    ]
    metadados = pd.DataFrame(linhas).drop_duplicates("codigo_wmo")
    cobertura_pct = cobertura[["cobertura_precipitacao_pct"]].reset_index().rename(
        columns={"cobertura_precipitacao_pct": "cobertura_anual_pct"}
    )
    return metadados.merge(
        cobertura_pct, on="codigo_wmo", how="left", validate="one_to_one"
    )


def _metricas_cobertura(
    cobertura: pd.DataFrame,
    precipitacao_diaria: pd.DataFrame,
    associacoes: pd.DataFrame,
) -> pd.DataFrame:
    metricas = cobertura.reset_index().rename(
        columns={"cobertura_precipitacao_pct": "cobertura_anual_pct"}
    )
    dias = (
        precipitacao_diaria.groupby("codigo_wmo", sort=True)
        .agg(
            estacao_dias_observados=("data_local", "nunique"),
            estacao_dias_18h=("completo_18h", "sum"),
            estacao_dias_23h=("completo_23h", "sum"),
            estacao_dias_24h=("completo_24h", "sum"),
        )
        .reset_index()
    )
    associados = (
        associacoes.loc[associacoes["status_associacao"].eq("associado")]
        .groupby("codigo_wmo")
        .size()
        .rename("acidentes_associados")
        .reset_index()
    )
    metricas = metricas.merge(dias, on="codigo_wmo", how="left", validate="one_to_one")
    metricas = metricas.merge(
        associados, on="codigo_wmo", how="left", validate="one_to_one"
    )
    for coluna in (
        "estacao_dias_observados",
        "estacao_dias_18h",
        "estacao_dias_23h",
        "estacao_dias_24h",
        "acidentes_associados",
    ):
        metricas[coluna] = metricas[coluna].fillna(0).astype(int)
    return metricas.sort_values("codigo_wmo").reset_index(drop=True)


def _gravar_csv(dados: pd.DataFrame, caminho: Path) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados.to_csv(caminho, index=False, encoding="utf-8")
    return caminho


def executar_pipeline_m22(
    caminho_prf: str | Path = Path("data/raw/datatran2025.zip"),
    caminho_inmet: str | Path = Path("data/raw/2025.zip"),
    pasta_dados: str | Path = Path("data/processed"),
    pasta_figuras: str | Path = Path("reports/figures"),
    caminho_relatorio: str | Path = Path("reports/resumo_m22.md"),
    ano: int = 2025,
    min_horas: int = 23,
    limite_km: float = 50.0,
    cobertura_alternativa_pct: float = 90.0,
    gerar_graficos: bool = True,
) -> ResultadoM22:
    """Executa todas as transformações da M2.2 a partir dos ZIPs locais."""

    pasta_dados = Path(pasta_dados)
    pasta_figuras = Path(pasta_figuras)
    caminho_relatorio = Path(caminho_relatorio)
    pasta_dados.mkdir(parents=True, exist_ok=True)
    caminho_relatorio.parent.mkdir(parents=True, exist_ok=True)

    prf_original = ler_prf(caminho_prf)
    prf_recorte = validar_prf_m22(filtrar_prf_sc_br101(prf_original), ano=ano)
    estacoes = ler_inmet_sc(caminho_inmet)
    _, cobertura = diagnosticar_inmet(estacoes, ano=ano)
    precipitacao_diaria = agregar_precipitacao_diaria(estacoes, min_horas=min_horas)
    metadados = _metadados_estacoes(estacoes, cobertura)

    associacoes = associar_estacoes(
        prf_recorte,
        metadados,
        limite_km=limite_km,
        estrategia="mais_proxima",
    )
    alternativa, resumo_alternativa = comparar_estrategia_cobertura(
        associacoes,
        prf_recorte,
        metadados,
        limite_km=limite_km,
        cobertura_minima_pct=cobertura_alternativa_pct,
    )
    colunas_alternativa = [
        "indice_acidente_origem",
        "codigo_wmo",
        "nome_estacao",
        "distancia_estacao_km",
        "status_associacao",
    ]
    alternativa_saida = alternativa.loc[:, colunas_alternativa].rename(
        columns={
            coluna: f"alt_{coluna}"
            for coluna in colunas_alternativa
            if coluna != "indice_acidente_origem"
        }
    )
    associacoes_saida = associacoes.merge(
        alternativa_saida,
        on="indice_acidente_origem",
        how="left",
        validate="one_to_one",
    )
    nao_correspondidos = associacoes_saida.loc[
        ~associacoes_saida["status_associacao"].eq("associado")
    ].copy()
    tabela_estacao_dia = construir_tabela_estacao_dia(
        associacoes, precipitacao_diaria, ano=ano
    )
    tabela_estacao_dia_alternativa = construir_tabela_estacao_dia(
        alternativa, precipitacao_diaria, ano=ano
    )
    acidentes_principal_validos = int(
        tabela_estacao_dia.loc[
            tabela_estacao_dia["precipitacao_mm_dia"].notna(), "acidentes"
        ].sum()
    )
    if tabela_estacao_dia_alternativa.empty:
        estacao_dias_alternativos_validos = 0
        acidentes_alternativos_validos = 0
        estacoes_alternativas_representadas = 0
    else:
        mascara_alternativa_valida = tabela_estacao_dia_alternativa[
            "precipitacao_mm_dia"
        ].notna()
        estacao_dias_alternativos_validos = int(mascara_alternativa_valida.sum())
        acidentes_alternativos_validos = int(
            tabela_estacao_dia_alternativa.loc[
                mascara_alternativa_valida, "acidentes"
            ].sum()
        )
        estacoes_alternativas_representadas = int(
            tabela_estacao_dia_alternativa["codigo_wmo"].nunique()
        )
    resumo_alternativa.update(
        {
            "estacoes_representadas": estacoes_alternativas_representadas,
            "estacao_dias_validos_23h": estacao_dias_alternativos_validos,
            "acidentes_com_chuva_valida": acidentes_alternativos_validos,
            "acidentes_com_chuva_valida_principal": acidentes_principal_validos,
            "ganho_acidentes_com_chuva_valida": acidentes_alternativos_validos
            - acidentes_principal_validos,
        }
    )
    metricas_cobertura = _metricas_cobertura(
        cobertura, precipitacao_diaria, associacoes
    )

    resumo_eda = calcular_resumo_eda(tabela_estacao_dia)
    distancias_associadas = associacoes.loc[
        associacoes["status_associacao"].eq("associado"), "distancia_estacao_km"
    ].dropna()
    metricas = {
        "acidentes_prf": int(len(prf_recorte)),
        "ids_duplicados": int(prf_recorte["id_duplicado"].sum()),
        "datas_horas_invalidas": int((~prf_recorte["data_hora_valida"]).sum()),
        "coordenadas_invalidas": int((~prf_recorte["coordenadas_validas"]).sum()),
        "associados": int(associacoes["status_associacao"].eq("associado").sum()),
        "sem_estacao": int((~associacoes["status_associacao"].eq("associado")).sum()),
        "estacoes_representadas": int(
            associacoes.loc[
                associacoes["status_associacao"].eq("associado"), "codigo_wmo"
            ].nunique()
        ),
        "distancia_media_km": float(distancias_associadas.mean()),
        "distancia_mediana_km": float(distancias_associadas.median()),
        "distancia_p95_km": float(distancias_associadas.quantile(0.95)),
        "distancia_maxima_km": float(distancias_associadas.max()),
        "estrategia_alternativa": resumo_alternativa,
    }

    tabelas = {
        "prf_tratada": _gravar_csv(
            prf_recorte, pasta_dados / "prf_sc_br101_2025.csv"
        ),
        "precipitacao_diaria": _gravar_csv(
            precipitacao_diaria,
            pasta_dados / "inmet_precipitacao_diaria_2025.csv",
        ),
        "associacoes": _gravar_csv(
            associacoes_saida,
            pasta_dados / "associacao_acidente_estacao_2025.csv",
        ),
        "nao_correspondidos": _gravar_csv(
            nao_correspondidos, pasta_dados / "acidentes_sem_estacao_2025.csv"
        ),
        "estacao_dia": _gravar_csv(
            tabela_estacao_dia, pasta_dados / "tabela_estacao_dia_2025.csv"
        ),
        "metricas_cobertura": _gravar_csv(
            metricas_cobertura, pasta_dados / "metricas_cobertura_2025.csv"
        ),
    }
    figuras = (
        tuple(gerar_figuras(tabela_estacao_dia, pasta_figuras))
        if gerar_graficos
        else tuple()
    )
    caminho_relatorio.write_text(
        renderizar_resumo_m22(resumo_eda, metricas), encoding="utf-8"
    )
    return ResultadoM22(
        tabelas=tabelas,
        figuras=figuras,
        relatorio=caminho_relatorio,
        metricas=metricas,
        resumo_eda=resumo_eda,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Executa a integração e EDA da M2.2")
    parser.add_argument("--prf", type=Path, default=Path("data/raw/datatran2025.zip"))
    parser.add_argument("--inmet", type=Path, default=Path("data/raw/2025.zip"))
    parser.add_argument("--dados", type=Path, default=Path("data/processed"))
    parser.add_argument("--figuras", type=Path, default=Path("reports/figures"))
    parser.add_argument("--relatorio", type=Path, default=Path("reports/resumo_m22.md"))
    args = parser.parse_args(argv)
    resultado = executar_pipeline_m22(
        caminho_prf=args.prf,
        caminho_inmet=args.inmet,
        pasta_dados=args.dados,
        pasta_figuras=args.figuras,
        caminho_relatorio=args.relatorio,
    )
    print(
        f"Acidentes: {resultado.metricas['acidentes_prf']}; "
        f"associados: {resultado.metricas['associados']}; "
        f"estação-dias válidos: {resultado.resumo_eda['estacao_dias_validos_23h']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
