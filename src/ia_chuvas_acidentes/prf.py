"""Leitura dos registros de acidentes da PRF."""

from __future__ import annotations

from io import TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from .formatos import detectar_formato_csv


CAMPOS_RELEVANTES = (
    "id",
    "data_inversa",
    "horario",
    "uf",
    "br",
    "municipio",
    "km",
    "latitude",
    "longitude",
    "mortos",
    "feridos",
    "classificacao_acidente",
    "condicao_metereologica",
)


def _numero_decimal(coluna: pd.Series) -> pd.Series:
    texto = coluna.astype("string").str.strip().replace({"": pd.NA, "NA": pd.NA})
    return pd.to_numeric(texto.str.replace(",", ".", regex=False), errors="coerce")


def _localizar_membro_prf(arquivo: ZipFile) -> str:
    membros = [
        nome
        for nome in arquivo.namelist()
        if not nome.endswith("/") and Path(nome).name.lower() == "datatran2025.csv"
    ]
    if len(membros) != 1:
        raise ValueError(
            "Era esperado exatamente um membro chamado datatran2025.csv "
            f"no ZIP; encontrados: {len(membros)}"
        )
    return membros[0]


def ler_prf(caminho_zip: str | Path) -> pd.DataFrame:
    """Lê a fonte PRF preservando texto bruto e adicionando campos tipados."""

    with ZipFile(caminho_zip) as arquivo:
        membro = _localizar_membro_prf(arquivo)
        formato = detectar_formato_csv(caminho_zip, membro)
        with arquivo.open(membro) as bruto:
            texto = TextIOWrapper(bruto, encoding=formato.codificacao, newline="")
            dados = pd.read_csv(
                texto,
                sep=formato.separador,
                dtype=str,
                keep_default_na=False,
            )

    ausentes = sorted(set(CAMPOS_RELEVANTES) - set(dados.columns))
    if ausentes:
        raise ValueError(f"Campos obrigatórios ausentes na PRF: {', '.join(ausentes)}")

    dados["data_acidente"] = pd.to_datetime(
        dados["data_inversa"], format="%Y-%m-%d", errors="coerce"
    )
    dados["data_hora_acidente"] = pd.to_datetime(
        dados["data_inversa"].str.strip() + " " + dados["horario"].str.strip(),
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )
    dados["br_num"] = _numero_decimal(dados["br"]).astype("Int64")
    dados["km_num"] = _numero_decimal(dados["km"])
    dados["latitude_num"] = _numero_decimal(dados["latitude"])
    dados["longitude_num"] = _numero_decimal(dados["longitude"])
    dados["mortos_num"] = _numero_decimal(dados["mortos"]).astype("Int64")
    dados["feridos_num"] = _numero_decimal(dados["feridos"]).astype("Int64")
    return dados


def filtrar_prf_sc_br101(dados: pd.DataFrame) -> pd.DataFrame:
    """Retorna o recorte de acidentes em SC na BR-101."""

    mascara = dados["uf"].str.strip().str.upper().eq("SC") & dados["br_num"].eq(101)
    return dados.loc[mascara].copy().reset_index(drop=True)
