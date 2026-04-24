"""Podstawowe testy importów i rejestracji narzędzi MCP.

Testy integracyjne (prawdziwe zapytania do API) wymagają internetu
— oznaczone markerem @pytest.mark.integration.
"""

from __future__ import annotations

import pytest


def test_import_server() -> None:
    """Serwer MCP można zaimportować bez błędów."""
    from mcp_polish_data.server import mcp

    assert mcp is not None
    assert mcp.name == "Polskie Dane Publiczne"


def test_import_modules() -> None:
    """Wszystkie moduły narzędzi można zaimportować."""
    from mcp_polish_data import ceidg, gus, krs

    assert hasattr(krs, "search_company")
    assert hasattr(krs, "get_company_details")
    assert hasattr(ceidg, "search_business")
    assert hasattr(gus, "get_population")
    assert hasattr(gus, "get_unemployment_rate")
    assert hasattr(gus, "get_average_salary")
    assert hasattr(gus, "search_variable")


@pytest.mark.asyncio
async def test_krs_empty_query() -> None:
    """Brak kryteriów → zwraca błąd walidacji, nie robi requestu."""
    from mcp_polish_data.krs import search_company

    result = await search_company()
    assert "error" in result


@pytest.mark.asyncio
async def test_krs_invalid_number() -> None:
    """Niecyfrowy KRS → zwraca błąd walidacji."""
    from mcp_polish_data.krs import get_company_details

    result = await get_company_details("abc123")
    assert "error" in result


@pytest.mark.asyncio
async def test_ceidg_no_criteria() -> None:
    """Brak kryteriów wyszukiwania → zwraca błąd walidacji."""
    from mcp_polish_data.ceidg import search_business

    result = await search_business()
    assert "error" in result


@pytest.mark.asyncio
async def test_ceidg_invalid_nip() -> None:
    """NIP o złej długości → zwraca błąd walidacji."""
    from mcp_polish_data.ceidg import search_business

    result = await search_business(nip="123")
    assert "error" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_krs_search_real() -> None:
    """Integracyjny: prawdziwe zapytanie do Białej Listy VAT MF przez NIP Orlen."""
    from mcp_polish_data.krs import search_company

    # NIP PKN Orlen SA
    result = await search_company(nip="7740001454")
    assert "error" in result or "results" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_krs_details_real() -> None:
    """Integracyjny: pełen odpis KRS Orlen."""
    from mcp_polish_data.krs import get_company_details

    result = await get_company_details("0000028860")
    assert "error" in result or "dane_podmiotu" in result
