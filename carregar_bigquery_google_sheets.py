import re
from datetime import date, datetime
from decimal import Decimal

import pygsheets


SCOPES_GOOGLE_SHEETS = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def conectar_google_sheets():
    credentials = connections["GCP-GSheets-API-ServiceAccount"].credentials
    return pygsheets.authorize(
        custom_credentials=credentials.with_scopes(SCOPES_GOOGLE_SHEETS)
    )


BIGQUERY_CONNECTION = "GCP_MELI_PEOPLE_SHIPPING"
client_bq = connections[BIGQUERY_CONNECTION].bigquery_client

PROJECT_ID = client_bq.project
DATASET_ID = "SILVER_PE_SHIPPING"
TABLE_ID = "EL_GOVERNANCA_CONSOLIDATED_BR_MASTER"
TABELA_ORIGEM = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Use somente a URL completa da aba de destino, incluindo o gid.
URL_PLANILHA_DESTINO = (
    "https://docs.google.com/spreadsheets/d/"
    "1otTVPQwcuFqK_ABxVx339ExFUIasrOkr5U4WNdkTWoY/edit?gid=832479326#gid=832479326"
)


def obter_gid_da_url(url):
    """Extrai o gid da aba diretamente da URL do Google Sheets."""
    resultado = re.search(r"[?#&]gid=(\d+)", url)
    if not resultado:
        raise ValueError(
            "A URL da planilha deve conter o gid da aba. "
            "Abra a aba desejada e copie a URL completa."
        )
    return int(resultado.group(1))


def obter_aba_por_gid(planilha, gid):
    for aba in planilha.worksheets():
        if int(aba.id) == gid:
            return aba
    raise ValueError(f"Nenhuma aba encontrada com gid={gid}.")


def extrair_tabela_bigquery():
    query = "SELECT * FROM " + chr(96) + TABELA_ORIGEM + chr(96)
    return client_bq.query(query).result()


def valor_compativel_com_sheets(valor):
    """Converte apenas tipos que a API do Google Sheets não aceita em JSON."""
    if valor is None:
        return ""
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return valor


def letra_da_coluna(indice):
    """Converte 1 em A, 27 em AA, e assim por diante."""
    resultado = ""
    while indice:
        indice, resto = divmod(indice - 1, 26)
        resultado = chr(65 + resto) + resultado
    return resultado


def carregar_resultado_na_aba(aba, resultado):
    """Copia o resultado SQL para a aba, sem criar DataFrame ou tratar colunas."""
    cabecalhos = [campo.name for campo in resultado.schema]
    linhas = [
        [valor_compativel_com_sheets(valor) for valor in linha.values()]
        for linha in resultado
    ]

    if not linhas:
        raise ValueError("A consulta não retornou dados. Nenhum dado será carregado.")

    aba.clear()
    aba.resize(rows=len(linhas) + 1, cols=len(cabecalhos))
    aba.update_values("A1", [cabecalhos])

    # Evita uma requisição grande demais para a API, sem alterar os dados.
    tamanho_lote = 1_000
    for inicio in range(0, len(linhas), tamanho_lote):
        lote = linhas[inicio : inicio + tamanho_lote]
        primeira_linha = inicio + 2  # Linha 1 é o cabeçalho.
        aba.update_values(f"A{primeira_linha}", lote)

    return len(linhas), len(cabecalhos)


def carregar_google_sheets(resultado):
    gc = conectar_google_sheets()
    planilha = gc.open_by_url(URL_PLANILHA_DESTINO)
    aba = obter_aba_por_gid(planilha, obter_gid_da_url(URL_PLANILHA_DESTINO))

    linhas, colunas = carregar_resultado_na_aba(aba, resultado)

    print(
        f"Carga concluída: {linhas} linhas e {colunas} colunas "
        f"na aba '{aba.title}'."
    )


def main():
    print(f"Extraindo a tabela {TABELA_ORIGEM}...")
    carregar_google_sheets(extrair_tabela_bigquery())


if __name__ == "__main__":
    main()
