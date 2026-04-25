# mcp-polish-data

> MCP Server z polskimi danymi publicznymi — KRS, CEIDG, GUS BDL dla Claude, Cursor i Windsurf.

![Screenshot](./screenshot.png)

## Co to jest

Serwer Model Context Protocol (MCP), który daje asystentom AI bezpośredni dostęp do polskich rejestrów rządowych i statystyk GUS bez opuszczania chatu. Instalujesz raz, a Claude lub Cursor automatycznie wie, jak szukać spółek w KRS, weryfikować przedsiębiorców w CEIDG i pobierać dane regionalne z GUS BDL.

Open Source, MIT, bez wymagania klucza API.

## Funkcje

- **KRS** — wyszukiwanie spółek po nazwie, pobieranie pełnego odpisu z Krajowego Rejestru Sądowego (9-cyfrowy numer KRS)
- **CEIDG** — wyszukiwanie jednoosobowych działalności po nazwie, NIP, REGON lub nazwisku właściciela
- **GUS BDL** — populacja wg województw, stopa bezrobocia, średnie wynagrodzenie brutto, odkrywanie zmiennych statystycznych
- **Graceful degradation** — gdy CEIDG wymaga tokenu JWT, serwer podaje pomocny komunikat zamiast crashować
- **Zero konfiguracji** — instalacja jedną komendą pip, brak wymaganych kluczy API dla podstawowych funkcji
- **Python 3.11+** — async/await, httpx, FastMCP 2.0

## Stack

| Warstwa | Technologia |
|---------|-------------|
| Protokół | Model Context Protocol (MCP) |
| Framework | FastMCP 2.0 |
| HTTP | httpx (async) |
| Python | 3.11+ |
| Build | Hatchling |
| Testy | pytest, pytest-asyncio |
| Licencja | MIT |

## Uruchomienie

```bash
pip install mcp-polish-data
```

### Claude Desktop

Edytuj `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) lub `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "polish-data": {
      "command": "mcp-polish-data"
    }
  }
}
```

Zrestartuj Claude Desktop — narzędzia pojawią się automatycznie.

### Cursor / Windsurf

```bash
git clone https://github.com/emilpinski/mcp-polish-data
cd mcp-polish-data
pip install -e ".[dev]"
pytest tests/ -v -m "not integration"
```

## Dostępne narzędzia

| Narzędzie | Opis |
|-----------|------|
| `krs_search_company(name)` | Wyszukaj spółki po nazwie w KRS |
| `krs_get_company_details(krs_number)` | Pełny odpis dla numeru KRS (9 cyfr) |
| `ceidg_search_business(name, nip, regon, surname)` | Szukaj działalności w CEIDG |
| `gus_get_population(unit_name, year)` | Populacja wg województwa |
| `gus_get_unemployment_rate(year)` | Stopa bezrobocia wg województw |
| `gus_get_average_salary(year)` | Średnie wynagrodzenie brutto wg województw |
| `gus_search_variable(query)` | Odkrywaj zmienne statystyczne w GUS BDL |

## Zmienne środowiskowe

| Zmienna | Opis | Wymagana |
|---------|------|----------|
| `CEIDG_TOKEN` | JWT token dla zaawansowanych endpointów CEIDG | ❌ (opcjonalna) |

## Przykładowe prompty

- *"Znajdź adres i zarząd PKN Orlen"*
- *"Porównaj stopę bezrobocia w 2023 we wszystkich województwach"*
- *"Jakie jest średnie wynagrodzenie w Pomorskim vs Mazowieckim?"*
- *"Znajdź wszystkie spółki z 'technologie' w nazwie"*

## Status

Open Source — [PyPI: mcp-polish-data](https://pypi.org/project/mcp-polish-data/)

---
Built by [Emil Piński](https://emilpinski.pl)
