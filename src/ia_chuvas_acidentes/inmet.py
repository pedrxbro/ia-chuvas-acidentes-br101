"""Leitura das observações meteorológicas horárias do INMET."""

from __future__ import annotations

from dataclasses import dataclass
from io import TextIOWrapper
from pathlib import Path
import unicodedata
from zipfile import ZipFile

import pandas as pd

from .formatos import FormatoCSV, detectar_formato_csv


@dataclass(frozen=True)
class MetadadosEstacao:
    """Metadados padronizados e valores textuais originais da estação."""

    codigo_wmo: str
    nome: str
    latitude: float
    longitude: float
    originais: dict[str, str]


@dataclass
class LeituraEstacao:
    """Conteúdo de um arquivo de estação dentro do ZIP do INMET."""

    membro: str
    formato: FormatoCSV
    metadados: MetadadosEstacao
    dados: pd.DataFrame


def _sem_acentos(valor: str) -> str:
    normalizado = unicodedata.normalize("NFKD", valor)
    return "".join(caractere for caractere in normalizado if not unicodedata.combining(caractere))


def _decimal(valor: str) -> float:
    return float(valor.strip().replace(",", "."))


def _normalizar_precipitacao(valores: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Retorna o texto limpo e o valor numérico, mascarando sentinelas INMET."""

    textos = valores.astype("string").fillna("").str.strip()
    ausentes = textos.str.upper().isin({"", "NULL", "9999"})
    numeros = pd.to_numeric(
        textos.str.replace(",", ".", regex=False), errors="coerce"
    ).mask(ausentes)
    return textos, numeros


def listar_membros_sc(caminho_zip: str | Path) -> list[str]:
    """Lista os CSVs catarinenses sem descompactar o arquivo."""

    with ZipFile(caminho_zip) as arquivo:
        return sorted(
            nome
            for nome in arquivo.namelist()
            if not nome.endswith("/")
            and "_SC_" in Path(nome).name.upper()
            and nome.upper().endswith(".CSV")
        )


def classificar_precipitacao(valores: pd.Series) -> pd.Series:
    """Classifica a disponibilidade sem confundir zero com ausência."""

    textos, numeros = _normalizar_precipitacao(valores)
    ausentes = textos.str.upper().isin({"", "NULL", "9999"})
    resultado = pd.Series("invalida", index=valores.index, dtype="object")
    resultado.loc[ausentes] = "ausente"
    resultado.loc[numeros.eq(0) & ~ausentes] = "zero"
    resultado.loc[numeros.gt(0)] = "positiva"
    return resultado


def ler_estacao_inmet(caminho_zip: str | Path, membro: str) -> LeituraEstacao:
    """Lê metadados e observações de uma estação diretamente do ZIP."""

    formato = detectar_formato_csv(caminho_zip, membro)
    with ZipFile(caminho_zip) as arquivo:
        with arquivo.open(membro) as bruto:
            texto = TextIOWrapper(bruto, encoding=formato.codificacao, newline="")
            originais: dict[str, str] = {}
            for _ in range(8):
                linha = texto.readline().rstrip("\r\n")
                chave, separador, valor = linha.partition(formato.separador)
                if not separador:
                    raise ValueError(f"Linha de metadado inválida em {membro}: {linha!r}")
                originais[chave.rstrip(":").strip()] = valor.strip()

            dados = pd.read_csv(
                texto,
                sep=formato.separador,
                dtype=str,
                keep_default_na=False,
            )

    colunas_artificiais = [
        coluna
        for coluna in dados.columns
        if coluna.startswith("Unnamed:") and dados[coluna].astype("string").str.strip().eq("").all()
    ]
    dados = dados.drop(columns=colunas_artificiais)

    obrigatorios = {"CODIGO (WMO)", "ESTACAO", "LATITUDE", "LONGITUDE"}
    ausentes = sorted(obrigatorios - set(originais))
    if ausentes:
        raise ValueError(f"Metadados obrigatórios ausentes em {membro}: {', '.join(ausentes)}")

    metadados = MetadadosEstacao(
        codigo_wmo=originais["CODIGO (WMO)"],
        nome=originais["ESTACAO"],
        latitude=_decimal(originais["LATITUDE"]),
        longitude=_decimal(originais["LONGITUDE"]),
        originais=originais,
    )
    coluna_precipitacao = next(
        (
            coluna
            for coluna in dados.columns
            if _sem_acentos(coluna).upper().startswith("PRECIPITACAO TOTAL, HORARIO")
        ),
        None,
    )
    if coluna_precipitacao is None:
        raise ValueError(f"Coluna de precipitação horária não encontrada em {membro}")

    _, numeros = _normalizar_precipitacao(dados[coluna_precipitacao])
    dados["precipitacao_mm"] = pd.Series(
        [float(numero) if pd.notna(numero) else None for numero in numeros],
        index=dados.index,
        dtype="object",
    )
    dados["status_precipitacao"] = classificar_precipitacao(dados[coluna_precipitacao])
    dados["data_hora_utc"] = pd.to_datetime(
        dados["Data"].str.strip() + " " + dados["Hora UTC"].str.strip(),
        format="%Y/%m/%d %H%M UTC",
        errors="coerce",
        utc=True,
    )
    dados["codigo_wmo"] = metadados.codigo_wmo
    dados["nome_estacao"] = metadados.nome
    dados["latitude_estacao"] = metadados.latitude
    dados["longitude_estacao"] = metadados.longitude
    dados["membro_origem"] = membro
    return LeituraEstacao(
        membro=membro,
        formato=formato,
        metadados=metadados,
        dados=dados,
    )


def ler_inmet_sc(caminho_zip: str | Path) -> list[LeituraEstacao]:
    """Lê todas as estações catarinenses presentes no ZIP."""

    return [
        ler_estacao_inmet(caminho_zip, membro)
        for membro in listar_membros_sc(caminho_zip)
    ]
