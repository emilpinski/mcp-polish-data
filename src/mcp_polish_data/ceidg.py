"""Narzędzia CEIDG — Centralna Ewidencja i Informacja o Działalności Gospodarczej.

Publiczne API rządowe — dane jednoosobowych działalności gospodarczych.
Dokumentacja: https://datastore.ceidg.gov.pl/
"""

from __future__ import annotations

import httpx

# Publiczny endpoint CEIDG (CEIDG.Public.UI) — bez klucza dla podstawowych zapytań.
# Uwaga: pełny dostęp do API CEIDG 2.0 wymaga tokena z datastore.ceidg.gov.pl,
# ale publiczny wyszukiwarkowy endpoint jest dostępny bez autoryzacji.
CEIDG_PUBLIC_BASE = "https://aplikacja.ceidg.gov.pl/CEIDG/CEIDG.Public.UI"
CEIDG_API_BASE = "https://dane.biznes.gov.pl/api/ceidg/v2"

TIMEOUT = httpx.Timeout(15.0, connect=5.0)
USER_AGENT = "mcp-polish-data/0.1 (+https://github.com/localfy/mcp-polish-data)"


def _headers() -> dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }


async def search_business(
    name: str | None = None,
    nip: str | None = None,
    regon: str | None = None,
    surname: str | None = None,
    max_items: int = 10,
) -> dict:
    """Szukaj przedsiębiorcy w CEIDG.

    Wymaga co najmniej jednego parametru (name, nip, regon lub surname).

    Args:
        name: nazwa firmy (np. "Kowalski Consulting")
        nip: numer NIP (10 cyfr)
        regon: numer REGON (9 lub 14 cyfr)
        surname: nazwisko przedsiębiorcy
        max_items: maksymalna liczba wyników

    Returns:
        dict: {"query": dict, "count": int, "results": list[dict]}
        Każdy wynik: nazwa, imie, nazwisko, nip, regon, adres, status.
    """
    if not any([name, nip, regon, surname]):
        return {
            "error": "Brak kryteriów wyszukiwania",
            "details": "Podaj co najmniej: name, nip, regon lub surname",
        }

    params: dict[str, str] = {}
    if nip:
        # Wyczyść NIP z ewentualnych myślników i spacji
        clean_nip = "".join(c for c in nip if c.isdigit())
        if len(clean_nip) != 10:
            return {
                "error": "Niepoprawny NIP",
                "details": f"NIP powinien mieć 10 cyfr, otrzymano: {nip}",
            }
        params["nip"] = clean_nip
    if regon:
        clean_regon = "".join(c for c in regon if c.isdigit())
        if len(clean_regon) not in (9, 14):
            return {
                "error": "Niepoprawny REGON",
                "details": f"REGON powinien mieć 9 lub 14 cyfr, otrzymano: {regon}",
            }
        params["regon"] = clean_regon
    if name:
        params["nazwa"] = name.strip()
    if surname:
        params["nazwisko"] = surname.strip()

    params["limit"] = str(max_items)

    url = f"{CEIDG_API_BASE}/firmy"

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, headers=_headers()) as client:
            response = await client.get(url, params=params)
            # CEIDG v2 publiczny — niektóre endpointy wymagają tokena
            if response.status_code == 401 or response.status_code == 403:
                return _fallback_message(params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        return {
            "error": "Błąd połączenia z CEIDG API",
            "details": str(e),
            "hint": (
                "Pełny dostęp do CEIDG 2.0 wymaga darmowego tokena z "
                "https://datastore.ceidg.gov.pl/ — dla jednoosobowych DG."
            ),
            "query": params,
            "count": 0,
            "results": [],
        }
    except ValueError as e:
        return {"error": "Niepoprawna odpowiedź JSON z CEIDG", "details": str(e)}

    items = data.get("firmy", data.get("items", data if isinstance(data, list) else []))

    results = []
    for item in items[:max_items]:
        if not isinstance(item, dict):
            continue
        wlasciciel = item.get("wlasciciel", {}) if isinstance(item.get("wlasciciel"), dict) else {}
        adres = item.get("adresDzialalnosci", item.get("adres", {}))
        results.append(
            {
                "nazwa": item.get("nazwa"),
                "imie": wlasciciel.get("imie"),
                "nazwisko": wlasciciel.get("nazwisko"),
                "nip": item.get("wlasciciel", {}).get("nip") if isinstance(item.get("wlasciciel"), dict) else item.get("nip"),
                "regon": item.get("wlasciciel", {}).get("regon") if isinstance(item.get("wlasciciel"), dict) else item.get("regon"),
                "status": item.get("status"),
                "data_rozpoczecia": item.get("dataRozpoczecia"),
                "adres": adres,
                "pkd_glowne": item.get("pkdGlowny"),
            }
        )

    return {
        "query": params,
        "count": len(results),
        "results": results,
    }


def _fallback_message(params: dict) -> dict:
    """Zwróć komunikat informacyjny gdy CEIDG wymaga tokena."""
    return {
        "error": "CEIDG 2.0 wymaga tokena",
        "details": (
            "Publiczne API CEIDG 2.0 wymaga darmowego tokena JWT. "
            "Zarejestruj się na https://datastore.ceidg.gov.pl/ "
            "i ustaw zmienną środowiskową CEIDG_TOKEN."
        ),
        "query": params,
        "count": 0,
        "results": [],
        "registration_url": "https://datastore.ceidg.gov.pl/",
    }
