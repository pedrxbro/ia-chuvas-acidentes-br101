"""Detecção de formato para membros CSV armazenados em ZIP."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile


@dataclass(frozen=True)
class FormatoCSV:
    """Formato textual observado em um membro CSV."""

    codificacao: str
    separador: str


def detectar_formato_csv(caminho_zip: str | Path, membro: str) -> FormatoCSV:
    """Detecta codificação e separador sem extrair o membro do ZIP."""

    with ZipFile(caminho_zip) as arquivo:
        amostra_bytes = arquivo.read(membro)[:65_536]

    codificacao = "latin-1"
    texto = amostra_bytes.decode(codificacao)
    for candidata in ("utf-8-sig", "cp1252"):
        try:
            texto = amostra_bytes.decode(candidata)
        except UnicodeDecodeError:
            continue
        codificacao = candidata
        break

    candidatos = ";,\t|"
    try:
        separador = csv.Sniffer().sniff(texto, delimiters=candidatos).delimiter
    except csv.Error:
        contagens = {candidato: texto.count(candidato) for candidato in candidatos}
        separador = max(contagens, key=contagens.get)
        if contagens[separador] == 0:
            raise ValueError(f"Não foi possível detectar o separador de {membro}") from None
    return FormatoCSV(codificacao=codificacao, separador=separador)
