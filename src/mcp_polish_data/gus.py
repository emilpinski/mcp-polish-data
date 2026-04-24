"""Narzędzia GUS BDL — Bank Danych Lokalnych Głównego Urzędu Statystycznego.

Publiczne API statystyczne — bez klucza dla podstawowych zapytań.
Dokumentacja: https://bdl.stat.gov.pl/api/v1/
Swagger: https://bdl.stat.gov.pl/api/v1/api-docs
"""

from __future__ import annotations

import httpx

GUS_BASE = "https://bdl.stat.gov.pl/api/v1"
TIMEOUT = httpx.Timeout(20.0, connect=5.0)
USER_AGENT = "mcp-polish-data/0.1 (+https://github.com/localfy/mcp-polish-data)"

# Kody zmiennych GUS BDL dla najczęstszych metryk
# (można znaleźć przez GET /variables?subject-id=...)
VARIABLES = {
    "ludnosc_ogolem": 72305,           # Ludność — stan w dniu 31 XII
    "bezrobocie_stopa": 60270,         # Stopa bezrobocia rejestrowanego
    "pkb_per_capita": 415001,          # PKB per capita wg województw
    "przecietne_wynagrodzenie": 1375,  # Przeciętne miesięczne wynagrodzenie brutto
    "przyrost_naturalny": 450646,      # Przyrost naturalny na 1000 ludności
}

# Poziomy jednostek administracyjnych w GUS BDL
UNIT_LEVELS = {
    "kraj": 0,
    "region": 1,
    "wojewodztwo": 2,
    "podregion": 3,
    "powiat": 4,
    "gmina": 5,
    "miasto": 6,
}


def _headers() -> dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }


async def _get(endpoint: str, params: dict | None = None) -> dict:
    """Wewnętrzny helper do GET na GUS BDL API."""
    url = f"{GUS_BASE}{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, headers=_headers()) as client:
            response = await client.get(url, params=params or {})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP {e.response.status_code} z GUS BDL",
            "details": e.response.text[:500],
        }
    except httpx.HTTPError as e:
        return {"error": "Błąd połączenia z GUS BDL", "details": str(e)}
    except ValueError as e:
        return {"error": "Niepoprawny JSON z GUS BDL", "details": str(e)}


async def get_population(unit_name: str | None = None, year: int = 2023) -> dict:
    """Pobierz dane demograficzne (ludność) dla województw lub wskazanej jednostki.

    Domyślnie zwraca ludność wszystkich 16 województw na 31 XII danego roku.

    Args:
        unit_name: nazwa województwa/gminy (None = wszystkie województwa)
        year: rok (domyślnie 2023)

    Returns:
        dict: {"variable": str, "year": int, "results": list[dict]}
        Każdy wynik: {"nazwa", "kod_teryt", "wartosc", "jednostka"}
    """
    variable_id = VARIABLES["ludnosc_ogolem"]
    params = {
        "format": "json",
        "year": year,
        "unit-level": UNIT_LEVELS["wojewodztwo"],
        "page-size": 100,
    }

    data = await _get(f"/data/by-variable/{variable_id}", params)
    if "error" in data:
        return data

    results = []
    for item in data.get("results", []):
        name = item.get("name", "")
        if unit_name and unit_name.lower() not in name.lower():
            continue
        values = item.get("values", [])
        value = values[0].get("val") if values else None
        results.append(
            {
                "nazwa": name,
                "kod_teryt": item.get("id"),
                "wartosc": value,
                "jednostka": "osoba",
            }
        )

    return {
        "variable": "Ludność — stan w dniu 31 XII",
        "year": year,
        "count": len(results),
        "results": results,
    }


async def get_unemployment_rate(year: int = 2023) -> dict:
    """Pobierz stopy bezrobocia rejestrowanego dla województw.

    Args:
        year: rok (domyślnie 2023)

    Returns:
        dict: stopy bezrobocia [%] dla 16 województw
    """
    variable_id = VARIABLES["bezrobocie_stopa"]
    params = {
        "format": "json",
        "year": year,
        "unit-level": UNIT_LEVELS["wojewodztwo"],
        "page-size": 100,
    }

    data = await _get(f"/data/by-variable/{variable_id}", params)
    if "error" in data:
        return data

    results = []
    for item in data.get("results", []):
        values = item.get("values", [])
        value = values[0].get("val") if values else None
        results.append(
            {
                "nazwa": item.get("name"),
                "kod_teryt": item.get("id"),
                "wartosc": value,
                "jednostka": "%",
            }
        )

    return {
        "variable": "Stopa bezrobocia rejestrowanego",
        "year": year,
        "count": len(results),
        "results": results,
    }


async def get_average_salary(year: int = 2023) -> dict:
    """Pobierz przeciętne miesięczne wynagrodzenie brutto dla województw.

    Args:
        year: rok (domyślnie 2023)

    Returns:
        dict: przeciętne wynagrodzenie [PLN] dla 16 województw
    """
    variable_id = VARIABLES["przecietne_wynagrodzenie"]
    params = {
        "format": "json",
        "year": year,
        "unit-level": UNIT_LEVELS["wojewodztwo"],
        "page-size": 100,
    }

    data = await _get(f"/data/by-variable/{variable_id}", params)
    if "error" in data:
        return data

    results = []
    for item in data.get("results", []):
        values = item.get("values", [])
        value = values[0].get("val") if values else None
        results.append(
            {
                "nazwa": item.get("name"),
                "kod_teryt": item.get("id"),
                "wartosc": value,
                "jednostka": "PLN",
            }
        )

    return {
        "variable": "Przeciętne miesięczne wynagrodzenie brutto",
        "year": year,
        "count": len(results),
        "results": results,
    }


async def search_variable(query: str, page_size: int = 20) -> dict:
    """Szukaj zmiennej statystycznej w GUS BDL po fragmencie nazwy.

    Przydatne gdy nie znasz konkretnego ID zmiennej.

    Args:
        query: fragment nazwy zmiennej (np. "bezrobocie", "PKB")
        page_size: liczba wyników

    Returns:
        dict: lista pasujących zmiennych z ich ID
    """
    params = {
        "format": "json",
        "name": query,
        "page-size": page_size,
    }

    data = await _get("/variables/search", params)
    if "error" in data:
        return data

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "id": item.get("id"),
                "nazwa": item.get("n1") or item.get("name"),
                "poziom": item.get("level"),
                "temat": item.get("subjectName"),
                "jednostka_miary": item.get("measureUnitName"),
            }
        )

    return {
        "query": query,
        "count": len(results),
        "results": results,
    }
