from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .bigquery_client import BigQuerySearchClient
from .config_bases import BASES, get_base_config, get_table_config
from .search_utils import parse_search_terms
from .unico_service import (
    UnicoConfigurationError,
    UnicoCredentialError,
    UnicoRateLimitError,
    UnicoRequestError,
    UnicoSearchService,
)


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

app = FastAPI(title="Busca de Candidatos API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
_bigquery_search: BigQuerySearchClient | None = None
unico_search = UnicoSearchService()
NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


@app.middleware("http")
async def disable_frontend_cache(request: Request, call_next):
    response = await call_next(request)
    if request.url.path in {"/", "/styles.css", "/icons.js", "/config.js", "/app.js"}:
        for header, value in NO_CACHE_HEADERS.items():
            response.headers[header] = value
    return response


def get_bigquery_search() -> BigQuerySearchClient:
    global _bigquery_search
    if _bigquery_search is None:
        _bigquery_search = BigQuerySearchClient()
    return _bigquery_search


class SearchRequest(BaseModel):
    tipo: str = Field(default="auto", pattern="^(auto|cpf|email|nome)$")
    entradas: list[str] = Field(default_factory=list, min_length=1)
    tabelas: list[str] = Field(default_factory=lambda: ["all"])
    modo_colunas: str = Field(default="resumo", pattern="^(resumo|todas)$")


class UnicoSearchRequest(BaseModel):
    tipo: str = Field(default="auto", pattern="^(auto|cpf|email|nome)$")
    entradas: list[str] = Field(default_factory=list, min_length=1, max_length=2000)
    credencial: str = ""
    dias: int = Field(default=5, ge=5, le=365)


def get_requested_tables(base_id: str, table_ids: list[str]) -> list[dict]:
    base = get_base_config(base_id)
    if not base:
        raise HTTPException(status_code=404, detail="Base nao encontrada.")

    if not table_ids or "all" in table_ids:
        return base["tabelas"]

    tables = []
    for table_id in table_ids:
        table = get_table_config(base_id, table_id)
        if not table:
            raise HTTPException(status_code=400, detail=f"Tabela invalida: {table_id}")
        tables.append(table)

    return tables


def get_output_columns(table: dict, mode: str) -> list[str]:
    if mode == "todas":
        return table["columns"]
    return table["summary_columns"]


def get_response_columns(tables: list[dict], mode: str) -> list[str]:
    columns = ["Consulta", "Tipo", "Resultado", "Tabela", "Linha"]
    seen = set(columns)

    for table in tables:
        for column in get_output_columns(table, mode):
            if column not in seen:
                seen.add(column)
                columns.append(column)

    return columns


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "unico_configurada": unico_search.configured,
    }


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html", headers=NO_CACHE_HEADERS)


@app.get("/styles.css")
def frontend_styles() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / "styles.css",
        media_type="text/css",
        headers=NO_CACHE_HEADERS,
    )


@app.get("/icons.js")
def frontend_icons() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / "icons.js",
        media_type="application/javascript",
        headers=NO_CACHE_HEADERS,
    )


@app.get("/app.js")
def frontend_script() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / "app.js",
        media_type="application/javascript",
        headers=NO_CACHE_HEADERS,
    )


@app.get("/config.js")
def frontend_config() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / "config.js",
        media_type="application/javascript",
        headers=NO_CACHE_HEADERS,
    )


@app.get("/unico/config")
def unico_config() -> dict:
    return {
        "configurada": unico_search.configured,
        "limite_execucao": 2000,
        "limite_por_segundo": 15,
        "periodo_minimo": 5,
        "periodo_maximo": 365,
        "incremento_periodo": 5,
    }


@app.post("/unico/search")
def search_unico(payload: UnicoSearchRequest) -> dict:
    terms = parse_search_terms(payload.entradas, payload.tipo)
    if not terms:
        raise HTTPException(status_code=400, detail="Nenhuma entrada válida para consulta.")

    try:
        results = unico_search.search(terms, payload.credencial, payload.dias)
    except UnicoCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except UnicoConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UnicoRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except UnicoRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    found = sum(1 for row in results if row["Resultado"] == "Encontrado")
    return {
        "total_consultado": len(terms),
        "total_encontrado": found,
        "total_ocorrencias": sum(int(row["Nº de ocorrências"]) for row in results),
        "colunas": [
            "Consulta",
            "Tipo",
            "Resultado",
            "Nome",
            "CPF",
            "Email",
            "Status",
            "Pendências",
            "Data limite",
            "Nº de ocorrências",
        ],
        "resultados": results,
    }


@app.get("/bases")
def list_bases() -> dict:
    return {
        "bases": [
            {
                "id": base["id"],
                "nome": base["nome"],
            }
            for base in BASES.values()
        ]
    }


@app.get("/bases/{base_id}")
def get_base(base_id: str) -> dict:
    base = get_base_config(base_id)
    if not base:
        raise HTTPException(status_code=404, detail="Base nao encontrada.")

    return {
        "base": base["id"],
        "nome": base["nome"],
        "tabelas": [
            {
                "id": table["id"],
                "nome": table["nome"],
                "colunas": [
                    {
                        "id": column,
                        "rotulo": column,
                        "tipo": "link" if column == table.get("link_column") else "texto",
                        "pesquisavel": column in [
                            table.get("cpf_column"),
                            table.get("name_column"),
                            table.get("email_column"),
                        ],
                        "copiavel": True,
                    }
                    for column in table["columns"]
                ],
                "colunas_resumo": table["summary_columns"],
            }
            for table in base["tabelas"]
        ],
    }


@app.post("/search/{base_id}")
def search_base(base_id: str, payload: SearchRequest) -> dict:
    tables = get_requested_tables(base_id, payload.tabelas)
    terms = parse_search_terms(payload.entradas, payload.tipo)

    if not terms:
        raise HTTPException(status_code=400, detail="Nenhuma entrada valida para consulta.")

    response_columns = get_response_columns(tables, payload.modo_colunas)
    found_by_key: set[tuple[str, str]] = set()
    results: list[dict] = []

    for table in tables:
        output_columns = get_output_columns(table, payload.modo_colunas)
        table_results = get_bigquery_search().search_table(table, terms, output_columns)

        for row in table_results:
            search_type = row["Tipo"].lower()
            if search_type == "nome":
                search_type = "nome"
            found_by_key.add((search_type, row["Consulta"]))
            results.append({column: row.get(column, "") for column in response_columns})

    for term in terms:
        if (term.type, term.raw) in found_by_key:
            continue

        missing_row = {column: "" for column in response_columns}
        missing_row.update(
            {
                "Consulta": term.raw,
                "Tipo": term.type.upper() if term.type != "nome" else "NOME",
                "Resultado": "Nao encontrado",
            }
        )
        results.append(missing_row)

    total_found = len({(row["Consulta"], row["Tipo"]) for row in results if row.get("Resultado") == "Encontrado"})

    return {
        "base": base_id,
        "total_consultado": len(terms),
        "total_encontrado": total_found,
        "colunas": response_columns,
        "resultados": results,
    }


app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")
