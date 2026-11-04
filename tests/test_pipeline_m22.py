from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pandas as pd

from ia_chuvas_acidentes.pipeline_m22 import executar_pipeline_m22
from tests.test_inmet import criar_zip_inmet
from tests.test_prf import criar_zip_prf


def test_pipeline_m22_grava_tabelas_auditaveis_com_caminhos_configuraveis(tmp_path):
    pasta_dados = tmp_path / "dados_processados"
    pasta_figuras = tmp_path / "figuras"
    caminho_relatorio = tmp_path / "relatorios" / "resumo.md"

    resultado = executar_pipeline_m22(
        caminho_prf=criar_zip_prf(tmp_path),
        caminho_inmet=criar_zip_inmet(tmp_path),
        pasta_dados=pasta_dados,
        pasta_figuras=pasta_figuras,
        caminho_relatorio=caminho_relatorio,
        gerar_graficos=False,
    )

    assert len(resultado.tabelas) == 6
    assert all(caminho.exists() for caminho in resultado.tabelas.values())
    assert resultado.relatorio == caminho_relatorio
    assert caminho_relatorio.exists()
    associacoes = pd.read_csv(resultado.tabelas["associacoes"])
    tabela = pd.read_csv(resultado.tabelas["estacao_dia"])
    assert len(associacoes) == 1
    assert associacoes["status_associacao"].tolist() == ["associado"]
    assert "alt_codigo_wmo" in associacoes
    assert resultado.metricas["distancia_media_km"] > 0
    alternativa = resultado.metricas["estrategia_alternativa"]
    assert "estacao_dias_validos_23h" in alternativa
    assert "acidentes_com_chuva_valida" in alternativa
    assert "ganho_acidentes_com_chuva_valida" in alternativa
    assert not tabela.duplicated(["codigo_wmo", "data_local"]).any()
    assert len(tabela) == 365
    assert (tabela["acidentes"] == 0).sum() == 364
    texto = caminho_relatorio.read_text(encoding="utf-8")
    assert "1 acidentes na BR-101/SC" in texto
    assert "31/10/2026" in texto


def test_cli_documentada_exibe_ajuda_sem_instalar_o_pacote():
    raiz = Path(__file__).resolve().parents[1]

    processo = subprocess.run(
        [sys.executable, str(raiz / "run_m22.py"), "--help"],
        cwd=raiz,
        capture_output=True,
        text=True,
        check=False,
    )

    assert processo.returncode == 0, processo.stderr
    assert "Executa a integração e EDA da M2.2" in processo.stdout
