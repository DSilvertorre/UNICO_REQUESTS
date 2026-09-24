import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchTerm:
    raw: str
    type: str
    key: str


def normalize_key(value: object) -> str:
    text = str(value or "")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.lower().strip()


def compact_spaces(value: object) -> str:
    return re.sub(r"\s+", " ", normalize_key(value)).strip()


def normalize_email(value: object) -> str:
    return str(value or "").strip().lower()


def normalize_cpf(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""

    text = re.sub(r"\.0+$", "", text)
    digits = re.sub(r"\D", "", text)

    if len(digits) != 11:
        return ""

    return digits


def detect_search_type(raw: str) -> str:
    if "@" in normalize_email(raw):
        return "email"

    if normalize_cpf(raw):
        return "cpf"

    return "nome"


def parse_search_terms(values: list[str], forced_type: str = "auto") -> list[SearchTerm]:
    terms: list[SearchTerm] = []

    for value in values:
        for raw in re.split(r"[\r\n,;]+", str(value or "")):
            raw = raw.strip()
            if not raw:
                continue

            search_type = detect_search_type(raw) if forced_type == "auto" else forced_type

            if search_type == "cpf":
                key = normalize_cpf(raw)
            elif search_type == "email":
                key = normalize_email(raw)
            elif search_type == "nome":
                key = compact_spaces(raw)
            else:
                continue

            if not key:
                continue

            terms.append(SearchTerm(raw=raw, type=search_type, key=key))

    return terms


def clean_cell_value(value: object) -> str:
    if value is None:
        return ""

    text = str(value)
    if text == "NaN":
        return ""

    return re.sub(r"\.0+$", "", text)
