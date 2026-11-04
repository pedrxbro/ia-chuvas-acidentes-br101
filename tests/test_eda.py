from __future__ import annotations

import math

import pandas as pd

from ia_chuvas_acidentes.eda import (
    calcular_resumo_eda,
    classificar_faixa_chuva,
    renderizar_resumo_m22,
)


def _tabela() -> pd.DataFrame:
    tabela = pd.DataFrame(
        {
            "codigo_wmo": ["A001"] * 5,
            "nome_estacao": ["ESTACAO TESTE"] * 5,
            "data_local": pd.date_range("2025-01-01", periods=5, freq="D"),
            "precipitacao_mm_dia": [0.0, 5.0, 15.0, 40.0, None],
            "precipitacao_mm_observada": [0.0, 5.0, 15.0, 40.0, 100.0],
            "acidentes": [0, 1, 2, 4, 9],
            "completo_18h": [True, True, True, True, True],
            "completo_23h": [True, True, True, True, False],
            "completo_24h": [True, True, False, False, False],
        }
    )
    tabela["mes"] = tabela["data_local"].dt.month
    tabela["fim_semana"] = tabela["data_local"].dt.day_of_week.ge(5)
    return tabela


def test_classificar_faixa_chuva_preserva_ausencia_e_limites_operacionais():
    resultado = classificar_faixa_chuva(
        pd.Series([None, 0.0, 0.1, 9.9, 10.0, 29.9, 30.0])
    )

    assert resultado.tolist() == [
        "Sem medição completa",
        "Sem chuva (0 mm)",
        "Chuva leve (>0 e <10 mm)",
        "Chuva leve (>0 e <10 mm)",
        "Chuva moderada (10 a <30 mm)",
        "Chuva moderada (10 a <30 mm)",
        "Chuva intensa (>=30 mm)",
    ]


def test_calcular_resumo_eda_usa_somente_cobertura_principal_no_denominador():
    resumo = calcular_resumo_eda(_tabela())

    assert resumo["estacao_dias_total"] == 5
    assert resumo["estacao_dias_validos_23h"] == 4
    assert resumo["acidentes_total"] == 16
    assert resumo["acidentes_em_dias_validos_23h"] == 7
    assert resumo["sensibilidade_completude"] == {"18h": 5, "23h": 4, "24h": 2}
    assert resumo["spearman_n"] == 4
    assert resumo["spearman_rho"] == 1.0
    assert resumo["faixas"]["Sem chuva (0 mm)"]["estacao_dias"] == 1
    assert resumo["faixas"]["Chuva intensa (>=30 mm)"]["media_acidentes"] == 4.0
    assert resumo["variacao_mensal"][1]["estacao_dias"] == 4
    assert resumo["variacao_fim_semana"]["fim_de_semana"]["media_acidentes"] == 4.0
    assert resumo["variacao_estacao"]["ESTACAO TESTE"]["acidentes"] == 7


def test_calcular_resumo_eda_nao_calcula_spearman_com_amostra_insuficiente():
    tabela = _tabela().iloc[:2].copy()

    resumo = calcular_resumo_eda(tabela)

    assert resumo["spearman_n"] == 2
    assert math.isnan(resumo["spearman_rho"])
    assert math.isnan(resumo["spearman_p_valor"])


def test_renderizar_resumo_declara_denominador_e_limite_causal():
    resumo = calcular_resumo_eda(_tabela())

    texto = renderizar_resumo_m22(
        resumo,
        {
            "acidentes_prf": 16,
            "associados": 12,
            "sem_estacao": 4,
            "estacoes_representadas": 1,
            "ids_duplicados": 0,
            "coordenadas_invalidas": 1,
            "distancia_media_km": 12.5,
            "estrategia_alternativa": {
                "associados_alternativa": 13,
                "estacao_dias_validos_23h": 4,
                "acidentes_com_chuva_valida": 8,
                "ganho_acidentes_com_chuva_valida": 1,
            },
        },
    )

    assert "4 estação-dias" in texto
    assert "31/10/2026" in texto
    assert "não demonstra causalidade" in texto
    assert "volume de tráfego" in texto
    assert "fim de semana" in texto
    assert "ESTACAO TESTE" in texto
    assert "amostra utilizável" in texto
