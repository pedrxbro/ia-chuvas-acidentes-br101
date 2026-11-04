"""Integração espacial e temporal auditável da M2.2."""

from __future__ import annotations

import numpy as np
import pandas as pd


RAIO_TERRA_KM = 6371.0088


def haversine_km(
    latitude_origem,
    longitude_origem,
    latitude_destino,
    longitude_destino,
):
    """Calcula distância de grande círculo em quilômetros."""

    lat1 = np.radians(latitude_origem)
    lon1 = np.radians(longitude_origem)
    lat2 = np.radians(latitude_destino)
    lon2 = np.radians(longitude_destino)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = np.sin(delta_lat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(
        delta_lon / 2
    ) ** 2
    return 2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))


def associar_estacoes(
    acidentes: pd.DataFrame,
    estacoes: pd.DataFrame,
    limite_km: float = 50.0,
    estrategia: str = "mais_proxima",
) -> pd.DataFrame:
    """Associa cada linha de acidente a no máximo uma estação."""

    obrigatorias_acidente = {"latitude_num", "longitude_num"}
    obrigatorias_estacao = {
        "codigo_wmo",
        "nome_estacao",
        "latitude_estacao",
        "longitude_estacao",
    }
    faltantes = sorted(obrigatorias_acidente - set(acidentes.columns))
    if faltantes:
        raise ValueError(f"Campos de acidente ausentes: {', '.join(faltantes)}")
    faltantes = sorted(obrigatorias_estacao - set(estacoes.columns))
    if faltantes:
        raise ValueError(f"Campos de estação ausentes: {', '.join(faltantes)}")

    estacoes_validas = estacoes.copy()
    estacoes_validas["latitude_estacao"] = pd.to_numeric(
        estacoes_validas["latitude_estacao"], errors="coerce"
    )
    estacoes_validas["longitude_estacao"] = pd.to_numeric(
        estacoes_validas["longitude_estacao"], errors="coerce"
    )
    estacoes_validas = estacoes_validas.loc[
        estacoes_validas["latitude_estacao"].between(-90, 90)
        & estacoes_validas["longitude_estacao"].between(-180, 180)
    ].drop_duplicates("codigo_wmo", keep="first")

    saida = acidentes.copy().reset_index(drop=True)
    saida["indice_acidente_origem"] = np.arange(len(saida), dtype=int)
    saida["codigo_wmo"] = pd.Series(pd.NA, index=saida.index, dtype="string")
    saida["nome_estacao"] = pd.Series(pd.NA, index=saida.index, dtype="string")
    saida["latitude_estacao"] = np.nan
    saida["longitude_estacao"] = np.nan
    saida["distancia_estacao_km"] = np.nan
    saida["distancia_estacao_mais_proxima_km"] = np.nan
    saida["status_associacao"] = "sem_coordenadas"
    saida["estrategia_associacao"] = estrategia
    saida["limite_distancia_km"] = float(limite_km)

    for indice, acidente in saida.iterrows():
        latitude = pd.to_numeric(pd.Series([acidente["latitude_num"]]), errors="coerce").iloc[0]
        longitude = pd.to_numeric(pd.Series([acidente["longitude_num"]]), errors="coerce").iloc[0]
        coordenadas_validas = bool(
            pd.notna(latitude)
            and pd.notna(longitude)
            and -90 <= latitude <= 90
            and -180 <= longitude <= 180
        )
        if not coordenadas_validas:
            continue
        if estacoes_validas.empty:
            saida.at[indice, "status_associacao"] = "sem_estacoes"
            continue

        candidatas = estacoes_validas.copy()
        candidatas["distancia"] = haversine_km(
            float(latitude),
            float(longitude),
            candidatas["latitude_estacao"].to_numpy(),
            candidatas["longitude_estacao"].to_numpy(),
        )
        escolhida = candidatas.sort_values(
            ["distancia", "codigo_wmo"], kind="mergesort"
        ).iloc[0]
        distancia = float(escolhida["distancia"])
        saida.at[indice, "distancia_estacao_mais_proxima_km"] = distancia
        if distancia > limite_km:
            saida.at[indice, "status_associacao"] = "fora_limite"
            continue
        saida.at[indice, "codigo_wmo"] = escolhida["codigo_wmo"]
        saida.at[indice, "nome_estacao"] = escolhida["nome_estacao"]
        saida.at[indice, "latitude_estacao"] = escolhida["latitude_estacao"]
        saida.at[indice, "longitude_estacao"] = escolhida["longitude_estacao"]
        saida.at[indice, "distancia_estacao_km"] = distancia
        saida.at[indice, "status_associacao"] = "associado"
    return saida


def comparar_estrategia_cobertura(
    associacoes_principais: pd.DataFrame,
    acidentes: pd.DataFrame,
    estacoes: pd.DataFrame,
    limite_km: float = 50.0,
    cobertura_minima_pct: float = 90.0,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    """Compara a associação principal com estações de alta cobertura anual."""

    if "cobertura_anual_pct" not in estacoes:
        raise ValueError("cobertura_anual_pct é obrigatória para a estratégia alternativa")
    elegiveis = estacoes.loc[
        pd.to_numeric(estacoes["cobertura_anual_pct"], errors="coerce").ge(
            cobertura_minima_pct
        )
    ].copy()
    alternativa = associar_estacoes(
        acidentes,
        elegiveis,
        limite_km=limite_km,
        estrategia=f"cobertura_anual_{cobertura_minima_pct:g}pct",
    )

    principal = associacoes_principais.set_index("indice_acidente_origem")
    alternativa_idx = alternativa.set_index("indice_acidente_origem")
    comparacao = principal[["codigo_wmo", "status_associacao", "distancia_estacao_km"]].merge(
        alternativa_idx[["codigo_wmo", "status_associacao", "distancia_estacao_km"]],
        left_index=True,
        right_index=True,
        suffixes=("_principal", "_alternativa"),
        how="outer",
        validate="one_to_one",
    )
    ambos = comparacao["status_associacao_principal"].eq("associado") & comparacao[
        "status_associacao_alternativa"
    ].eq("associado")
    diferenca = (
        comparacao.loc[ambos, "distancia_estacao_km_alternativa"]
        - comparacao.loc[ambos, "distancia_estacao_km_principal"]
    )
    resumo: dict[str, float | int] = {
        "cobertura_minima_pct": float(cobertura_minima_pct),
        "estacoes_elegiveis": int(len(elegiveis)),
        "associados_principal": int(
            comparacao["status_associacao_principal"].eq("associado").sum()
        ),
        "associados_alternativa": int(
            comparacao["status_associacao_alternativa"].eq("associado").sum()
        ),
        "estacoes_trocadas": int(
            (
                ambos
                & comparacao["codigo_wmo_principal"].ne(
                    comparacao["codigo_wmo_alternativa"]
                )
            ).sum()
        ),
        "aumento_medio_distancia_km": float(diferenca.mean()) if not diferenca.empty else np.nan,
    }
    return alternativa, resumo


def construir_tabela_estacao_dia(
    associacoes: pd.DataFrame,
    precipitacao_diaria: pd.DataFrame,
    ano: int = 2025,
) -> pd.DataFrame:
    """Constrói calendário completo das estações representadas e integra chuva."""

    chaves = ["codigo_wmo", "data_local"]
    if precipitacao_diaria.duplicated(chaves).any():
        raise ValueError("Há chave de precipitação diária repetida")

    associadas = associacoes.loc[
        associacoes["status_associacao"].eq("associado")
        & associacoes["codigo_wmo"].notna()
    ].copy()
    codigos = sorted(associadas["codigo_wmo"].astype(str).unique())
    if not codigos:
        return pd.DataFrame(columns=[*chaves, "acidentes"])

    datas = pd.date_range(f"{ano}-01-01", f"{ano}-12-31", freq="D")
    calendario = pd.MultiIndex.from_product(
        [codigos, datas], names=chaves
    ).to_frame(index=False)

    metadados_assoc = associadas[
        ["codigo_wmo", "nome_estacao", "latitude_estacao", "longitude_estacao"]
    ].drop_duplicates("codigo_wmo")
    calendario = calendario.merge(
        metadados_assoc, on="codigo_wmo", how="left", validate="many_to_one"
    )

    associadas["data_local"] = pd.to_datetime(
        associadas["data_local"], errors="coerce"
    ).dt.normalize()
    if "mortos_num" not in associadas:
        associadas["mortos_num"] = 0
    if "feridos_num" not in associadas:
        associadas["feridos_num"] = 0
    contagens = (
        associadas.loc[associadas["data_local"].dt.year.eq(ano)]
        .groupby(chaves, sort=True)
        .agg(
            acidentes=("indice_acidente_origem", "size"),
            mortos=("mortos_num", "sum"),
            feridos=("feridos_num", "sum"),
        )
        .reset_index()
    )
    tabela = calendario.merge(
        contagens, on=chaves, how="left", validate="one_to_one"
    )
    for coluna in ("acidentes", "mortos", "feridos"):
        tabela[coluna] = tabela[coluna].fillna(0).astype(int)

    chuva = precipitacao_diaria.copy()
    chuva["data_local"] = pd.to_datetime(chuva["data_local"], errors="coerce").dt.normalize()
    chuva = chuva.loc[
        chuva["codigo_wmo"].astype(str).isin(codigos)
        & chuva["data_local"].dt.year.eq(ano)
    ]
    colunas_repetidas = {
        "nome_estacao",
        "latitude_estacao",
        "longitude_estacao",
    } & set(chuva.columns)
    chuva = chuva.drop(columns=sorted(colunas_repetidas))
    tabela = tabela.merge(chuva, on=chaves, how="left", validate="one_to_one")
    tabela["mes"] = tabela["data_local"].dt.month
    tabela["dia_semana"] = tabela["data_local"].dt.day_name(locale=None)
    tabela["fim_semana"] = tabela["data_local"].dt.day_of_week.ge(5)
    return tabela.sort_values(chaves).reset_index(drop=True)
