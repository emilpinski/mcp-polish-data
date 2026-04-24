"""Narzędzia KRS — Krajowy Rejestr Sądowy + wyszukiwanie przez Białą Listę VAT MF.

Łączy dwa publiczne API:
- api-krs.ms.gov.pl — pobieranie pełnego odpisu po numerze KRS
- wl-api.mf.gov.pl  — wyszukiwanie podmiotów po NIP (Biała Lista VAT MF)

Oba API są darmowe i nie wymagają klucza.
"""

from __future__ import annotations

from datetime import date

import httpx

KRS_BASE = "https://api-krs.ms.gov.pl/api/Krs"
MF_VAT_BASE = "https://wl-api.mf.gov.pl/api/search"

TIMEOUT = httpx.Timeout(15.0, connect=5.0)
USER_AGENT = "mcp-polish-data/0.1 (+https://github.com/localfy/mcp-polish-data)"


def _headers() -> dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }


async def search_company(nip: str | None = None, name: str | None = None, max_items: int = 10) -> dict:
    """Szukaj spółki / podmiotu gospodarczego.

    Preferuje wyszukiwanie po NIP (dokładne, przez Białą Listę VAT MF).
    Jeśli podano tylko nazwę — zwraca komunikat bo publiczne KRS API
    nie obsługuje wyszukiwania po nazwie (tylko po numerze KRS).

    Args:
        nip: numer NIP (10 cyfr) — preferowana metoda wyszukiwania
        name: nazwa firmy (tylko jako fallback, zwraca instrukcje)
        max_items: maksymalna liczba wyników

    Returns:
        dict: dane podmiotu z Białej Listy VAT — nazwa, NIP, REGON,
              numer KRS (jeśli spółka), adres, zarząd, wspólnicy.
    """
    if not nip and not name:
        return {
            "error": "Brak kryteriów wyszukiwania",
            "details": "Podaj numer NIP (10 cyfr) — preferowana metoda.",
        }

    if nip:
        return await _search_by_nip(nip)

    # Tylko nazwa — KRS nie ma publicznego endpointu search-by-name.
    return {
        "error": "Wyszukiwanie po nazwie niedostępne",
        "details": (
            f"Publiczne API KRS oraz Biała Lista VAT MF nie obsługują wyszukiwania "
            f"po nazwie. Podaj numer NIP (10 cyfr) dla '{name}' lub numer KRS "
            f"(10 cyfr) i użyj krs_get_company_details. Numery KRS można znaleźć "
            f"przez wyszukiwarkę: https://wyszukiwarka-krs.ms.gov.pl/"
        ),
        "query": {"name": name},
        "count": 0,
        "results": [],
    }


async def _search_by_nip(nip: str) -> dict:
    """Wyszukiwanie podmiotu po NIP przez Białą Listę VAT Ministerstwa Finansów."""
    clean_nip = "".join(c for c in nip if c.isdigit())
    if len(clean_nip) != 10:
        return {
            "error": "Niepoprawny NIP",
            "details": f"NIP powinien mieć 10 cyfr, otrzymano: {nip}",
        }

    today = date.today().isoformat()
    url = f"{MF_VAT_BASE}/nip/{clean_nip}"
    params = {"date": today}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, headers=_headers()) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP {e.response.status_code} z Białej Listy VAT",
            "details": e.response.text[:300],
            "nip": clean_nip,
        }
    except httpx.HTTPError as e:
        return {"error": "Błąd połączenia z API MF", "details": str(e), "nip": clean_nip}
    except ValueError as e:
        return {"error": "Niepoprawny JSON z MF", "details": str(e), "nip": clean_nip}

    subject = (data.get("result") or {}).get("subject")
    if not subject:
        return {
            "query": {"nip": clean_nip},
            "count": 0,
            "results": [],
            "info": "Podmiot nie został znaleziony w Białej Liście VAT",
        }

    result = {
        "nazwa": subject.get("name"),
        "nip": subject.get("nip"),
        "regon": subject.get("regon"),
        "krs": subject.get("krs"),
        "status_vat": subject.get("statusVat"),
        "adres_rejestrowy": subject.get("residenceAddress"),
        "adres_dzialalnosci": subject.get("workingAddress"),
        "reprezentanci": subject.get("representatives", []),
        "pelnomocnicy": subject.get("authorizedClerks", []),
        "wspolnicy": subject.get("partners", []),
        "data_rejestracji": subject.get("registrationLegalDate"),
        "data_wykreslenia": subject.get("removalDate"),
        "rachunki_bankowe": subject.get("accountNumbers", []),
    }

    return {
        "query": {"nip": clean_nip},
        "count": 1,
        "results": [result],
    }


async def get_company_details(krs_number: str) -> dict:
    """Pobierz pełen odpis aktualny z KRS na podstawie numeru.

    Args:
        krs_number: 9- lub 10-cyfrowy numer KRS (np. "0000028860" dla PKN Orlen)

    Returns:
        dict: pełny odpis — nagłówek, dane podmiotu, siedziba, kapitał,
              organ reprezentacji, organ nadzoru, prokurenci, przedmiot
              działalności, wspólnicy, sprawozdania finansowe.
    """
    if not krs_number or not krs_number.strip():
        return {"error": "Pusty numer KRS", "details": "Podaj 9- lub 10-cyfrowy numer KRS"}

    krs = krs_number.strip().zfill(10)
    if not krs.isdigit() or len(krs) > 10:
        return {
            "error": "Niepoprawny numer KRS",
            "details": f"Oczekiwano cyfr (max 10), otrzymano: {krs_number}",
        }

    # Spróbuj rejestru przedsiębiorców (P), potem stowarzyszeń (S) jako fallback.
    for rejestr in ("P", "S"):
        url = f"{KRS_BASE}/OdpisAktualny/{krs}"
        params = {"rejestr": rejestr, "format": "json"}

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT, headers=_headers()) as client:
                response = await client.get(url, params=params)
        except httpx.HTTPError as e:
            return {"error": "Błąd połączenia z KRS API", "details": str(e), "krs": krs}

        if response.status_code == 204:
            # 204 = brak w tym rejestrze, spróbuj następnego
            continue
        if response.status_code == 404:
            continue
        if response.status_code != 200:
            return {
                "error": f"HTTP {response.status_code} z KRS",
                "details": response.text[:300],
                "krs": krs,
            }

        try:
            data = response.json()
        except ValueError as e:
            return {"error": "Niepoprawny JSON z KRS", "details": str(e), "krs": krs}

        return _parse_krs_odpis(krs, rejestr, data)

    return {
        "error": "Nie znaleziono podmiotu",
        "details": f"KRS {krs} nie istnieje w rejestrze przedsiębiorców ani stowarzyszeń",
        "krs": krs,
    }


def _parse_krs_odpis(krs: str, rejestr: str, data: dict) -> dict:
    """Wyciągnij najważniejsze pola z pełnego odpisu KRS."""
    odpis = data.get("odpis", data)
    naglowek = odpis.get("naglowekA") or odpis.get("naglowekP") or {}
    dane = odpis.get("dane", {})
    dzial1 = dane.get("dzial1", {}) or {}
    dzial2 = dane.get("dzial2", {}) or {}
    dzial3 = dane.get("dzial3", {}) or {}

    return {
        "krs": krs,
        "rejestr": "przedsiębiorców" if rejestr == "P" else "stowarzyszeń",
        "stan_z_dnia": naglowek.get("stanZDnia"),
        "data_rejestracji": naglowek.get("dataRejestracjiWKRS"),
        "numer_ostatniego_wpisu": naglowek.get("numerOstatniegoWpisu"),
        "data_ostatniego_wpisu": naglowek.get("dataOstatniegoWpisu"),
        "sad": naglowek.get("oznaczenieSaduDokonujacegoOstatniegoWpisu"),
        "dane_podmiotu": dzial1.get("danePodmiotu"),
        "siedziba_i_adres": dzial1.get("siedzibaIAdres"),
        "identyfikatory": dzial1.get("danePodmiotu", {}).get("identyfikatory") if isinstance(dzial1.get("danePodmiotu"), dict) else None,
        "kapital": dzial1.get("kapital"),
        "organ_reprezentacji": dzial2.get("reprezentacja"),
        "organ_nadzoru": dzial2.get("organNadzoru"),
        "prokurenci": dzial2.get("prokurenci"),
        "przedmiot_dzialalnosci": dzial3.get("przedmiotDzialalnosci"),
        "sprawozdania_finansowe": dzial3.get("sprawozdaniaFinansoweIOpinieBieglychRewidentow"),
        "raw": data,
    }
