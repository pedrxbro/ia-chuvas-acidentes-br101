"""Preparação temporal e agregação diária para a etapa M2.2."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from .inmet import LeituraEstacao


FUSO_LOCAL = "America/Sao_Paulo"


def validar_prf_m22(dados: pd.DataFrame, ano: int = 2025) -> pd.DataFrame:
    """Filtra o ano e acrescenta indicadores auditáveis sem apagar originais."""

    obrigatorias = {
        "id",
        "data_acidente",
        "data_hora_acidente_sp",
        "latitude_num",
        "longitude_num",
    }
    ausentes = sorted(obrigatorias - set(dados.columns))
    if ausentes:
        raise ValueError(f"Campos PRF ausentes para a M2.2: {', '.join(ausentes)}")

    datas = pd.to_datetime(dados["data_acidente"], errors="coerce")
    resultado = dados.loc[datas.dt.year.eq(ano)].copy().reset_index(drop=True)
    ids = resultado["id"].astype("string").fillna("").str.strip()
    resultado["id_valido"] = ids.ne("")
    resultado["id_duplicado"] = ids.duplicated(keep=False) & resultado["id_valido"]
    resultado["data_hora_valida"] = resultado["data_hora_acidente_sp"].notna()

    latitudes = pd.to_numeric(resultado["latitude_num"], errors="coerce")
    longitudes = pd.to_numeric(resultado["longitude_num"], errors="coerce")
    resultado["coordenadas_validas"] = latitudes.between(-90, 90) & longitudes.between(
        -180, 180
    )

    horarios = resultado["data_hora_acidente_sp"]
    if getattr(horarios.dt, "tz", None) is None:
        horarios = horarios.dt.tz_localize(
            FUSO_LOCAL, ambiguous="NaT", nonexistent="NaT"
        )
    else:
        horarios = horarios.dt.tz_convert(FUSO_LOCAL)
    resultado["data_local"] = horarios.dt.tz_localize(None).dt.normalize()
    return resultado


def _observacoes_inmet(estacoes: Sequence[LeituraEstacao]) -> pd.DataFrame:
    partes: list[pd.DataFrame] = []
    for estacao in estacoes:
        dados = estacao.dados.loc[
            :, ["data_hora_utc", "precipitacao_mm", "status_precipitacao"]
        ].copy()
        dados["codigo_wmo"] = estacao.metadados.codigo_wmo
        dados["nome_estacao"] = estacao.metadados.nome
        dados["latitude_estacao"] = estacao.metadados.latitude
        dados["longitude_estacao"] = estacao.metadados.longitude
        partes.append(dados)
    if not partes:
        return pd.DataFrame(
            columns=[
                "data_hora_utc",
                "precipitacao_mm",
                "status_precipitacao",
                "codigo_wmo",
                "nome_estacao",
                "latitude_estacao",
                "longitude_estacao",
            ]
        )
    return pd.concat(partes, ignore_index=True)


def agregar_precipitacao_diaria(
    estacoes: Sequence[LeituraEstacao], min_horas: int = 23
) -> pd.DataFrame:
    """Agrega chuva por estação e data local, mantendo cobertura e soma bruta."""

    if not 1 <= min_horas <= 24:
        raise ValueError("min_horas deve estar entre 1 e 24")

    observacoes = _observacoes_inmet(estacoes)
    if observacoes.empty:
        return observacoes

    observacoes["data_hora_utc"] = pd.to_datetime(
        observacoes["data_hora_utc"], errors="coerce", utc=True
    )
    observacoes = observacoes.loc[observacoes["data_hora_utc"].notna()].copy()
    observacoes["data_hora_local"] = observacoes["data_hora_utc"].dt.tz_convert(
        FUSO_LOCAL
    )
    observacoes["data_local"] = (
        observacoes["data_hora_local"].dt.tz_localize(None).dt.normalize()
    )
    observacoes["precipitacao_mm"] = pd.to_numeric(
        observacoes["precipitacao_mm"], errors="coerce"
    )
    observacoes["medicao_valida"] = observacoes["status_precipitacao"].isin(
        ["zero", "positiva"]
    ) & observacoes["precipitacao_mm"].notna()
    observacoes["timestamp_duplicado"] = observacoes.duplicated(
        ["codigo_wmo", "data_hora_utc"], keep=False
    )
    unicas = observacoes.drop_duplicates(
        ["codigo_wmo", "data_hora_utc"], keep="first"
    )

    chaves = [
        "codigo_wmo",
        "nome_estacao",
        "latitude_estacao",
        "longitude_estacao",
        "data_local",
    ]

    def resumir(grupo: pd.DataFrame) -> pd.Series:
        validas = grupo.loc[grupo["medicao_valida"], "precipitacao_mm"]
        return pd.Series(
            {
                "horas_registradas": int(grupo["data_hora_utc"].nunique()),
                "horas_validas": int(grupo["medicao_valida"].sum()),
                "horas_ausentes": int((~grupo["medicao_valida"]).sum()),
                "precipitacao_mm_observada": validas.sum(min_count=1),
                "data_hora_local_inicial": grupo["data_hora_local"].min(),
                "data_hora_local_final": grupo["data_hora_local"].max(),
            }
        )

    diario = unicas.groupby(chaves, dropna=False, sort=True).apply(
        resumir, include_groups=False
    ).reset_index()
    duplicados_dia = (
        observacoes.loc[observacoes["timestamp_duplicado"]]
        .groupby(["codigo_wmo", "data_local"], sort=True)
        .size()
        .rename("linhas_em_timestamps_duplicados")
        .reset_index()
    )
    diario = diario.merge(
        duplicados_dia, on=["codigo_wmo", "data_local"], how="left", validate="one_to_one"
    )
    diario["linhas_em_timestamps_duplicados"] = diario[
        "linhas_em_timestamps_duplicados"
    ].fillna(0).astype(int)
    for limite in (18, 23, 24):
        diario[f"completo_{limite}h"] = diario["horas_validas"].ge(limite)
    diario["precipitacao_mm_dia"] = diario["precipitacao_mm_observada"].where(
        diario["horas_validas"].ge(min_horas)
    )
    diario["criterio_min_horas"] = min_horas
    diario["status_cobertura"] = "incompleta"
    diario.loc[diario["horas_validas"].eq(0), "status_cobertura"] = "sem_medicao"
    diario.loc[
        diario["horas_validas"].ge(min_horas), "status_cobertura"
    ] = "completa"
    return diario.sort_values(["codigo_wmo", "data_local"]).reset_index(drop=True)
