import os
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .search_utils import SearchTerm


UNICO_URL = "https://admin.acessorh.com.br/svc2/search/people"
REQUESTS_PER_SECOND = 15
REQUEST_DELAY = 1 / REQUESTS_PER_SECOND

STATUS_PRIORITY = {
    "Arquivado": 1,
    "Mesa de análise": 2,
    "Pendente": 3,
    "Não iniciado": 4,
    "Sem acesso recente": 5,
}

TRACKED_DOCUMENTS = {
    "rg": "RG",
    "cpf": "CPF",
    "escolaridade": "Comprovante de escolaridade",
    "declaracao-de-escolaridade": "Autodeclaração de escolaridade",
    "endereco": "Comprovante de endereço",
    "declaracao-de-endereco": "Autodeclaração de endereço",
    "cracha": "Foto do crachá",
    "nascimento": "Certidão de nascimento",
    "casamento": "Certidão de casamento",
    "dependentes": "Dependentes",
    "divorcio": "Certidão de divórcio",
    "beneficios": "Benefícios",
    "pis": "PIS",
    "exame": "Exame admissional",
    "info-pessoal": "Informações pessoais",
}


class UnicoConfigurationError(RuntimeError):
    pass


class UnicoCredentialError(RuntimeError):
    pass


class UnicoRateLimitError(RuntimeError):
    pass


class UnicoRequestError(RuntimeError):
    pass


def _normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(text.lower().split())


def _parse_date(value: Any) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _format_date(value: Any) -> str:
    parsed = _parse_date(value)
    if not parsed or parsed.year <= 1900:
        return ""
    return parsed.strftime("%d/%m/%Y")


def _reference_date(admission: dict) -> datetime | None:
    limit_date = _parse_date(admission.get("limitDate"))
    if limit_date and limit_date.year > 1900:
        return limit_date
    return None


def _is_recent(admission: dict, days: int) -> bool:
    reference = _reference_date(admission)
    if reference is None:
        return True
    return reference >= datetime.now(timezone.utc) - timedelta(days=days)


def _status(admission: dict) -> str:
    status_data = admission.get("status", {})
    if isinstance(status_data, dict):
        overview = status_data.get("overview", {})
    else:
        overview = {}

    if not isinstance(overview, dict):
        overview = {}

    # The current UNICO response uses status.overview.code. The other fields
    # remain as compatibility fallbacks for older response formats.
    flat_overview = admission.get("status_overview")
    camel_overview = admission.get("statusOverview")
    code_values = (
        overview.get("code"),
        overview.get("status"),
        overview.get("status_overview"),
        overview.get("statusOverview"),
        flat_overview.get("code") if isinstance(flat_overview, dict) else flat_overview,
        camel_overview.get("code") if isinstance(camel_overview, dict) else camel_overview,
        status_data.get("code") if isinstance(status_data, dict) else status_data,
        status_data.get("status") if isinstance(status_data, dict) else None,
        admission.get("statusCode"),
        admission.get("status_code"),
    )
    normalized_codes = [
        str(value).lower().strip()
        for value in code_values
        if value is not None and str(value).strip()
    ]
    code = next(
        (value for value in normalized_codes if value in {"archived", "completed", "pending"}),
        normalized_codes[0] if normalized_codes else "",
    )

    if code == "archived":
        return "Arquivado"
    if code == "completed":
        return "Mesa de análise"
    if code == "pending":
        return "Pendente"
    return "Não iniciado"


def _best_admission(admissions: list[dict]) -> tuple[dict | None, str]:
    if not admissions:
        return None, "Não iniciado"

    ranked = sorted(
        ((_status(admission), admission) for admission in admissions),
        key=lambda item: STATUS_PRIORITY.get(item[0], 999),
    )
    status, admission = ranked[0]
    return admission, status


def _document_name(document: dict) -> str:
    slug = _normalize_text(document.get("slug")).replace(" ", "-")
    if slug in TRACKED_DOCUMENTS:
        return TRACKED_DOCUMENTS[slug]

    title = document.get("title", {})
    if isinstance(title, dict):
        title = title.get("pt_BR") or title.get("pt-br") or title.get("pt") or ""

    normalized_title = _normalize_text(title)
    for tracked_name in TRACKED_DOCUMENTS.values():
        if _normalize_text(tracked_name) == normalized_title:
            return tracked_name
    return ""


def _pending_documents(admission: dict) -> str:
    pending: list[str] = []

    for document in admission.get("documentList", []):
        name = _document_name(document)
        if not name:
            continue

        try:
            code = int(document.get("code"))
        except (TypeError, ValueError):
            code = None

        if code not in {200, 220}:
            pending.append(name)

    return "; ".join(dict.fromkeys(pending))


def _is_not_started(admission: dict) -> bool:
    """A pending candidate is not started only before any document was delivered."""
    for document in admission.get("documentList", []) or []:
        try:
            if int(document.get("code")) in {200, 220}:
                return False
        except (TypeError, ValueError):
            continue
    return True


def _pendencies(status: str, admission: dict) -> str:
    if status == "Arquivado":
        return ""
    if status == "Mesa de análise":
        return ""
    if status == "Não iniciado":
        return "Todos os documentos"
    if status == "Pendente":
        return _pending_documents(admission) or "Pendências"
    return ""


def _authorization_value(credential: str) -> str:
    credential = credential.strip()
    if not credential:
        return ""
    if " " in credential:
        return credential
    return f"Bearer {credential}"


class UnicoSearchService:
    def __init__(self) -> None:
        self.account_id = os.getenv("UNICO_ACCOUNT_ID", "").strip()
        self.tenant = os.getenv("UNICO_TENANT", "").strip()
        self.cookie = os.getenv("UNICO_COOKIE", "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.account_id and self.tenant)

    def _headers(self, credential: str) -> dict[str, str]:
        if not self.configured:
            raise UnicoConfigurationError(
                "A integração UNICO ainda não possui UNICO_ACCOUNT_ID e UNICO_TENANT."
            )

        headers = {
            "authorization": _authorization_value(credential),
            "tenant": self.tenant,
            "user-agent": "Busca-Candidatos/1.0",
            "accept": "application/json",
        }
        if self.cookie:
            headers["cookie"] = self.cookie
        return headers

    def _request(self, session: requests.Session, term: SearchTerm, credential: str) -> tuple[list[dict], int]:
        try:
            response = session.get(
                UNICO_URL,
                params={
                    "account": self.account_id,
                    "q": term.key if term.type in {"cpf", "email"} else term.raw,
                },
                headers=self._headers(credential),
                timeout=25,
            )
        except requests.Timeout as exc:
            raise UnicoRequestError(
                "A UNICO demorou mais que o esperado para responder. Tente novamente."
            ) from exc
        except requests.RequestException as exc:
            raise UnicoRequestError(
                "Não foi possível conectar à UNICO. Verifique a rede e tente novamente."
            ) from exc

        if response.status_code in {401, 403}:
            raise UnicoCredentialError("Credencial não encontrada, tente novamente.")
        if response.status_code == 429:
            raise UnicoRateLimitError(
                "A UNICO atingiu o limite de requisições. Aguarde alguns segundos e tente novamente."
            )
        if response.status_code in {500, 502, 503, 504}:
            raise UnicoRequestError(
                "A UNICO apresentou uma instabilidade temporária "
                f"(HTTP {response.status_code}) mesmo após novas tentativas. Tente novamente em alguns instantes."
            )
        if response.status_code != 200:
            raise UnicoRequestError(f"A UNICO respondeu com o código HTTP {response.status_code}.")

        try:
            payload = response.json()
        except ValueError as exc:
            raise UnicoRequestError("A UNICO retornou uma resposta inválida.") from exc

        admissions = payload.get("result", {}).get("admissions", {})
        return admissions.get("results", []) or [], int(admissions.get("total", 0) or 0)

    def search(
        self,
        terms: list[SearchTerm],
        credential: str,
        days: int,
    ) -> list[dict[str, Any]]:
        if not credential.strip():
            raise UnicoCredentialError(
                "Para a requisição de busca, adicione a credencial. "
                "Caso tenha dúvida de como proceder, entre na página de Documentação."
            )

        rows: list[dict[str, Any]] = []
        session = requests.Session()
        # Avoid unrelated proxy settings injected into the internal runtime.
        session.trust_env = False
        session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=3,
                    connect=3,
                    read=1,
                    status=3,
                    status_forcelist=(500, 502, 503, 504),
                    backoff_factor=1,
                    allowed_methods=frozenset({"GET"}),
                    raise_on_status=False,
                    respect_retry_after_header=True,
                )
            ),
        )

        for index, term in enumerate(terms):
            admissions, total = self._request(session, term, credential)
            recent = [admission for admission in admissions if _is_recent(admission, days)]

            if not admissions:
                rows.append(
                    {
                        "Consulta": term.raw,
                        "Tipo": term.type.upper(),
                        "Resultado": "Não encontrado",
                        "Nome": "",
                        "CPF": term.key if term.type == "cpf" else "",
                        "Email": term.key if term.type == "email" else "",
                        "Status": "",
                        "Pendências": "",
                        "Data limite": "",
                        "Nº de ocorrências": 0,
                    }
                )
            else:
                selected_pool = recent or admissions
                admission, status = _best_admission(selected_pool)
                if not recent:
                    status = "Sem acesso recente"
                elif status == "Pendente" and _is_not_started(admission or {}):
                    status = "Não iniciado"

                candidate = (admission or {}).get("candidate", {})
                identifier = candidate.get("identifier", {})
                cpf = identifier.get("value", "") if isinstance(identifier, dict) else ""

                rows.append(
                    {
                        "Consulta": term.raw,
                        "Tipo": term.type.upper(),
                        "Resultado": "Encontrado",
                        "Nome": candidate.get("name", "") or "",
                        "CPF": cpf or (term.key if term.type == "cpf" else ""),
                        "Email": candidate.get("email", "") or "",
                        "Status": status,
                        "Pendências": _pendencies(status, admission or {}),
                        "Data limite": _format_date((admission or {}).get("limitDate")),
                        "Nº de ocorrências": total,
                    }
                )

            if index < len(terms) - 1:
                time.sleep(REQUEST_DELAY)

        return rows
