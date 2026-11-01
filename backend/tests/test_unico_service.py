from datetime import datetime, timedelta, timezone

import requests
import pytest

from app.search_utils import SearchTerm
from app.unico_service import (
    UnicoCredentialError,
    UnicoRequestError,
    UnicoSearchService,
    _is_recent,
    _is_not_started,
    _pendencies,
    _pending_documents,
    _status,
)


class FailingSession:
    def get(self, *args, **kwargs):
        raise requests.ConnectionError("falha de teste")


def configured_service(monkeypatch):
    monkeypatch.setenv("UNICO_ACCOUNT_ID", "account-test")
    monkeypatch.setenv("UNICO_TENANT", "tenant-test")
    return UnicoSearchService()


def test_requires_credential(monkeypatch):
    service = configured_service(monkeypatch)

    with pytest.raises(UnicoCredentialError):
        service.search(
            [SearchTerm(raw="12345678900", type="cpf", key="12345678900")],
            credential="",
            days=30,
        )


def test_network_error_becomes_readable_message(monkeypatch):
    service = configured_service(monkeypatch)
    term = SearchTerm(raw="12345678900", type="cpf", key="12345678900")

    with pytest.raises(UnicoRequestError, match="Não foi possível conectar"):
        service._request(FailingSession(), term, "token")


def test_search_ignores_environment_proxy(monkeypatch):
    service = configured_service(monkeypatch)
    session = requests.Session()
    monkeypatch.setattr("app.unico_service.requests.Session", lambda: session)
    monkeypatch.setattr(service, "_request", lambda active_session, term, credential: ([], 0))

    service.search(
        [SearchTerm(raw="12345678900", type="cpf", key="12345678900")],
        credential="token",
        days=30,
    )

    assert session.trust_env is False


@pytest.mark.parametrize(
    "admission",
    [
        {"status": {"overview": {"code": "archived", "total": 0}}},
        {"status": {"overview": {"status_overview": "archived", "code": 1}}},
        {"status_overview": "archived"},
        {"status": {"code": "archived", "total": 0}},
        {"status": "archived"},
    ],
)
def test_archived_status_is_not_reported_as_not_started(admission):
    assert _status(admission) == "Arquivado"


def test_pending_status_does_not_depend_on_progress_code():
    assert _status({"status_overview": "pending", "code": 1}) == "Pendente"


def test_current_unico_status_path_keeps_pending_when_documents_exist():
    admission = {
        "status": {"overview": {"code": "pending", "total": 1}},
        "documentList": [{"code": 220}, {"code": 200}],
    }

    assert _status(admission) == "Pendente"
    assert not _is_not_started(admission)


def test_not_started_requires_no_completed_document():
    assert _is_not_started({"documentList": [{"code": 400}, {"code": 404}]})
    assert not _is_not_started({"documentList": [{"code": 220}, {"code": 404}]})
    assert not _is_not_started({"documentList": [{"code": 220}, {"code": 200}]})


def test_documents_under_analysis_are_not_pending():
    admission = {
        "documentList": [
            {"code": 200, "exist": True, "slug": "rg"},
            {"code": 220, "exist": False, "slug": "cpf"},
            {"code": 404, "exist": False, "slug": "pis"},
        ]
    }

    assert _pending_documents(admission) == "PIS"


def test_analysis_table_has_no_pending_output():
    assert _pendencies("Mesa de análise", {}) == ""


def test_schooling_self_declaration_is_a_tracked_pending_document():
    admission = {
        "documentList": [
            {
                "slug": "declaracao-de-escolaridade",
                "title": {"pt_BR": "Autodeclaração de Escolaridade"},
                "code": 400,
                "exist": True,
            }
        ]
    }

    assert _pending_documents(admission) == "Autodeclaração de escolaridade"


def test_address_self_declaration_is_a_tracked_pending_document():
    admission = {
        "documentList": [
            {
                "slug": "declaracao-de-endereco",
                "title": {"pt_BR": "Autodeclaração de Endereço"},
                "code": 100,
                "exist": False,
            }
        ]
    }

    assert _pending_documents(admission) == "Autodeclaração de endereço"


def test_recent_period_uses_limit_date_instead_of_document_activity():
    old_activity = datetime.now(timezone.utc) - timedelta(days=30)
    future_limit = datetime.now(timezone.utc) + timedelta(days=10)
    admission = {
        "limitDate": future_limit.isoformat(),
        "documentList": [{"timestamp": old_activity.isoformat(), "code": 200}],
    }

    assert _is_recent(admission, days=5)


def test_old_candidate_is_reported_without_recent_access(monkeypatch):
    service = configured_service(monkeypatch)
    old_limit = datetime.now(timezone.utc) - timedelta(days=30)
    recent_activity = datetime.now(timezone.utc) - timedelta(days=1)
    admission = {
        "status": {"overview": {"code": "completed"}},
        "candidate": {"name": "Pessoa Teste"},
        "limitDate": old_limit.isoformat(),
        "documentList": [{"timestamp": recent_activity.isoformat(), "code": 220}],
    }
    monkeypatch.setattr(service, "_request", lambda session, term, credential: ([admission], 1))

    rows = service.search(
        [SearchTerm(raw="Pessoa Teste", type="nome", key="pessoa teste")],
        credential="token",
        days=5,
    )

    assert rows[0]["Status"] == "Sem acesso recente"


@pytest.mark.parametrize("field", ["birthDate", "birthdate", "dateOfBirth", "dataNascimento"])
def test_search_includes_candidate_birth_date(monkeypatch, field):
    service = configured_service(monkeypatch)
    admission = {
        "candidate": {"name": "Pessoa Teste", field: "1992-06-15"},
        "status": {"overview": {"code": "completed"}},
    }
    monkeypatch.setattr(service, "_request", lambda session, term, credential: ([admission], 1))

    rows = service.search(
        [SearchTerm(raw="12345678900", type="cpf", key="12345678900")],
        credential="token",
        days=5,
    )

    assert rows[0]["Data de nascimento"] == "15/06/1992"


def test_search_reads_birth_date_from_candidate_person(monkeypatch):
    service = configured_service(monkeypatch)
    admission = {
        "candidate": {"name": "Pessoa Teste"},
        "persons": [
            {"personType": "dependent", "personData": {"dataNascimento": "2018-01-02"}},
            {"personType": "candidate", "personData": {"dataNascimento": "1992-06-15"}},
        ],
        "status": {"overview": {"code": "completed"}},
    }
    monkeypatch.setattr(service, "_request", lambda session, term, credential: ([admission], 1))

    rows = service.search(
        [SearchTerm(raw="12345678900", type="cpf", key="12345678900")],
        credential="token",
        days=5,
    )

    assert rows[0]["Data de nascimento"] == "15/06/1992"


def test_position_result_is_read_as_one_admission(monkeypatch):
    service = configured_service(monkeypatch)
    position = {
        "position": "position-test",
        "candidate": {"name": "Pessoa Teste"},
        "persons": [
            {"personType": "candidate", "personData": {"dataNascimento": "1992-06-15"}}
        ],
    }

    class PositionSession:
        def get(self, *args, **kwargs):
            class Response:
                status_code = 200

                def json(self):
                    return {"code": 200, "result": position, "status": "ok"}

            return Response()

    term = SearchTerm(raw="12345678900", type="cpf", key="12345678900")
    admissions, total = service._request(PositionSession(), term, "token")

    assert admissions == [position]
    assert total == 1


def test_search_fetches_birth_date_from_position(monkeypatch):
    service = configured_service(monkeypatch)
    admission = {
        "position": "position-test",
        "unit": {"uid": "unit-test"},
        "candidate": {"name": "Pessoa Teste"},
        "status": {"overview": {"code": "completed"}},
    }

    class PositionSession:
        def mount(self, *args, **kwargs):
            pass

        def get(self, url, **kwargs):
            assert url == "https://admin.acessorh.com.br/svc2/position"
            assert kwargs["params"] == {"uid": "position-test", "unit": "unit-test"}

            class Response:
                status_code = 200

                def json(self):
                    return {
                        "code": 200,
                        "result": {
                            "persons": [
                                {"personType": "dependent", "personData": {"dataNascimento": "2018-01-02"}},
                                {"personType": "candidate", "personData": {"dataNascimento": "1992-06-15"}},
                            ]
                        },
                    }

            return Response()

    monkeypatch.setattr(service, "_request", lambda session, term, credential: ([admission], 1))
    monkeypatch.setattr("app.unico_service.requests.Session", PositionSession)
    rows = service.search(
        [SearchTerm(raw="12345678900", type="cpf", key="12345678900")],
        credential="token",
        days=5,
    )
    assert rows[0]["Data de nascimento"] == "15/06/1992"


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [(401, UnicoCredentialError), (403, UnicoRequestError)],
)
def test_position_access_error_shows_unico_status(monkeypatch, status_code, error_type):
    service = configured_service(monkeypatch)
    monkeypatch.setattr("app.unico_service.time.sleep", lambda seconds: None)

    class PositionSession:
        def get(self, *args, **kwargs):
            class Response:
                pass

            response = Response()
            response.status_code = status_code
            return response

    admission = {"position": "position-test", "unit": {"uid": "unit-test"}}
    with pytest.raises(error_type, match=f"HTTP {status_code}"):
        service._position_birth_date(PositionSession(), admission, "token")


def test_missing_unit_is_reported_before_position_request(monkeypatch):
    service = configured_service(monkeypatch)
    admission = {"position": "position-test"}

    with pytest.raises(UnicoRequestError, match="identificador da unidade"):
        service._position_birth_date(FailingSession(), admission, "token")
