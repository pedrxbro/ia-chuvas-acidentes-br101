"""Diagnóstico reprodutível das fontes PRF e INMET."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import unicodedata
from zipfile import ZipFile

import pandas as pd

from .formatos import detectar_formato_csv
from .inmet import LeituraEstacao, ler_inmet_sc
from .prf import CAMPOS_RELEVANTES, filtrar_prf_sc_br101, ler_prf


@dataclass
class ResultadoDiagnostico:
    """Resultados calculados e caminhos dos artefatos gerados."""

    prf: dict
    inmet: dict
    cobertura_inmet: pd.DataFrame
    amostra_prf: Path
    amostra_inmet: Path
    relatorio: Path


def _nulos_textuais(coluna: pd.Series) -> int:
    textos = coluna.astype("string").fillna("").str.strip()
    return int(textos.isin(["", "NA"]).sum())


def _iso(valor) -> str | None:
    return valor.date().isoformat() if pd.notna(valor) else None

def diagnosticar_prf(dados: pd.DataFrame) -> dict:
    """Calcula indicadores de qualidade para o recorte SC/BR-101."""

    recorte = filtrar_prf_sc_br101(dados)
    datas = recorte["data_acidente"].dropna()
    nulos = {
        campo: _nulos_textuais(recorte[campo])
        for campo in CAMPOS_RELEVANTES
    }
    return {
        "registros_total": int(len(dados)),
        "registros_sc": int(dados["uf"].str.strip().str.upper().eq("SC").sum()),
        "registros_sc_br101": int(len(recorte)),
        "ids_duplicados": int(recorte["id"].duplicated().sum()),
        "nulos_relevantes": nulos,
        "datas_invalidas": int(recorte["data_acidente"].isna().sum()),
        "data_hora_invalida": int(recorte["data_hora_acidente"].isna().sum()),
        "data_inicial": _iso(datas.min()) if not datas.empty else None,
        "data_final": _iso(datas.max()) if not datas.empty else None,
        "dias_com_registros": int(datas.dt.date.nunique()),
    }


def diagnosticar_inmet(
    estacoes: list[LeituraEstacao], ano: int = 2025
) -> tuple[dict, pd.DataFrame]:
    """Calcula cobertura horária e de precipitação por estação."""

    inicio_ano = pd.Timestamp(f"{ano}-01-01", tz="UTC")
    fim_ano = pd.Timestamp(f"{ano + 1}-01-01", tz="UTC")
    horas_esperadas = len(pd.date_range(inicio_ano, fim_ano, inclusive="left", freq="h"))
    linhas = []
    for estacao in estacoes:
        dados = estacao.dados
        timestamps = pd.to_datetime(dados["data_hora_utc"], errors="coerce", utc=True)
        validos_tempo = timestamps.dropna()
        dentro_ano = timestamps.ge(inicio_ano) & timestamps.lt(fim_ano)
        timestamps_no_ano = timestamps.loc[dentro_ano]
        contagens = dados["status_precipitacao"].value_counts()
        zeros = int(contagens.get("zero", 0))
        positivas = int(contagens.get("positiva", 0))
        medicoes_validas = zeros + positivas
        precipitacao_valida = dados["status_precipitacao"].isin(["zero", "positiva"])
        horas_com_precipitacao_valida = int(
            timestamps.loc[dentro_ano & precipitacao_valida].nunique()
        )
        horas_com_registro = int(timestamps_no_ano.nunique())
        linhas.append(
            {
                "codigo_wmo": estacao.metadados.codigo_wmo,
                "nome_estacao": estacao.metadados.nome,
                "latitude": estacao.metadados.latitude,
                "longitude": estacao.metadados.longitude,
                "registros": int(len(dados)),
                "horas_esperadas": horas_esperadas,
                "horas_com_registro": horas_com_registro,
                "horas_sem_registro": max(horas_esperadas - horas_com_registro, 0),
                "timestamps_duplicados": int(validos_tempo.duplicated().sum()),
                "timestamps_invalidos": int(timestamps.isna().sum()),
                "timestamps_fora_ano": int((~dentro_ano & timestamps.notna()).sum()),
                "data_inicial": _iso(validos_tempo.min()) if not validos_tempo.empty else None,
                "data_final": _iso(validos_tempo.max()) if not validos_tempo.empty else None,
                "medicoes_validas": medicoes_validas,
                "horas_com_precipitacao_valida": horas_com_precipitacao_valida,
                "precipitacao_zero": zeros,
                "precipitacao_positiva": positivas,
                "medicoes_ausentes": int(contagens.get("ausente", 0)),
                "medicoes_invalidas": int(contagens.get("invalida", 0)),
                "cobertura_precipitacao_pct": round(
                    100 * horas_com_precipitacao_valida / horas_esperadas, 2
                ),
            }
        )

    cobertura = pd.DataFrame(linhas).set_index("codigo_wmo").sort_index()
    if cobertura.empty:
        resumo = {
            "quantidade_estacoes": 0,
            "registros_total": 0,
            "medicoes_validas": 0,
            "precipitacao_zero": 0,
            "precipitacao_positiva": 0,
            "medicoes_ausentes": 0,
            "medicoes_invalidas": 0,
            "timestamps_duplicados": 0,
        }
        return resumo, cobertura

    datas_iniciais = cobertura["data_inicial"].dropna()
    datas_finais = cobertura["data_final"].dropna()
    resumo = {
        "quantidade_estacoes": int(len(cobertura)),
        "registros_total": int(cobertura["registros"].sum()),
        "medicoes_validas": int(cobertura["medicoes_validas"].sum()),
        "precipitacao_zero": int(cobertura["precipitacao_zero"].sum()),
        "precipitacao_positiva": int(cobertura["precipitacao_positiva"].sum()),
        "medicoes_ausentes": int(cobertura["medicoes_ausentes"].sum()),
        "medicoes_invalidas": int(cobertura["medicoes_invalidas"].sum()),
        "timestamps_duplicados": int(cobertura["timestamps_duplicados"].sum()),
        "data_inicial": datas_iniciais.min() if not datas_iniciais.empty else None,
        "data_final": datas_finais.max() if not datas_finais.empty else None,
        "latitude_min": float(cobertura["latitude"].min()),
        "latitude_max": float(cobertura["latitude"].max()),
        "longitude_min": float(cobertura["longitude"].min()),
        "longitude_max": float(cobertura["longitude"].max()),
    }
    return resumo, cobertura


def _sem_acentos(valor: str) -> str:
    normalizado = unicodedata.normalize("NFKD", valor)
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def _coluna_precipitacao(dados: pd.DataFrame) -> str:
    for coluna in dados.columns:
        if _sem_acentos(coluna).upper().startswith("PRECIPITACAO TOTAL, HORARIO"):
            return coluna
    raise ValueError("Coluna original de precipitação não encontrada")


def _amostrar_inmet(estacoes: list[LeituraEstacao], tamanho: int) -> pd.DataFrame:
    partes = []
    for estacao in estacoes:
        dados = estacao.dados.copy()
        dados["precipitacao_original"] = dados[_coluna_precipitacao(dados)]
        partes.append(dados)
    observacoes = pd.concat(partes, ignore_index=True)
    observacoes = observacoes.sort_values(
        ["codigo_wmo", "status_precipitacao", "data_hora_utc"], na_position="last"
    ).reset_index(drop=True)
    candidatos = observacoes.groupby(
        ["codigo_wmo", "status_precipitacao"], sort=True, dropna=False
    ).head(1)
    escolhidos = candidatos.head(tamanho)
    if len(escolhidos) < tamanho:
        restantes = observacoes.drop(index=escolhidos.index).head(tamanho - len(escolhidos))
        escolhidos = pd.concat([escolhidos, restantes])
    colunas = [
        "codigo_wmo",
        "nome_estacao",
        "latitude_estacao",
        "longitude_estacao",
        "Data",
        "Hora UTC",
        "precipitacao_original",
        "precipitacao_mm",
        "status_precipitacao",
        "data_hora_utc",
        "membro_origem",
    ]
    return escolhidos.loc[:, colunas].reset_index(drop=True)


def _tabela_markdown(colunas: list[str], linhas: list[list[object]]) -> str:
    def texto(valor: object) -> str:
        if valor is None or pd.isna(valor):
            return "—"
        return str(valor).replace("|", "\\|")

    cabecalho = "| " + " | ".join(colunas) + " |"
    separador = "| " + " | ".join("---" for _ in colunas) + " |"
    corpo = ["| " + " | ".join(texto(v) for v in linha) + " |" for linha in linhas]
    return "\n".join([cabecalho, separador, *corpo])


def _inteiro(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def _percentual(valor: float) -> str:
    return f"{valor:.2f}%".replace(".", ",")


def _renderizar_relatorio(
    diagnostico_prf: dict,
    resumo_inmet: dict,
    cobertura: pd.DataFrame,
    formato_prf,
    estacoes: list[LeituraEstacao],
    codigo_grupo: str,
) -> str:
    nulos = _tabela_markdown(
        ["Campo", "Nulos/NA no recorte"],
        [[campo, quantidade] for campo, quantidade in diagnostico_prf["nulos_relevantes"].items()],
    )
    esquema_prf = _tabela_markdown(
        ["Campo original", "Uso no diagnóstico", "Campo padronizado"],
        [
            ["id", "Identificador e duplicidade", "—"],
            [
                "data_inversa + horario",
                "Data e hora da ocorrência",
                "data_acidente; data_hora_acidente; data_hora_acidente_sp; "
                "data_hora_acidente_utc",
            ],
            ["uf + br", "Filtro SC/BR-101", "br_num"],
            ["municipio", "Localidade declarada", "—"],
            ["km", "Posição quilométrica", "km_num"],
            ["latitude + longitude", "Coordenadas da ocorrência", "latitude_num; longitude_num"],
            ["mortos + feridos", "Gravidade quantitativa", "mortos_num; feridos_num"],
            ["classificacao_acidente", "Classificação da ocorrência", "—"],
            ["condicao_metereologica", "Condição declarada pela PRF", "—"],
        ],
    )
    cobertura_linhas = []
    for codigo, linha in cobertura.iterrows():
        cobertura_linhas.append(
            [
                codigo,
                linha["nome_estacao"],
                linha["latitude"],
                linha["longitude"],
                linha["registros"],
                linha["horas_com_registro"],
                linha["timestamps_duplicados"],
                linha["medicoes_validas"],
                linha["horas_com_precipitacao_valida"],
                linha["precipitacao_zero"],
                linha["precipitacao_positiva"],
                linha["medicoes_ausentes"],
                linha["medicoes_invalidas"],
                _percentual(linha["cobertura_precipitacao_pct"]),
            ]
        )
    tabela_cobertura = _tabela_markdown(
        [
            "WMO",
            "Estação",
            "Latitude",
            "Longitude",
            "Linhas",
            "Horas únicas",
            "Duplicadas",
            "Medições válidas (linhas)",
            "Horas com medição válida",
            "Zero",
            "Positivas",
            "Ausentes",
            "Inválidas",
            "Cobertura",
        ],
        cobertura_linhas,
    )
    especiais = cobertura[
        cobertura["nome_estacao"].str.upper().str.contains("FLORIANOPOLIS|LAGUNA", regex=True)
    ]
    linhas_especiais = [
        (
            f"- **{linha['nome_estacao']} ({codigo})**: "
            f"{_inteiro(int(linha['horas_com_precipitacao_valida']))} horas com medição válida, "
            f"{_inteiro(int(linha['medicoes_ausentes']))} ausentes, "
            f"{_inteiro(int(linha['precipitacao_zero']))} iguais a zero; "
            f"cobertura de {_percentual(linha['cobertura_precipitacao_pct'])} das "
            f"{_inteiro(int(linha['horas_esperadas']))} horas esperadas."
        )
        for codigo, linha in especiais.iterrows()
    ]
    codificacoes_inmet = ", ".join(sorted({e.formato.codificacao for e in estacoes}))
    separadores_inmet = ", ".join(repr(v) for v in sorted({e.formato.separador for e in estacoes}))
    return f"""# Diagnóstico inicial das fontes — M2.1

Este documento registra a leitura e o diagnóstico calculado dos arquivos fornecidos para 2025. Ele não realiza associação espacial definitiva, EDA completa nem inferência de correlação.

## Fonte A — Polícia Rodoviária Federal (PRF)

- Arquivo analisado: `data/raw/datatran2025.zip` → `datatran2025.csv`.
- Instituição: Polícia Rodoviária Federal.
- Período declarado e observado no recorte: 2025; {diagnostico_prf['data_inicial']} a {diagnostico_prf['data_final']}.
- Unidade original: ocorrência de acidente.
- Separador detectado: `{formato_prf.separador}`.
- Codificação detectada: `{formato_prf.codificacao}`.
- Cabeçalho: primeira linha do CSV.
- Data: `AAAA-MM-DD`; horário: `HH:MM:SS`; decimais: vírgula.
- Fuso adotado para o horário PRF: `America/Sao_Paulo`; a coluna UTC é derivada sem substituir o valor original.
- Página oficial: https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf
- Condições informadas na página oficial: dados abertos, disponíveis para livre utilização, reutilização e redistribuição; nenhuma licença nominal específica foi identificada nesta verificação.
- Página oficial verificada em 2026-11-03; data de download dos ZIPs locais: 31/10/2026.

### Quantidade e qualidade

- Registros no arquivo nacional: **{_inteiro(diagnostico_prf['registros_total'])}**.
- Registros com `uf = SC`: **{_inteiro(diagnostico_prf['registros_sc'])}**.
- Registros com `uf = SC` e `br = 101`: **{_inteiro(diagnostico_prf['registros_sc_br101'])}**.
- Dias com acidentes no recorte: **{_inteiro(diagnostico_prf['dias_com_registros'])}**.
- IDs duplicados no recorte: **{_inteiro(diagnostico_prf['ids_duplicados'])}**.
- Datas inválidas: **{_inteiro(diagnostico_prf['datas_invalidas'])}**; combinações data/hora inválidas: **{_inteiro(diagnostico_prf['data_hora_invalida'])}**.

{nulos}

### Esquema relevante

{esquema_prf}

Os campos originais são preservados como texto. Sufixos `_num` e os campos temporais são derivados e não substituem o conteúdo de origem. A grafia `condicao_metereologica` é mantida porque é o nome fornecido pela PRF.

## Fonte B — Instituto Nacional de Meteorologia (INMET)

- Arquivo analisado: `data/raw/2025.zip`.
- Instituição: Instituto Nacional de Meteorologia.
- Recorte: membros CSV cujo nome contém `_SC_`.
- Período observado: {resumo_inmet['data_inicial']} a {resumo_inmet['data_final']}.
- Unidade original: observação meteorológica horária.
- Quantidade de arquivos/estações SC: **{_inteiro(resumo_inmet['quantidade_estacoes'])}**.
- Separador detectado: {separadores_inmet}; codificação detectada: {codificacoes_inmet}.
- Metadados lidos das oito linhas iniciais: código WMO, nome, latitude e longitude (além dos valores originais de região, UF, altitude e data de fundação quando presentes).
- Data: `AAAA/MM/DD`; hora: `HHMM UTC`; precipitação: milímetros com vírgula decimal.
- Página oficial: https://portal.inmet.gov.br/dadoshistoricos/
- Orientação oficial sobre acesso, horários e qualidade: https://portal.inmet.gov.br/noticias/saiba-como-acessar-os-dados-meteorol%C3%B3gicos-dispon%C3%ADveis-no-site-do-inmet
- Condições informadas pelo INMET: dados públicos e gratuitos; o usuário é responsável pelo uso e pela aplicação. Os dados de estações automáticas são brutos e não passam por validação de consistência antes da disponibilização.
- Página oficial verificada em 2026-11-03; data de download dos ZIPs locais: 31/10/2026.

### Quantidade, localização e cobertura

- Observações horárias (linhas): **{_inteiro(resumo_inmet['registros_total'])}**.
- Medições de precipitação válidas: **{_inteiro(resumo_inmet['medicoes_validas'])}**.
- Medições iguais a zero: **{_inteiro(resumo_inmet['precipitacao_zero'])}**.
- Medições positivas: **{_inteiro(resumo_inmet['precipitacao_positiva'])}**.
- Medições ausentes: **{_inteiro(resumo_inmet['medicoes_ausentes'])}**.
- Medições não vazias mas inválidas: **{_inteiro(resumo_inmet['medicoes_invalidas'])}**.
- Timestamps duplicados dentro da mesma estação: **{_inteiro(resumo_inmet['timestamps_duplicados'])}**.
- Extensão espacial das estações: latitude {resumo_inmet['latitude_min']} a {resumo_inmet['latitude_max']}; longitude {resumo_inmet['longitude_min']} a {resumo_inmet['longitude_max']}.

Uma linha horária com precipitação vazia, `Null` ou `9999` é **medição ausente**, não ausência de chuva. O valor numérico `0` é preservado como **medição válida sem precipitação**. A cobertura abaixo usa medições válidas divididas pelas 8.760 horas de 2025.

{tabela_cobertura}

### Florianópolis e Laguna

{chr(10).join(linhas_especiais) if linhas_especiais else '- Estações não encontradas no arquivo analisado.'}

## Amostras preparadas

- `data/samples/Grupo_{codigo_grupo}_Fonte_A.csv`: até 8 ocorrências reais do recorte SC/BR-101, com campos originais relevantes e derivados padronizados.
- `data/samples/Grupo_{codigo_grupo}_Fonte_B.csv`: até 8 observações reais, escolhidas deterministicamente por estação e estado da precipitação para representar zero, valor positivo e lacunas quando disponíveis.

## Limitações e pendências

- A data de download dos ZIPs foi informada pelo usuário como 31/10/2026. A data de 2026-11-03 documenta a verificação das páginas oficiais.
- O fuso de `horario` da PRF não está marcado no CSV. Por decisão metodológica do projeto, ele é tratado como `America/Sao_Paulo` e convertido também para UTC; essa suposição deve permanecer documentada na integração.
- Ausência de medição INMET não pode ser interpretada como precipitação zero. Lacunas extensas podem impedir o uso de uma estação em etapas posteriores.
- A causa operacional das lacunas de cada estação não está presente nos arquivos e não foi inferida.
- Coordenadas e km são declarações das fontes; este diagnóstico valida conversão e disponibilidade, não precisão geográfica.
- Os resultados descrevem a versão local dos ZIPs disponibilizados; a revisão exata publicada pelas instituições não está identificada nos nomes locais.
- Nenhuma associação espacial entre acidentes e estações foi feita nesta etapa e nenhuma conclusão sobre correlação foi produzida.

Relatório gerado de forma reproduzível em {date.today().isoformat()} a partir dos arquivos locais. Essa data é a data de processamento, não uma data de acesso às fontes.
"""


def gerar_artefatos(
    caminho_prf: str | Path,
    caminho_inmet: str | Path,
    pasta_amostras: str | Path,
    caminho_relatorio: str | Path,
    tamanho_amostra: int = 8,
    codigo_grupo: str = "R",
) -> ResultadoDiagnostico:
    """Lê as fontes, calcula indicadores e grava amostras e relatório."""

    caminho_prf = Path(caminho_prf)
    caminho_inmet = Path(caminho_inmet)
    pasta_amostras = Path(pasta_amostras)
    caminho_relatorio = Path(caminho_relatorio)
    pasta_amostras.mkdir(parents=True, exist_ok=True)
    caminho_relatorio.parent.mkdir(parents=True, exist_ok=True)

    dados_prf = ler_prf(caminho_prf)
    recorte_prf = filtrar_prf_sc_br101(dados_prf)
    diagnostico_prf = diagnosticar_prf(dados_prf)
    estacoes = ler_inmet_sc(caminho_inmet)
    resumo_inmet, cobertura = diagnosticar_inmet(estacoes, ano=2025)

    colunas_prf = [
        *CAMPOS_RELEVANTES,
        "data_hora_acidente",
        "data_hora_acidente_sp",
        "data_hora_acidente_utc",
        "br_num",
        "km_num",
        "latitude_num",
        "longitude_num",
        "mortos_num",
        "feridos_num",
    ]
    amostra_prf = recorte_prf.sort_values(["data_hora_acidente", "id"]).head(tamanho_amostra)
    caminho_amostra_prf = pasta_amostras / f"Grupo_{codigo_grupo}_Fonte_A.csv"
    amostra_prf.loc[:, colunas_prf].to_csv(caminho_amostra_prf, index=False, encoding="utf-8")

    amostra_inmet = _amostrar_inmet(estacoes, tamanho_amostra)
    caminho_amostra_inmet = pasta_amostras / f"Grupo_{codigo_grupo}_Fonte_B.csv"
    amostra_inmet.to_csv(caminho_amostra_inmet, index=False, encoding="utf-8")

    with ZipFile(caminho_prf) as arquivo:
        membro_prf = next(
            nome for nome in arquivo.namelist() if Path(nome).name.lower() == "datatran2025.csv"
        )
    formato_prf = detectar_formato_csv(caminho_prf, membro_prf)
    relatorio = _renderizar_relatorio(
        diagnostico_prf,
        resumo_inmet,
        cobertura,
        formato_prf,
        estacoes,
        codigo_grupo,
    )
    caminho_relatorio.write_text(relatorio, encoding="utf-8")
    return ResultadoDiagnostico(
        prf=diagnostico_prf,
        inmet=resumo_inmet,
        cobertura_inmet=cobertura,
        amostra_prf=caminho_amostra_prf,
        amostra_inmet=caminho_amostra_inmet,
        relatorio=caminho_relatorio,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera o diagnóstico M2.1 das fontes")
    parser.add_argument("--prf", type=Path, default=Path("data/raw/datatran2025.zip"))
    parser.add_argument("--inmet", type=Path, default=Path("data/raw/2025.zip"))
    parser.add_argument("--amostras", type=Path, default=Path("data/samples"))
    parser.add_argument("--relatorio", type=Path, default=Path("docs/diagnostico_fontes.md"))
    parser.add_argument("--grupo", default="R", help="Código usado nos nomes das amostras")
    args = parser.parse_args(argv)
    resultado = gerar_artefatos(
        args.prf,
        args.inmet,
        args.amostras,
        args.relatorio,
        codigo_grupo=args.grupo,
    )
    print(
        f"PRF SC/BR-101: {resultado.prf['registros_sc_br101']}; "
        f"estações INMET: {resultado.inmet['quantidade_estacoes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
