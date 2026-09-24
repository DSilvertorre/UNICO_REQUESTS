from app.search_utils import normalize_cpf, normalize_email, parse_search_terms


def test_normalize_cpf_removes_punctuation_and_excel_decimal():
    assert normalize_cpf("123.456.789-00") == "12345678900"
    assert normalize_cpf("12345678900.0") == "12345678900"


def test_normalize_cpf_rejects_values_with_other_than_eleven_digits():
    assert normalize_cpf("1234567890") == ""
    assert normalize_cpf("123456789000") == ""


def test_normalize_email_lowercases_and_trims():
    assert normalize_email("  Pessoa@Email.COM ") == "pessoa@email.com"


def test_parse_search_terms_detects_types_and_preserves_duplicates_in_order():
    terms = parse_search_terms(
        [
            "123.456.789-00",
            "12345678900",
            "Pessoa@Email.COM",
            "Maria da Silva",
        ]
    )

    assert [(term.type, term.key) for term in terms] == [
        ("cpf", "12345678900"),
        ("cpf", "12345678900"),
        ("email", "pessoa@email.com"),
        ("nome", "maria da silva"),
    ]
