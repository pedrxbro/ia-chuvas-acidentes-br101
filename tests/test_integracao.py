from __future__ import annotations

import pandas as pd
import pytest

from ia_chuvas_acidentes.integracao import (
    associar_estacoes,
    comparar_estrategia_cobertura,
    construir_tabela_estacao_dia,
    haversine_km,
)


def _acidentes() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": ["1", "2", "3"],
            "data_local": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
            "latitude_num": [0.0, 0.0, None],
            "longitude_num": [0.0, 2.0, None],
            "coordenadas_validas": [True, True, False],
            "mortos_num": [0, 1, 0],
            "feridos_num": [1, 0, 0],
        }
    )


def _estacoes() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "codigo_wmo": ["A001", "A002", "A003"],
            "nome_estacao": ["PRIMEIRA", "SEGUNDA", "DISTANTE"],
            "latitude_estacao": [0.0, 0.0, 10.0],
            "longitude_estacao": [0.1, -0.1, 10.0],
            "cobertura_anual_pct": [50.0, 95.0, 100.0],
        }
    )


def test_haversine_um_grau_de_latitude():
    assert haversine_km(0.0, 0.0, 1.0, 0.0) == pytest.approx(111.195, rel=1e-4)


def test_associar_estacoes_respeita_limite_coordenadas_e_desempate_wmo():
    resultado = associar_estacoes(_acidentes(), _estacoes(), limite_km=50)

    assert len(resultado) == 3
    assert resultado.loc[0, "codigo_wmo"] == "A001"
    assert resultado.loc[0, "status_associacao"] == "associado"
    assert resultado.loc[1, "status_associacao"] == "fora_limite"
    assert pd.isna(resultado.loc[1, "codigo_wmo"])
    assert resultado.loc[2, "status_associacao"] == "sem_coordenadas"
    assert resultado["id"].tolist() == ["1", "2", "3"]


def test_estrategia_de_cobertura_troca_estacao_e_registra_aumento_de_distancia():
    acidentes = _acidentes().iloc[[0]].copy()
    estacoes = _estacoes()
    principal = associar_estacoes(acidentes, estacoes, limite_km=50)

    alternativa, resumo = comparar_estrategia_cobertura(
        principal,
        acidentes,
        estacoes,
        limite_km=50,
        cobertura_minima_pct=90,
    )

    assert principal.loc[0, "codigo_wmo"] == "A001"
    assert alternativa.loc[0, "codigo_wmo"] == "A002"
    assert resumo["associados_principal"] == 1
    assert resumo["associados_alternativa"] == 1
    assert resumo["estacoes_trocadas"] == 1
    assert resumo["aumento_medio_distancia_km"] == pytest.approx(0.0, abs=1e-9)


def test_construir_tabela_estacao_dia_inclui_zero_acidentes_e_rejeita_chave_repetida():
    associacoes = associar_estacoes(_acidentes().iloc[[0]], _estacoes(), limite_km=50)
    precipitacao = pd.DataFrame(
        {
            "codigo_wmo": ["A001"],
            "nome_estacao": ["PRIMEIRA"],
            "latitude_estacao": [0.0],
            "longitude_estacao": [0.1],
            "data_local": pd.to_datetime(["2025-01-01"]),
            "horas_validas": [24],
            "precipitacao_mm_observada": [5.0],
            "precipitacao_mm_dia": [5.0],
            "completo_18h": [True],
            "completo_23h": [True],
            "completo_24h": [True],
            "status_cobertura": ["completa"],
        }
    )

    tabela = construir_tabela_estacao_dia(associacoes, precipitacao, ano=2025)

    assert len(tabela) == 365
    assert not tabela.duplicated(["codigo_wmo", "data_local"]).any()
    assert tabela.loc[tabela["data_local"].eq(pd.Timestamp("2025-01-01")), "acidentes"].item() == 1
    assert tabela.loc[tabela["data_local"].eq(pd.Timestamp("2025-01-02")), "acidentes"].item() == 0
    assert tabela.loc[tabela["data_local"].eq(pd.Timestamp("2025-01-01")), "precipitacao_mm_dia"].item() == 5.0

    repetida = pd.concat([precipitacao, precipitacao], ignore_index=True)
    with pytest.raises(ValueError, match="precipitação diária repetida"):
        construir_tabela_estacao_dia(associacoes, repetida, ano=2025)
