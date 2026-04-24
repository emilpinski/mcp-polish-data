"""Główny serwer MCP — Polskie Dane Publiczne.

Udostępnia narzędzia do publicznych API:
- KRS (Krajowy Rejestr Sądowy)
- CEIDG (Centralna Ewidencja Działalności Gospodarczej)
- GUS BDL (Bank Danych Lokalnych)

Uruchomienie:
    mcp-polish-data
lub:
    python -m mcp_polish_data.server

Konfiguracja w Claude Desktop (~/Library/Application Support/Claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "polish-data": {
          "command": "mcp-polish-data"
        }
      }
    }
"""

from __future__ import annotations

from fastmcp import FastMCP

from . import ceidg, gus, krs

mcp = FastMCP("Polskie Dane Publiczne")


# ---------------------- KRS ----------------------

@mcp.tool()
async def krs_search_company(nip: str | None = None, name: str | None = None, max_items: int = 10) -> dict:
    """Szukaj podmiotu gospodarczego — preferowana metoda po NIP.

    Używa Białej Listy VAT Ministerstwa Finansów — zwraca dane dowolnego
    podatnika (spółki, JDG, instytucji) po numerze NIP:
    nazwa, REGON, numer KRS, adres, zarząd, wspólnicy, rachunki bankowe.

    Publiczne API KRS nie obsługuje wyszukiwania po nazwie — dlatego
    najlepszą metodą identyfikacji podmiotu jest NIP.

    Args:
        nip: numer NIP (10 cyfr) — preferowane
        name: nazwa firmy (zwraca instrukcje, bo API nie wspiera search-by-name)
        max_items: maksymalna liczba wyników

    Returns:
        Dane podmiotu z Białej Listy VAT wraz z numerem KRS (gdy spółka).
    """
    return await krs.search_company(nip=nip, name=name, max_items=max_items)


@mcp.tool()
async def krs_get_company_details(krs_number: str) -> dict:
    """Pobierz pełne dane spółki z KRS na podstawie numeru KRS.

    Zwraca pełen odpis aktualny: dane rejestrowe, siedzibę, zarząd,
    kapitał zakładowy, PKD, prokurentów, sprawozdania finansowe.

    Args:
        krs_number: 9- lub 10-cyfrowy numer KRS (np. "0000127815" dla Orlen)

    Returns:
        Pełny odpis aktualny spółki z KRS.
    """
    return await krs.get_company_details(krs_number)


# ---------------------- CEIDG ----------------------

@mcp.tool()
async def ceidg_search_business(
    name: str | None = None,
    nip: str | None = None,
    regon: str | None = None,
    surname: str | None = None,
    max_items: int = 10,
) -> dict:
    """Szukaj przedsiębiorcy (jednoosobowej działalności gospodarczej) w CEIDG.

    Użyj gdy użytkownik pyta o JDG, freelancera, osobę fizyczną prowadzącą
    działalność gospodarczą. Dla spółek użyj krs_search_company.

    Wymaga co najmniej jednego z: name, nip, regon, surname.

    Args:
        name: nazwa firmy
        nip: numer NIP (10 cyfr)
        regon: numer REGON (9 lub 14 cyfr)
        surname: nazwisko przedsiębiorcy
        max_items: maksymalna liczba wyników

    Returns:
        Lista przedsiębiorców z CEIDG — imię, nazwisko, NIP, REGON, adres, status.
    """
    return await ceidg.search_business(name, nip, regon, surname, max_items)


# ---------------------- GUS BDL ----------------------

@mcp.tool()
async def gus_get_population(unit_name: str | None = None, year: int = 2023) -> dict:
    """Pobierz dane demograficzne (ludność) z GUS BDL.

    Domyślnie zwraca ludność wszystkich 16 województw na 31 XII danego roku.
    Podaj unit_name (np. "Mazowieckie") aby zawęzić wyniki.

    Args:
        unit_name: nazwa województwa (opcjonalnie)
        year: rok (domyślnie 2023)

    Returns:
        Ludność według województw — liczba osób na 31 XII.
    """
    return await gus.get_population(unit_name, year)


@mcp.tool()
async def gus_get_unemployment_rate(year: int = 2023) -> dict:
    """Pobierz stopy bezrobocia rejestrowanego dla 16 województw z GUS BDL.

    Args:
        year: rok (domyślnie 2023)

    Returns:
        Stopa bezrobocia [%] dla każdego województwa.
    """
    return await gus.get_unemployment_rate(year)


@mcp.tool()
async def gus_get_average_salary(year: int = 2023) -> dict:
    """Pobierz przeciętne miesięczne wynagrodzenie brutto dla województw z GUS BDL.

    Args:
        year: rok (domyślnie 2023)

    Returns:
        Przeciętne wynagrodzenie [PLN] dla każdego z 16 województw.
    """
    return await gus.get_average_salary(year)


@mcp.tool()
async def gus_search_variable(query: str, page_size: int = 20) -> dict:
    """Szukaj zmiennej statystycznej w GUS BDL po fragmencie nazwy.

    Użyj gdy potrzebujesz wskaźnika którego nie ma w dedykowanych narzędziach
    (np. "emisja CO2", "liczba lekarzy", "turystyka").

    Args:
        query: fragment nazwy zmiennej
        page_size: liczba wyników

    Returns:
        Lista zmiennych z ich ID, nazwą, tematem i jednostką miary.
    """
    return await gus.search_variable(query, page_size)


# ---------------------- Entry point ----------------------

def main() -> None:
    """Uruchom serwer MCP na stdio (standardowy transport dla Claude Desktop)."""
    mcp.run()


if __name__ == "__main__":
    main()
