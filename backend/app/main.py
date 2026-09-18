from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel, Field

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

class UnicoSearchRequest(BaseModel):
    tipo: str = Field(default="cpf", pattern="^cpf$")
    entradas: list[str] = Field(default_factory=list, min_length=1, max_length=2000)
    credencial: str = ""
    dias: int = Field(default=5, ge=5, le=365)

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "unico_configurada": unico_search.configured,
    }


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html", headers=NO_CACHE_HEADERS)


@app.get("/{frontend_route:unico|documentacao}")
def frontend_route(frontend_route: str) -> FileResponse:
    """Permite abrir uma rota da interface diretamente no navegador."""
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
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")
