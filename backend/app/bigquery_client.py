from google.cloud import bigquery

from .search_utils import SearchTerm, clean_cell_value


def quote_identifier(identifier: str) -> str:
    return f"`{identifier.replace('`', '')}`"


def quote_table(table_name: str) -> str:
    parts = [part.replace("`", "") for part in table_name.split(".")]
    return ".".join(f"`{part}`" for part in parts)


def build_select_columns(columns: list[str]) -> str:
    return ",\n  ".join(f"{quote_identifier(column)} AS {quote_identifier(column)}" for column in columns)


class BigQuerySearchClient:
    def __init__(self) -> None:
        self.client = bigquery.Client()

    def search_table(
        self,
        table_config: dict,
        terms: list[SearchTerm],
        output_columns: list[str],
    ) -> list[dict]:
        results: list[dict] = []

        terms_by_type = {
            "cpf": [term for term in terms if term.type == "cpf"],
            "email": [term for term in terms if term.type == "email"],
            "nome": [term for term in terms if term.type == "nome"],
        }

        for search_type, typed_terms in terms_by_type.items():
            if not typed_terms:
                continue
            results.extend(self._search_table_by_type(table_config, typed_terms, search_type, output_columns))

        return results

    def _search_table_by_type(
        self,
        table_config: dict,
        terms: list[SearchTerm],
        search_type: str,
        output_columns: list[str],
    ) -> list[dict]:
        table_name = quote_table(table_config["bigquery_table"])
        selected_columns = build_select_columns(output_columns)
        raw_values = [term.raw for term in terms]
        key_values = [term.key for term in terms]

        if search_type == "cpf":
            search_column = table_config["cpf_column"]
            predicate = (
                f"REGEXP_REPLACE(CAST(t.{quote_identifier(search_column)} AS STRING), r'[^0-9]', '') = entrada.key"
            )
        elif search_type == "email":
            search_column = table_config["email_column"]
            predicate = f"LOWER(TRIM(CAST(t.{quote_identifier(search_column)} AS STRING))) = entrada.key"
        else:
            search_column = table_config["name_column"]
            predicate = (
                "REGEXP_CONTAINS("
                f"REGEXP_REPLACE(NORMALIZE_AND_CASEFOLD(CAST(t.{quote_identifier(search_column)} AS STRING), NFD), r'\\pM', ''), "
                "REGEXP_REPLACE(REGEXP_REPLACE(NORMALIZE_AND_CASEFOLD(entrada.key, NFD), r'\\pM', ''), r'\\s+', r'.*')"
                ")"
            )

        sql = f"""
        WITH entradas AS (
          SELECT
            raw,
            key
          FROM UNNEST(@raw_values) AS raw WITH OFFSET raw_pos
          JOIN UNNEST(@key_values) AS key WITH OFFSET key_pos
          ON raw_pos = key_pos
        )
        SELECT
          entrada.raw AS __consulta,
          entrada.key AS __key,
          @search_type AS __tipo,
          ROW_NUMBER() OVER() AS __linha,
          {selected_columns}
        FROM entradas AS entrada
        JOIN {table_name} AS t
        ON {predicate}
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("raw_values", "STRING", raw_values),
                bigquery.ArrayQueryParameter("key_values", "STRING", key_values),
                bigquery.ScalarQueryParameter("search_type", "STRING", search_type),
            ]
        )

        rows = self.client.query(sql, job_config=job_config).result()
        output: list[dict] = []

        for row in rows:
            item = dict(row.items())
            result = {
                "Consulta": clean_cell_value(item.pop("__consulta", "")),
                "Tipo": search_type.upper() if search_type != "nome" else "NOME",
                "Resultado": "Encontrado",
                "Tabela": table_config["nome"],
                "Linha": clean_cell_value(item.pop("__linha", "")),
            }

            item.pop("__key", None)
            item.pop("__tipo", None)

            for column in output_columns:
                result[column] = clean_cell_value(item.get(column, ""))

            output.append(result)

        return output
