# mcp-polish-data

**MCP Server for Polish public data** — KRS, CEIDG, GUS BDL.

Give your AI assistant (Claude, Cursor, Windsurf) direct access to Polish government registries and statistics without leaving the chat.

## What is this?

A [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes three Polish public APIs as tools:

- **KRS** — National Court Register (spółki / companies)
- **CEIDG** — Central Register of Economic Activity (sole proprietorships)
- **GUS BDL** — Local Data Bank (regional statistics, demographics, unemployment, salaries)

Ask your AI: *"Find Orlen in KRS"* or *"What's the unemployment rate in Mazowieckie?"* — and it just works.

## Quick start

```bash
pip install mcp-polish-data
```

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "polish-data": {
      "command": "mcp-polish-data"
    }
  }
}
```

Restart Claude Desktop. The tools appear automatically.

### Cursor / Windsurf

Add to your MCP config the same way — both IDEs follow the same spec.

## Tools

| Tool | Description |
|------|-------------|
| `krs_search_company(name)` | Search companies by name in the National Court Register |
| `krs_get_company_details(krs_number)` | Full registry excerpt for a 9-digit KRS number |
| `ceidg_search_business(name, nip, regon, surname)` | Search sole proprietorships |
| `gus_get_population(unit_name, year)` | Population by voivodeship (16 regions) |
| `gus_get_unemployment_rate(year)` | Unemployment rate by voivodeship |
| `gus_get_average_salary(year)` | Average gross monthly salary by voivodeship |
| `gus_search_variable(query)` | Discover any statistical variable in GUS BDL |

## Example prompts

- *"Show me the registered address and board of PKN Orlen"*
- *"List top 10 companies in KRS with 'technologie' in their name"*
- *"Compare 2023 unemployment rates across all Polish voivodeships"*
- *"What's the average salary in Pomorskie vs Mazowieckie?"*
- *"Find any GUS variable related to renewable energy"*

## Development

```bash
git clone https://github.com/emilpinski/mcp-polish-data.git
cd mcp-polish-data
pip install -e ".[dev]"
pytest tests/ -v -m "not integration"  # unit tests (offline)
pytest tests/ -v                        # include live API tests
```

## Notes on API access

- **KRS** and **GUS BDL** — fully public, no API key needed.
- **CEIDG 2.0** — basic search works anonymously; some advanced endpoints require a free JWT token from [datastore.ceidg.gov.pl](https://datastore.ceidg.gov.pl/). The server degrades gracefully with a helpful message when a token is needed.

## License

MIT — use it, fork it, ship it.

## Contributing

PRs welcome. Ideas for next tools:
- REGON (Central Statistical Register)
- Rejestr Dłużników Niewypłacalnych
- Rejestr BDO (waste management)
- Monitor Sądowy i Gospodarczy

---

Built with [FastMCP](https://github.com/jlowin/fastmcp). Not affiliated with Polish government agencies — this is a community wrapper around their public APIs.
