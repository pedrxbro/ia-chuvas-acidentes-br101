from __future__ import annotations

from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from ia_chuvas_acidentes.formatos import detectar_formato_csv
from ia_chuvas_acidentes.prf import filtrar_prf_sc_br101, ler_prf


CABECALHO = (
    '"id";"data_inversa";"horario";"uf";"br";"municipio";"km";'
    '"latitude";"longitude";"mortos";"feridos";'
    '"classificacao_acidente";"condicao_metereologica"\r\n'
)


def criar_zip_prf(tmp_path, incluir_timestamp_invalido=False):
    linhas = [
        '1;2025-01-01;"06:20:00";"SC";101;"SÃO JOSÉ";207,4;-27,6000;-48,6200;0;1;"Com Vítimas Feridas";"Nublado"',
        '2;2025-01-02;"07:00:00";"SC";282;"LAGES";10;"";"";0;0;"Sem Vítimas";"Céu Claro"',
        '3;2025-01-03;"08:15:00";"PR";101;"CURITIBA";5,5;-25,4;-49,2;1;2;"Com Vítimas Fatais";"Chuva"',
    ]
    if incluir_timestamp_invalido:
        linhas.append(
            '4;2025-99-99;"25:70:00";"SC";101;"PALHOÇA";220;-27,64;-48,67;0;0;"Sem Vítimas";"Céu Claro"'
        )
    caminho = tmp_path / "datatran.zip"
    conteudo = (CABECALHO + "\r\n".join(linhas) + "\r\n").encode("cp1252")
    with ZipFile(caminho, "w", ZIP_DEFLATED) as arquivo:
        arquivo.writestr("datatran2025.csv", conteudo)
    return caminho


def test_detecta_cp1252_e_ponto_e_virgula_no_membro_prf(tmp_path):
    caminho = criar_zip_prf(tmp_path)

    formato = detectar_formato_csv(caminho, "datatran2025.csv")

    assert formato.codificacao == "cp1252"
    assert formato.separador == ";"


def test_le_prf_preservando_originais_e_criando_campos_padronizados(tmp_path):
    caminho = criar_zip_prf(tmp_path)

    dados = ler_prf(caminho)

    assert dados.loc[0, "municipio"] == "SÃO JOSÉ"
    assert dados.loc[0, "km"] == "207,4"
    assert dados.loc[0, "latitude"] == "-27,6000"
    assert dados.loc[0, "km_num"] == 207.4
    assert dados.loc[0, "latitude_num"] == -27.6
    assert dados.loc[0, "br_num"] == 101
    assert dados.loc[0, "feridos_num"] == 1
    assert dados.loc[0, "data_acidente"] == pd.Timestamp("2025-01-01")
    assert dados.loc[0, "data_hora_acidente"] == pd.Timestamp("2025-01-01 06:20:00")
    assert dados.loc[0, "data_hora_acidente_sp"] == pd.Timestamp(
        "2025-01-01 06:20:00", tz="America/Sao_Paulo"
    )
    assert dados.loc[0, "data_hora_acidente_utc"] == pd.Timestamp(
        "2025-01-01 09:20:00", tz="UTC"
    )
    assert pd.isna(dados.loc[1, "latitude_num"])


def test_timestamp_invalido_permanece_ausente_nos_campos_com_fuso(tmp_path):
    dados = ler_prf(criar_zip_prf(tmp_path, incluir_timestamp_invalido=True))

    assert pd.isna(dados.loc[3, "data_hora_acidente"])
    assert pd.isna(dados.loc[3, "data_hora_acidente_sp"])
    assert pd.isna(dados.loc[3, "data_hora_acidente_utc"])


def test_filtra_apenas_santa_catarina_e_br_101(tmp_path):
    dados = ler_prf(criar_zip_prf(tmp_path))

    filtrados = filtrar_prf_sc_br101(dados)

    assert filtrados["id"].tolist() == ["1"]
