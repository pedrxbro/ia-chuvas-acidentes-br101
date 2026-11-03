from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pandas as pd

from ia_chuvas_acidentes.diagnostico import (
    diagnosticar_inmet,
    diagnosticar_prf,
    gerar_artefatos,
)
from ia_chuvas_acidentes.inmet import ler_inmet_sc
from ia_chuvas_acidentes.prf import ler_prf
from tests.test_inmet import criar_zip_inmet
from tests.test_prf import criar_zip_prf


def test_diagnostica_totais_duplicidades_nulos_e_datas_prf(tmp_path):
    dados = ler_prf(criar_zip_prf(tmp_path))
    repetido = dados.iloc[[0]].copy()
    repetido["latitude"] = ""
    repetido["latitude_num"] = pd.NA
    dados = pd.concat([dados, repetido], ignore_index=True)

    diagnostico = diagnosticar_prf(dados)

    assert diagnostico["registros_total"] == 4
    assert diagnostico["registros_sc"] == 3
    assert diagnostico["registros_sc_br101"] == 2
    assert diagnostico["ids_duplicados"] == 1
    assert diagnostico["nulos_relevantes"]["latitude"] == 1
    assert diagnostico["data_inicial"] == "2025-01-01"
    assert diagnostico["data_final"] == "2025-01-01"


def test_diagnostica_cobertura_de_precipitacao_por_estacao(tmp_path):
    estacoes = ler_inmet_sc(criar_zip_inmet(tmp_path))

    resumo, cobertura = diagnosticar_inmet(estacoes, ano=2025)

    assert resumo["quantidade_estacoes"] == 2
    assert resumo["registros_total"] == 8
    assert resumo["medicoes_validas"] == 4
    assert resumo["precipitacao_zero"] == 2
    assert resumo["precipitacao_positiva"] == 2
    assert resumo["medicoes_ausentes"] == 2
    assert resumo["medicoes_invalidas"] == 2
    assert cobertura.loc["A806", "horas_esperadas"] == 8760
    assert cobertura.loc["A806", "horas_com_registro"] == 4
    assert cobertura.loc["A806", "timestamps_duplicados"] == 0
    assert cobertura.loc["A806", "medicoes_validas"] == 2
    assert cobertura.loc["A806", "horas_com_precipitacao_valida"] == 2
    assert cobertura.loc["A806", "cobertura_precipitacao_pct"] == 0.02


def test_cobertura_usa_timestamps_validos_unicos_e_dentro_do_ano(tmp_path):
    estacao = ler_inmet_sc(criar_zip_inmet(tmp_path))[0]
    duplicada = estacao.dados.iloc[[0]].copy()
    fora_do_ano = estacao.dados.iloc[[0]].copy()
    fora_do_ano["data_hora_utc"] = pd.Timestamp("2024-12-31 23:00:00+00:00")
    timestamp_invalido = estacao.dados.iloc[[0]].copy()
    timestamp_invalido["data_hora_utc"] = pd.NaT
    estacao.dados = pd.concat(
        [estacao.dados, duplicada, fora_do_ano, timestamp_invalido],
        ignore_index=True,
    )

    _, cobertura = diagnosticar_inmet([estacao], ano=2025)

    assert cobertura.loc["A806", "medicoes_validas"] == 5
    assert cobertura.loc["A806", "horas_com_precipitacao_valida"] == 2
    assert cobertura.loc["A806", "timestamps_duplicados"] == 1
    assert cobertura.loc["A806", "timestamps_fora_ano"] == 1
    assert cobertura.loc["A806", "cobertura_precipitacao_pct"] == 0.02


def test_diagnostico_inmet_registra_estacao_sem_timestamp_valido(tmp_path):
    estacao = ler_inmet_sc(criar_zip_inmet(tmp_path))[0]
    estacao.dados["data_hora_utc"] = pd.NaT

    resumo, cobertura = diagnosticar_inmet([estacao], ano=2025)

    assert resumo["data_inicial"] is None
    assert resumo["data_final"] is None
    assert cobertura.loc["A806", "timestamps_invalidos"] == 4
    assert cobertura.loc["A806", "horas_com_precipitacao_valida"] == 0
    assert cobertura.loc["A806", "cobertura_precipitacao_pct"] == 0.0


def test_gera_amostras_e_relatorio_a_partir_dos_zips(tmp_path):
    caminho_prf = criar_zip_prf(tmp_path)
    caminho_inmet = criar_zip_inmet(tmp_path)
    pasta_amostras = tmp_path / "samples"
    caminho_relatorio = tmp_path / "diagnostico.md"

    gerar_artefatos(
        caminho_prf,
        caminho_inmet,
        pasta_amostras,
        caminho_relatorio,
        tamanho_amostra=8,
        codigo_grupo="R",
    )

    amostra_a = pd.read_csv(pasta_amostras / "Grupo_R_Fonte_A.csv")
    amostra_b = pd.read_csv(pasta_amostras / "Grupo_R_Fonte_B.csv")
    relatorio = caminho_relatorio.read_text(encoding="utf-8")
    assert amostra_a["id"].tolist() == [1]
    assert {"data_hora_acidente_sp", "data_hora_acidente_utc"}.issubset(
        amostra_a.columns
    )
    assert set(amostra_b["status_precipitacao"]) == {
        "ausente",
        "invalida",
        "positiva",
        "zero",
    }
    assert len(amostra_b) == 8
    assert "associação espacial" in relatorio
    assert "Grupo_R_Fonte_A.csv" in relatorio
    assert "cobertura de 0,02%" in relatorio
    assert "America/Sao_Paulo" in relatorio
    assert (
        "https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/"
        "dados-abertos-da-prf" in relatorio
    )
    assert "https://portal.inmet.gov.br/dadoshistoricos/" in relatorio
    assert (
        "https://portal.inmet.gov.br/noticias/saiba-como-acessar-os-dados-"
        "meteorol%C3%B3gicos-dispon%C3%ADveis-no-site-do-inmet" in relatorio
    )
    assert "data original de download do ZIP local não foi registrada" in relatorio


def test_cli_executa_modulo_sem_aviso_de_importacao(tmp_path):
    caminho_prf = criar_zip_prf(tmp_path)
    caminho_inmet = criar_zip_inmet(tmp_path)
    raiz = Path(__file__).resolve().parents[1]
    ambiente = os.environ.copy()
    ambiente["PYTHONPATH"] = str(raiz / "src")

    processo = subprocess.run(
        [
            sys.executable,
            "-m",
            "ia_chuvas_acidentes.diagnostico",
            "--prf",
            str(caminho_prf),
            "--inmet",
            str(caminho_inmet),
            "--amostras",
            str(tmp_path / "saida"),
            "--relatorio",
            str(tmp_path / "saida.md"),
        ],
        cwd=raiz,
        env=ambiente,
        capture_output=True,
        text=True,
        check=False,
    )

    assert processo.returncode == 0, processo.stderr
    assert "RuntimeWarning" not in processo.stderr
