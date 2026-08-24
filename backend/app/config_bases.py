import os


PROCESSOS_SELETIVOS_SP_COLUMNS = [
    "Nome da planilha",
    "Link da aba",
    "WEEK",
    "DATA",
    "REGIONAL RESPONSÁVEL",
    "LOCAL DO PROCESSO",
    "FONTE DE AGENDAMENTO",
    "FONTE DE CONVOCAÇÃO",
    "DETALHE DA FONTE DE CONVOCAÇÃO",
    "STATUS",
    "PRESENÇA",
    "OBSERVAÇÕES",
    "NOME COMPLETO",
    "CPF",
    "E-mail",
    "Telefone",
    "Data de Nascimento",
    "Endereço Completo",
    "Rua (COM NÚMERO)",
    "Bairro",
    "Cidade",
    "CEP",
    "Horário Descritivo",
    "TURNO FINAL",
    "2º opção de turno (Deu Match!)",
    "ESCOLARIDADE",
    "Horário do agendamento",
    "TA/APRENDIZ",
    "TL em entrevista",
    "STATUS ENTREVISTA TA + TL",
    "Entrevista",
    "Etapa desistência",
]


PROCESSOS_SELETIVOS_SP_SUMMARY_COLUMNS = [
    "Nome da planilha",
    "Link da aba",
    "WEEK",
    "DATA",
    "REGIONAL RESPONSÁVEL",
    "LOCAL DO PROCESSO",
    "STATUS",
    "PRESENÇA",
    "NOME COMPLETO",
    "CPF",
    "E-mail",
    "Telefone",
    "TURNO FINAL",
    "STATUS ENTREVISTA TA + TL",
    "Etapa desistência",
]


BASES = {
    "processos-seletivos-sp": {
        "id": "processos-seletivos-sp",
        "nome": "Processos Seletivos SP",
        "tabelas": [
            {
                "id": "processos_seletivos_sp",
                "nome": "Processos Seletivos SP",
                "bigquery_table": os.getenv(
                    "BQ_PROCESSOS_SELETIVOS_SP_TABLE",
                    "seu-projeto.seu_dataset.processos_seletivos_sp",
                ),
                "columns": PROCESSOS_SELETIVOS_SP_COLUMNS,
                "summary_columns": PROCESSOS_SELETIVOS_SP_SUMMARY_COLUMNS,
                "cpf_column": "CPF",
                "name_column": "NOME COMPLETO",
                "email_column": "E-mail",
                "link_column": "Link da aba",
                "sheet_name_column": "Nome da planilha",
            }
        ],
    }
}


def get_base_config(base_id: str) -> dict | None:
    return BASES.get(base_id)


def get_table_config(base_id: str, table_id: str) -> dict | None:
    base = get_base_config(base_id)
    if not base:
        return None

    for table in base["tabelas"]:
        if table["id"] == table_id:
            return table

    return None
