import re

import pandas as pd
import pygsheets


# URLs das planilhas de mapeamento e de destino.
URL_MAPEAMENTO = ""
URL_DESTINO = ""

SCOPES_GOOGLE_SHEETS = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# Colunas fixas do mapeamento (A até E).
# Não há colunas de owner nem descrição.
IDX_STATUS = 0  # A: Base ativa?
IDX_LINK_BASE = 1  # B: Link da base
IDX_NOME_PLANILHA = 2  # C: Nome do excel
IDX_NOME_ABA = 3  # D: Nome da aba
IDX_REGIONAL = 4  # E: REGIONAL
IDX_LINHA_INICIAL = 5  # F: A partir de

INDICES_CONTROLE = [
    IDX_NOME_PLANILHA,
    IDX_LINK_BASE,
    IDX_STATUS,
    IDX_NOME_ABA,
    IDX_REGIONAL,
    IDX_LINHA_INICIAL,
]


def conectar_google_sheets():
    credentials = connections["GCP-GSheets-API-ServiceAccount"].credentials
    return pygsheets.authorize(
        custom_credentials=credentials.with_scopes(SCOPES_GOOGLE_SHEETS)
    )


def extract_id_and_gid_from_url(url: str):
    """Extrai o ID e, quando presente, o GID da URL da planilha."""
    url = str(url).strip()
    id_match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    gid_match = re.search(r"gid=([0-9]+)", url)
    if not id_match:
        raise ValueError(f"URL de planilha inválida: {url}")
    return id_match.group(1), int(gid_match.group(1)) if gid_match else None


def get_worksheet_by_gid(spreadsheet, gid: int):
    if gid is None:
        return None
    return next(
        (worksheet for worksheet in spreadsheet.worksheets() if int(worksheet.id) == gid),
        None,
    )


def excel_col_to_index(col_letter):
    if pd.isna(col_letter):
        return None
    col_letter = str(col_letter).strip().upper()
    if not col_letter or not col_letter.isalpha():
        return None
    result = 0
    for char in col_letter:
        result = result * 26 + ord(char) - ord("A") + 1
    return result - 1


def valor_texto(valor):
    return "" if pd.isna(valor) else str(valor).strip()


def linha_inicial_valida(valor):
    """Converte o número de linha do Sheets em índice zero-based do pandas."""
    try:
        numero_linha = int(float(valor))
    except (TypeError, ValueError):
        return None
    return numero_linha - 1 if numero_linha >= 1 else None


def formatar_colunas_data(df):
    for coluna in ["Data do processo", "Data de nascimento"]:
        if coluna in df.columns:
            datas = pd.to_datetime(df[coluna], errors="coerce", dayfirst=True)
            df[coluna] = datas.dt.strftime("%d/%m/%Y")
    return df


def abrir_planilha_por_id(gc, spreadsheet_id, nome_planilha):
    try:
        return gc.open_by_key(spreadsheet_id)
    except Exception as erro:
        raise RuntimeError(
            f"Não foi possível abrir a planilha '{nome_planilha}'. "
            "Verifique o compartilhamento com a conta de serviço."
        ) from erro


def get_worksheet(spreadsheet, gid, nome_aba):
    """Usa o GID da URL quando houver; sem ele, usa o nome mapeado na coluna D."""
    worksheet = get_worksheet_by_gid(spreadsheet, gid)
    if worksheet is not None:
        return worksheet
    if nome_aba:
        try:
            return spreadsheet.worksheet_by_title(nome_aba)
        except pygsheets.WorksheetNotFound:
            pass
    return None


def main():
    gc = conectar_google_sheets()
    map_id, map_gid = extract_id_and_gid_from_url(URL_MAPEAMENTO)
    ws_map = get_worksheet_by_gid(abrir_planilha_por_id(gc, map_id, "Mapeamento"), map_gid)
    if ws_map is None:
        raise ValueError(f"Aba de mapeamento com GID {map_gid} não encontrada.")

    df_map = ws_map.get_as_df()
    colunas_alvo = [
        coluna
        for indice, coluna in enumerate(df_map.columns)
        if indice not in INDICES_CONTROLE
        and str(coluna).strip()
        and not str(coluna).strip().startswith("Unnamed")
    ]

    lista_df_consolidados = []
    for index, row in df_map.iterrows():
        numero_linha_mapeamento = index + 2
        nome_planilha = valor_texto(row.iloc[IDX_NOME_PLANILHA])
        link_base = valor_texto(row.iloc[IDX_LINK_BASE])
        status_ativo = valor_texto(row.iloc[IDX_STATUS]).upper()
        nome_aba_mapeamento = valor_texto(row.iloc[IDX_NOME_ABA])
        regional = valor_texto(row.iloc[IDX_REGIONAL])
        inicio = linha_inicial_valida(row.iloc[IDX_LINHA_INICIAL])

        if status_ativo != "TRUE":
            print(f"Base ignorada na linha {numero_linha_mapeamento}: status '{status_ativo}'.")
            continue
        if not link_base.startswith("http"):
            print(f"Base ignorada na linha {numero_linha_mapeamento}: link inválido.")
            continue
        if inicio is None:
            print(
                f"Base ignorada na linha {numero_linha_mapeamento}: "
                "a coluna F deve conter um número de linha maior que zero."
            )
            continue

        src_id, src_gid = extract_id_and_gid_from_url(link_base)
        sh_src = abrir_planilha_por_id(gc, src_id, nome_planilha)
        ws_src = get_worksheet(sh_src, src_gid, nome_aba_mapeamento)
        if ws_src is None:
            raise ValueError(
                f"Aba não encontrada na planilha '{nome_planilha}'. "
                f"GID na URL: {src_gid}; aba mapeada: '{nome_aba_mapeamento}'."
            )

        df_origem = pd.DataFrame(ws_src.get_all_values())
        if inicio >= len(df_origem):
            print(
                f"Base '{nome_planilha}' ignorada: a linha inicial {inicio + 1} "
                "está além dos dados disponíveis."
            )
            continue

        # A linha indicada na coluna F é a primeira linha incluída no resultado.
        df_temp = pd.DataFrame(index=range(len(df_origem) - inicio))
        df_temp["Link da base"] = link_base
        df_temp["Nome do excel"] = nome_planilha
        df_temp["Nome da aba"] = nome_aba_mapeamento
        df_temp["REGIONAL"] = regional

        for alvo in colunas_alvo:
            indice_coluna = excel_col_to_index(row[alvo])
            if indice_coluna is not None and indice_coluna < df_origem.shape[1]:
                df_temp[alvo] = df_origem.iloc[inicio:, indice_coluna].reset_index(drop=True)
            else:
                df_temp[alvo] = None

        if colunas_alvo:
            df_temp[colunas_alvo] = df_temp[colunas_alvo].replace(r"^\s*$", pd.NA, regex=True)
            df_temp = df_temp.dropna(how="all", subset=colunas_alvo)

        print(f"Base concluída: '{nome_planilha}' | Linhas extraídas: {len(df_temp)}")
        lista_df_consolidados.append(df_temp)

    if not lista_df_consolidados:
        print("Nenhuma linha foi extraída.")
        return

    dest_id, dest_gid = extract_id_and_gid_from_url(URL_DESTINO)
    ws_dest = get_worksheet_by_gid(
        abrir_planilha_por_id(gc, dest_id, "Destino"), dest_gid
    )
    if ws_dest is None:
        raise ValueError(f"Aba de destino com GID {dest_gid} não encontrada.")

    df_final = pd.concat(lista_df_consolidados, ignore_index=True)
    df_final = formatar_colunas_data(df_final)
    # O Google Sheets deve receber células vazias, e não valores NaN do pandas.
    df_final = df_final.fillna("")
    ws_dest.clear()
    ws_dest.set_dataframe(df_final, start="A1", copy_head=True, extend=True)
    print(f"Processo concluído com sucesso: {len(df_final)} linhas consolidadas.")


if __name__ == "__main__":
    main()
