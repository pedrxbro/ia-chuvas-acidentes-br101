from __future__ import annotations

import pandas as pd

from ia_chuvas_acidentes.formatos import FormatoCSV
from ia_chuvas_acidentes.inmet import LeituraEstacao, MetadadosEstacao
from ia_chuvas_acidentes.preparacao import (
    agregar_precipitacao_diaria,
    validar_prf_m22,
)


def _estacao(horarios: list[str], precipitacoes: list[object]) -> LeituraEstacao:
    metadados = MetadadosEstacao(
        codigo_wmo="A999",
        nome="ESTACAO TESTE",
        latitude=-27.5,
        longitude=-48.5,
        originais={},
    )
    dados = pd.DataFrame(
        {
            "data_hora_utc": pd.to_datetime(horarios, utc=True),
            "precipitacao_mm": precipitacoes,
            "status_precipitacao": [
                "ausente" if pd.isna(valor) else "zero" if valor == 0 else "positiva"
                for valor in precipitacoes
            ],
        }
    )
    return LeituraEstacao(
        membro="teste.csv",
        formato=FormatoCSV(codificacao="cp1252", separador=";"),
        metadados=metadados,
        dados=dados,
    )


def test_validar_prf_m22_filtra_ano_e_sinaliza_ids_datas_e_coordenadas():
    dados = pd.DataFrame(
        {
            "id": ["10", "10", "", "13"],
            "data_acidente": pd.to_datetime(
                ["2025-01-01", "2025-01-02", "2025-01-03", "2024-12-31"]
            ),
            "data_hora_acidente_sp": pd.to_datetime(
                ["2025-01-01 08:00", "2025-01-02 09:00", None, "2024-12-31 23:00"]
            ).tz_localize("America/Sao_Paulo"),
            "latitude_num": [-27.6, -95.0, -27.7, -27.8],
            "longitude_num": [-48.6, -48.7, None, -48.8],
        }
    )

    resultado = validar_prf_m22(dados, ano=2025)

    assert resultado["id"].tolist() == ["10", "10", ""]
    assert resultado["id_valido"].tolist() == [True, True, False]
    assert resultado["id_duplicado"].tolist() == [True, True, False]
    assert resultado["data_hora_valida"].tolist() == [True, True, False]
    assert resultado["coordenadas_validas"].tolist() == [True, False, False]
    assert resultado.loc[0, "data_local"] == pd.Timestamp("2025-01-01")


def test_agregar_precipitacao_converte_utc_para_data_local_e_preserva_zero():
    estacao = _estacao(
        [
            "2025-01-01 00:00:00+00:00",
            "2025-01-01 03:00:00+00:00",
            "2025-01-01 04:00:00+00:00",
        ],
        [2.0, 0.0, 1.5],
    )

    diario = agregar_precipitacao_diaria([estacao], min_horas=1)

    assert diario["data_local"].tolist() == [
        pd.Timestamp("2024-12-31"),
        pd.Timestamp("2025-01-01"),
    ]
    assert diario["horas_validas"].tolist() == [1, 2]
    assert diario["precipitacao_mm_dia"].tolist() == [2.0, 1.5]
    assert diario["data_hora_local_inicial"].iloc[0] == pd.Timestamp(
        "2024-12-31 21:00:00", tz="America/Sao_Paulo"
    )


def test_agregar_precipitacao_mantem_soma_bruta_mas_mascara_dia_incompleto():
    horarios = pd.date_range("2025-01-01 03:00", periods=24, freq="h", tz="UTC")
    precipitacoes = [0.0] * 22 + [2.5, None]
    estacao = _estacao([str(valor) for valor in horarios], precipitacoes)

    diario = agregar_precipitacao_diaria([estacao], min_horas=23)
    linha = diario.loc[diario["data_local"].eq(pd.Timestamp("2025-01-01"))].iloc[0]

    assert linha["horas_validas"] == 23
    assert linha["precipitacao_mm_observada"] == 2.5
    assert linha["precipitacao_mm_dia"] == 2.5
    assert bool(linha["completo_18h"])
    assert bool(linha["completo_23h"])
    assert not bool(linha["completo_24h"])

    restrito = agregar_precipitacao_diaria([estacao], min_horas=24)
    linha_restrita = restrito.loc[
        restrito["data_local"].eq(pd.Timestamp("2025-01-01"))
    ].iloc[0]
    assert pd.isna(linha_restrita["precipitacao_mm_dia"])
    assert linha_restrita["status_cobertura"] == "incompleta"
