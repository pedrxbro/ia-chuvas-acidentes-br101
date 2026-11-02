from __future__ import annotations

from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from ia_chuvas_acidentes.inmet import (
    classificar_precipitacao,
    ler_estacao_inmet,
    ler_inmet_sc,
    listar_membros_sc,
)


def conteudo_estacao(uf="SC", codigo="A806", nome="FLORIANOPOLIS"):
    metadados = (
        f"REGIAO:;S\r\nUF:;{uf}\r\nESTACAO:;{nome}\r\n"
        f"CODIGO (WMO):;{codigo}\r\nLATITUDE:;-27,6025\r\n"
        "LONGITUDE:;-48,61999999\r\nALTITUDE:;4,87\r\n"
        "DATA DE FUNDACAO:;22/01/03\r\n"
    )
    cabecalho = "Data;Hora UTC;PRECIPITAÇÃO TOTAL, HORÁRIO (mm);\r\n"
    linhas = (
        "2025/01/01;0000 UTC;0;\r\n"
        "2025/01/01;0100 UTC;;\r\n"
        "2025/01/01;0200 UTC;1,2;\r\n"
        "2025/01/01;0300 UTC;inválido;\r\n"
    )
    return (metadados + cabecalho + linhas).encode("cp1252")


def criar_zip_inmet(tmp_path):
    caminho = tmp_path / "2025.zip"
    with ZipFile(caminho, "w", ZIP_DEFLATED) as arquivo:
        arquivo.writestr(
            "2025/INMET_S_SC_A806_FLORIANOPOLIS_01-01-2025_A_31-12-2025.CSV",
            conteudo_estacao(),
        )
        arquivo.writestr(
            "2025/INMET_S_SC_A866_LAGUNA_01-01-2025_A_31-12-2025.CSV",
            conteudo_estacao(codigo="A866", nome="LAGUNA"),
        )
        arquivo.writestr(
            "2025/INMET_S_PR_A807_CURITIBA_01-01-2025_A_31-12-2025.CSV",
            conteudo_estacao(uf="PR", codigo="A807", nome="CURITIBA"),
        )
    return caminho


def test_lista_somente_membros_de_santa_catarina(tmp_path):
    caminho = criar_zip_inmet(tmp_path)

    membros = listar_membros_sc(caminho)

    assert len(membros) == 2
    assert all("_SC_" in membro for membro in membros)


def test_le_metadados_timestamp_e_precipitacao_preservando_originais(tmp_path):
    caminho = criar_zip_inmet(tmp_path)
    membro = listar_membros_sc(caminho)[0]

    estacao = ler_estacao_inmet(caminho, membro)

    assert estacao.metadados.codigo_wmo == "A806"
    assert estacao.metadados.nome == "FLORIANOPOLIS"
    assert estacao.metadados.latitude == -27.6025
    assert estacao.metadados.longitude == -48.61999999
    assert estacao.metadados.originais["LATITUDE"] == "-27,6025"
    assert estacao.dados.loc[0, "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)"] == "0"
    assert estacao.dados["precipitacao_mm"].tolist()[:3] == [0.0, None, 1.2]
    assert estacao.dados["status_precipitacao"].tolist() == [
        "zero",
        "ausente",
        "positiva",
        "invalida",
    ]
    assert estacao.dados.loc[0, "data_hora_utc"] == pd.Timestamp(
        "2025-01-01 00:00:00+00:00"
    )


def test_classifica_zero_ausente_positivo_e_invalido():
    resultado = classificar_precipitacao(pd.Series(["", "0", "0,0", "2,4", "x"]))

    assert resultado.tolist() == ["ausente", "zero", "zero", "positiva", "invalida"]


def test_le_todas_as_estacoes_sc_sem_incluir_outros_estados(tmp_path):
    estacoes = ler_inmet_sc(criar_zip_inmet(tmp_path))

    assert [estacao.metadados.codigo_wmo for estacao in estacoes] == ["A806", "A866"]
