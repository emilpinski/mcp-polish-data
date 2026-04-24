"""Vercel Python handler — Polish Data REST API."""

from http.server import BaseHTTPRequestHandler
import json
import asyncio
import sys
import os
import urllib.parse

# Add src/ to path so we can import mcp_polish_data
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_polish_data.krs import search_company as krs_search, get_company_details as krs_details
from mcp_polish_data.ceidg import search_business as ceidg_search
from mcp_polish_data.gus import get_population, get_unemployment_rate

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
}

LANDING_HTML = """<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Polish Data API &mdash; Pierwsze polskie API danych publicznych</title>
<meta name="description" content="Darmowe REST API do polskich danych publicznych: KRS, CEIDG, GUS BDL. Bez klucza API. Dla polskich programist&oacute;w.">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0a0a0f;
    --surface: #111118;
    --surface2: #16161f;
    --border: #1e1e2e;
    --green: #22c55e;
    --green-dim: #166534;
    --green-glow: rgba(34,197,94,0.12);
    --text: #e2e8f0;
    --muted: #64748b;
    --muted2: #94a3b8;
  }

  html { scroll-behavior: smooth; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.6;
    font-size: 16px;
    min-height: 100vh;
  }

  /* ---- NAV ---- */
  nav {
    position: sticky; top: 0; z-index: 100;
    background: rgba(10,10,15,0.85);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 0 1.5rem;
    display: flex; align-items: center; justify-content: space-between;
    height: 56px;
  }
  .nav-logo {
    font-weight: 700; font-size: 0.95rem; color: var(--text); letter-spacing: -0.02em;
    display: flex; align-items: center; gap: 0.5rem;
  }
  .nav-logo .dot { width: 8px; height: 8px; background: var(--green); border-radius: 50%; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:.4;} }
  .nav-links { display: flex; gap: 1.5rem; }
  .nav-links a { color: var(--muted2); font-size: 0.875rem; text-decoration: none; transition: color .15s; }
  .nav-links a:hover { color: var(--text); }

  /* ---- LAYOUT ---- */
  .container { max-width: 1000px; margin: 0 auto; padding: 0 1.5rem; }

  /* ---- HERO ---- */
  .hero {
    padding: 6rem 1.5rem 4rem;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse 70% 50% at 50% 0%, rgba(34,197,94,0.08), transparent);
    pointer-events: none;
  }
  .hero-badge {
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 100px; padding: 0.3rem 0.9rem;
    font-size: 0.8rem; color: var(--muted2); margin-bottom: 2rem;
  }
  .hero-badge .flag { font-size: 1rem; }
  .hero h1 {
    font-size: clamp(2.2rem, 5vw, 3.5rem);
    font-weight: 800; letter-spacing: -0.04em;
    line-height: 1.1; margin-bottom: 1.2rem;
  }
  .hero h1 em { color: var(--green); font-style: normal; }
  .hero-sub {
    font-size: 1.15rem; color: var(--muted2);
    max-width: 540px; margin: 0 auto 1rem;
  }
  .hero-tags {
    display: flex; justify-content: center; gap: 0.5rem;
    flex-wrap: wrap; margin-bottom: 2.5rem;
  }
  .tag {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 0.25rem 0.75rem;
    font-size: 0.8rem; font-weight: 600; color: var(--muted2); letter-spacing: 0.05em;
  }
  .hero-ctas { display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; }
  .btn {
    display: inline-flex; align-items: center; gap: 0.5rem;
    padding: 0.65rem 1.4rem; border-radius: 8px;
    font-size: 0.9rem; font-weight: 600; cursor: pointer;
    text-decoration: none; border: none; transition: all .15s;
  }
  .btn-primary {
    background: var(--green); color: #0a0a0f;
  }
  .btn-primary:hover { background: #16a34a; transform: translateY(-1px); }
  .btn-secondary {
    background: var(--surface); color: var(--text);
    border: 1px solid var(--border);
  }
  .btn-secondary:hover { background: var(--surface2); border-color: var(--muted); }

  /* ---- SECTION ---- */
  section { padding: 4rem 1.5rem; }
  .section-label {
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--green); margin-bottom: 0.75rem;
  }
  .section-title {
    font-size: 1.75rem; font-weight: 700; letter-spacing: -0.03em;
    margin-bottom: 0.5rem;
  }
  .section-desc { color: var(--muted2); margin-bottom: 2.5rem; font-size: 0.95rem; }

  /* ---- LIVE DEMO ---- */
  .demo-wrapper {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px; overflow: hidden;
  }
  .demo-topbar {
    background: var(--surface2); border-bottom: 1px solid var(--border);
    padding: 0.75rem 1.25rem;
    display: flex; align-items: center; gap: 0.5rem;
  }
  .demo-dot { width: 10px; height: 10px; border-radius: 50%; }
  .demo-dot.red { background: #ef4444; }
  .demo-dot.yellow { background: #f59e0b; }
  .demo-dot.green { background: #22c55e; }
  .demo-title { margin-left: 0.5rem; font-size: 0.8rem; color: var(--muted); }
  .demo-body { padding: 1.5rem; }
  .demo-search {
    display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap;
  }
  .demo-input {
    flex: 1; min-width: 200px;
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; padding: 0.65rem 1rem;
    color: var(--text); font-size: 0.9rem; outline: none;
    transition: border-color .15s;
  }
  .demo-input:focus { border-color: var(--green); }
  .demo-input::placeholder { color: var(--muted); }
  .demo-examples {
    display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.5rem;
  }
  .example-chip {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 100px; padding: 0.25rem 0.85rem;
    font-size: 0.78rem; color: var(--muted2); cursor: pointer;
    transition: all .15s;
  }
  .example-chip:hover { border-color: var(--green); color: var(--green); }
  .demo-result {
    min-height: 120px;
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.25rem;
    font-size: 0.875rem;
  }
  .result-empty { color: var(--muted); font-size: 0.85rem; }
  .result-spinner {
    display: flex; align-items: center; gap: 0.75rem;
    color: var(--muted2);
  }
  .spinner {
    width: 18px; height: 18px; border: 2px solid var(--border);
    border-top-color: var(--green); border-radius: 50%;
    animation: spin .7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .result-card { }
  .result-name {
    font-size: 1.05rem; font-weight: 700; color: var(--text);
    margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;
  }
  .result-row {
    display: flex; flex-wrap: wrap; gap: 0.25rem 1.5rem;
    color: var(--muted2); font-size: 0.82rem; margin-bottom: 0.5rem;
  }
  .result-row span { color: var(--text); font-weight: 500; }
  .result-address { color: var(--muted2); font-size: 0.82rem; margin-bottom: 0.5rem; }
  .result-vat {
    display: inline-flex; align-items: center; gap: 0.35rem;
    font-size: 0.8rem; font-weight: 600;
    background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.2);
    color: var(--green); border-radius: 6px; padding: 0.2rem 0.6rem;
    margin-top: 0.25rem;
  }
  .result-error {
    color: #f87171; font-size: 0.85rem;
    display: flex; align-items: center; gap: 0.5rem;
  }

  /* ---- ENDPOINTS ---- */
  .endpoints-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.25rem;
  }
  .endpoint-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.5rem;
    transition: border-color .2s, transform .2s;
  }
  .endpoint-card:hover { border-color: rgba(34,197,94,0.35); transform: translateY(-2px); }
  .endpoint-icon {
    width: 40px; height: 40px; border-radius: 10px;
    background: var(--green-glow); border: 1px solid rgba(34,197,94,0.2);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; margin-bottom: 1rem;
  }
  .endpoint-name {
    font-weight: 700; font-size: 1rem; margin-bottom: 0.25rem;
  }
  .endpoint-full-name {
    font-size: 0.78rem; color: var(--muted); margin-bottom: 0.75rem;
  }
  .endpoint-desc {
    font-size: 0.85rem; color: var(--muted2); margin-bottom: 1rem; line-height: 1.5;
  }
  .endpoint-routes { display: flex; flex-direction: column; gap: 0.4rem; }
  .route {
    font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace;
    font-size: 0.75rem; color: var(--muted2);
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 5px; padding: 0.3rem 0.6rem;
    word-break: break-all;
  }
  .route .method {
    color: var(--green); font-weight: 700; margin-right: 0.4rem;
  }

  /* ---- MCP ---- */
  .mcp-wrapper {
    display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: start;
  }
  @media (max-width: 680px) { .mcp-wrapper { grid-template-columns: 1fr; } }
  .mcp-text h3 { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; }
  .mcp-text p { color: var(--muted2); font-size: 0.9rem; line-height: 1.7; margin-bottom: 0.75rem; }
  .mcp-steps { list-style: none; display: flex; flex-direction: column; gap: 0.75rem; }
  .mcp-step {
    display: flex; align-items: flex-start; gap: 0.75rem; font-size: 0.875rem;
  }
  .step-num {
    flex-shrink: 0; width: 22px; height: 22px; border-radius: 50%;
    background: var(--green-glow); border: 1px solid rgba(34,197,94,0.3);
    color: var(--green); font-size: 0.72rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
  }
  .code-block {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; overflow: hidden;
  }
  .code-header {
    background: var(--surface2); border-bottom: 1px solid var(--border);
    padding: 0.6rem 1rem;
    display: flex; align-items: center; justify-content: space-between;
  }
  .code-lang { font-size: 0.75rem; color: var(--muted); }
  .code-copy {
    font-size: 0.72rem; color: var(--muted); background: none; border: none;
    cursor: pointer; padding: 0.2rem 0.5rem; border-radius: 4px;
    transition: color .15s;
  }
  .code-copy:hover { color: var(--text); }
  .code-body {
    padding: 1.1rem 1.25rem;
    font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace;
    font-size: 0.82rem; color: #a9b1d6; line-height: 1.8;
    overflow-x: auto;
    white-space: pre;
  }
  .code-body .k { color: #bb9af7; }
  .code-body .s { color: #9ece6a; }
  .code-body .p { color: #e2e8f0; }
  .code-body .c { color: #565f89; font-style: italic; }

  /* ---- FOOTER ---- */
  footer {
    border-top: 1px solid var(--border);
    padding: 2rem 1.5rem;
    text-align: center; color: var(--muted); font-size: 0.85rem;
  }
  footer a { color: var(--muted2); text-decoration: none; }
  footer a:hover { color: var(--text); }

  /* ---- DIVIDER ---- */
  .divider { border: none; border-top: 1px solid var(--border); }

  @media (max-width: 600px) {
    .nav-links { display: none; }
    .demo-search { flex-direction: column; }
  }
</style>
</head>
<body>

<!-- NAV -->
<nav>
  <div class="nav-logo">
    <div class="dot"></div>
    Polish Data API
  </div>
  <div class="nav-links">
    <a href="#demo">Demo</a>
    <a href="#endpoints">Endpoints</a>
    <a href="#mcp">MCP</a>
    <a href="https://github.com/emilpinski/mcp-polish-data" target="_blank">GitHub</a>
  </div>
</nav>

<!-- HERO -->
<div class="hero">
  <div class="hero-badge">
    <span class="flag">&#127477;&#127473;</span>
    Pierwsze polskie API danych publicznych
  </div>
  <div class="container">
    <h1>Dane firm w <em>jednym</em> API</h1>
    <p class="hero-sub">Darmowy dostęp do KRS, CEIDG i GUS BDL. Bez klucza API. Dla polskich programistów.</p>
    <div class="hero-tags">
      <span class="tag">KRS</span>
      <span class="tag">CEIDG</span>
      <span class="tag">GUS BDL</span>
      <span class="tag">REST API</span>
      <span class="tag">MCP Server</span>
    </div>
    <div class="hero-ctas">
      <a href="#demo" class="btn btn-primary">Przetestuj &rarr;</a>
      <a href="https://github.com/emilpinski/mcp-polish-data" target="_blank" class="btn btn-secondary">&#128196; GitHub</a>
    </div>
  </div>
</div>

<!-- DEMO -->
<section id="demo">
  <div class="container">
    <div class="section-label">Live Demo</div>
    <h2 class="section-title">Sprawdź dowolną firmę</h2>
    <p class="section-desc">Wpisz NIP i zobacz dane z KRS w czasie rzeczywistym.</p>

    <div class="demo-wrapper">
      <div class="demo-topbar">
        <div class="demo-dot red"></div>
        <div class="demo-dot yellow"></div>
        <div class="demo-dot green"></div>
        <span class="demo-title">GET /api/krs?nip=...</span>
      </div>
      <div class="demo-body">
        <div class="demo-search">
          <input
            id="nip-input"
            class="demo-input"
            type="text"
            placeholder="Wpisz NIP firmy (np. 7740001454)"
            maxlength="13"
          />
          <button class="btn btn-primary" onclick="searchNip()">Szukaj</button>
        </div>
        <div class="demo-examples">
          <span class="example-chip" onclick="setNip('7740001454')">Orlen (7740001454)</span>
          <span class="example-chip" onclick="setNip('5260215088')">mBank (5260215088)</span>
          <span class="example-chip" onclick="setNip('5250007738')">PKO BP (5250007738)</span>
        </div>
        <div class="demo-result" id="demo-result">
          <span class="result-empty">Wyniki pojawi&#261; si&#281; tutaj &mdash; wybierz przykład lub wpisz NIP.</span>
        </div>
      </div>
    </div>
  </div>
</section>

<hr class="divider">

<!-- ENDPOINTS -->
<section id="endpoints">
  <div class="container">
    <div class="section-label">Endpoints</div>
    <h2 class="section-title">Trzy rejestry, jeden interfejs</h2>
    <p class="section-desc">Wszystkie polskie publiczne bazy danych dostępne przez spójne REST API.</p>

    <div class="endpoints-grid">
      <div class="endpoint-card">
        <div class="endpoint-icon">&#127970;</div>
        <div class="endpoint-name">KRS</div>
        <div class="endpoint-full-name">Krajowy Rejestr Sądowy</div>
        <p class="endpoint-desc">Spółki, fundacje, stowarzyszenia. Zarząd, kapitał zakładowy, adres siedziby, rachunki bankowe (Biała Lista VAT).</p>
        <div class="endpoint-routes">
          <div class="route"><span class="method">GET</span>/api/krs?nip={NIP}</div>
          <div class="route"><span class="method">GET</span>/api/krs?krs={numer_krs}</div>
        </div>
      </div>

      <div class="endpoint-card">
        <div class="endpoint-icon">&#128188;</div>
        <div class="endpoint-name">CEIDG</div>
        <div class="endpoint-full-name">Centralna Ewidencja Działalności Gospodarczej</div>
        <p class="endpoint-desc">Jednoosobowe działalności gospodarcze (JDG). Status, PKD, adres, data rejestracji.</p>
        <div class="endpoint-routes">
          <div class="route"><span class="method">GET</span>/api/ceidg?nip={NIP}</div>
          <div class="route"><span class="method">GET</span>/api/ceidg?name={nazwa}</div>
        </div>
      </div>

      <div class="endpoint-card">
        <div class="endpoint-icon">&#128202;</div>
        <div class="endpoint-name">GUS BDL</div>
        <div class="endpoint-full-name">Bank Danych Lokalnych GUS</div>
        <p class="endpoint-desc">Statystyki publiczne. Bezrobocie wg województw, demografia, wynagrodzenia.</p>
        <div class="endpoint-routes">
          <div class="route"><span class="method">GET</span>/api/gus?type=unemployment</div>
          <div class="route"><span class="method">GET</span>/api/gus?type=population&amp;unit={miasto}</div>
        </div>
      </div>
    </div>
  </div>
</section>

<hr class="divider">

<!-- MCP -->
<section id="mcp">
  <div class="container">
    <div class="section-label">MCP Server</div>
    <h2 class="section-title">Integracja z Claude i Cursor</h2>
    <p class="section-desc">Dodaj jako MCP server i pytaj o dane firm wprost w czacie AI.</p>

    <div class="mcp-wrapper">
      <div class="mcp-text">
        <h3>Jak to działa?</h3>
        <p>Model Context Protocol pozwala Claude Desktop i Cursorowi wywoływać zewnętrzne narzędzia. Po instalacji możesz pisać: <em>&bdquo;Sprawdź czy Orlen jest czynnym podatnikiem VAT&rdquo;</em> &mdash; i AI sama odpyta API.</p>
        <ul class="mcp-steps">
          <li class="mcp-step">
            <span class="step-num">1</span>
            <span>Zainstaluj pakiet: <code style="font-size:0.8rem;color:var(--green);">pip install mcp-polish-data</code></span>
          </li>
          <li class="mcp-step">
            <span class="step-num">2</span>
            <span>Dodaj konfigurację do <code style="font-size:0.8rem;color:var(--green);">claude_desktop_config.json</code></span>
          </li>
          <li class="mcp-step">
            <span class="step-num">3</span>
            <span>Uruchom ponownie Claude Desktop i pytaj o dane firm</span>
          </li>
        </ul>
      </div>

      <div class="code-block">
        <div class="code-header">
          <span class="code-lang">claude_desktop_config.json</span>
          <button class="code-copy" onclick="copyCode(this, 'mcp-code')">Kopiuj</button>
        </div>
        <div class="code-body" id="mcp-code"><span class="p">{</span>
  <span class="s">"mcpServers"</span><span class="p">: {</span>
    <span class="s">"polish-data"</span><span class="p">: {</span>
      <span class="s">"command"</span><span class="p">:</span> <span class="s">"pip install mcp-polish-data &amp;&amp; mcp-polish-data"</span>
    <span class="p">}</span>
  <span class="p">}</span>
<span class="p">}</span></div>
      </div>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <p>Built with Built with &#10084;&#65039; by <a href="https://localfy.pl" target="_blank">Localfy</a>#10084;Built with &#10084;&#65039; by <a href="https://localfy.pl" target="_blank">Localfy</a>#65039; by <a href="https://emilpinski.pl" target="_blank">Emil Piński</a> &nbsp;&middot;&nbsp; Free forever &nbsp;&middot;&nbsp; Data from KRS, CEIDG, GUS &nbsp;&middot;&nbsp; <a href="https://github.com/emilpinski/mcp-polish-data" target="_blank">Open Source MIT</a></p>
</footer>

<script>
  function setNip(nip) {
    document.getElementById('nip-input').value = nip;
    searchNip();
  }

  document.getElementById('nip-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') searchNip();
  });

  async function searchNip() {
    var nip = document.getElementById('nip-input').value.trim().replace(/[\\-\\s]/g, '');
    if (!nip) return;

    var resultEl = document.getElementById('demo-result');
    resultEl.innerHTML = '<div class="result-spinner"><div class="spinner"></div><span>Pobieranie danych z KRS&hellip;</span></div>';

    try {
      var res = await fetch('/api/krs?nip=' + encodeURIComponent(nip));
      var data = await res.json();

      if (data.error || (data.count !== undefined && data.count === 0)) {
        resultEl.innerHTML = '<div class="result-error">&#10060; ' + (data.error || 'Nie znaleziono firmy dla podanego NIP.') + '</div>';
        return;
      }

      var company = data;
      if (data.results && data.results.length > 0) {
        company = data.results[0];
      }

      var name = company.name || company.nazwa || 'Nieznana nazwa';
      var nipVal = company.nip || nip;
      var krs = company.krs || company.krs_number || '—';
      var regon = company.regon || '—';
      var street = company.street || company.ulica || '';
      var city = company.city || company.miasto || '';
      var postCode = company.post_code || company.kod_pocztowy || '';
      var address = [street, postCode, city].filter(Boolean).join(', ') || '—';
      var vatStatus = company.vat_status || company.status_vat || '';
      var isActive = vatStatus && vatStatus.toLowerCase().indexOf('czyn') !== -1;

      resultEl.innerHTML =
        '<div class="result-card">' +
          '<div class="result-name">&#128203; ' + escHtml(name) + '</div>' +
          '<div class="result-row">' +
            'NIP: <span>' + escHtml(String(nipVal)) + '</span>' +
            'KRS: <span>' + escHtml(String(krs)) + '</span>' +
            'REGON: <span>' + escHtml(String(regon)) + '</span>' +
          '</div>' +
          '<div class="result-address">&#128205; ' + escHtml(address) + '</div>' +
          (vatStatus ? '<div><span class="result-vat">' + (isActive ? '&#9989;' : '&#10060;') + ' Status VAT: ' + escHtml(vatStatus) + '</span></div>' : '') +
        '</div>';
    } catch(e) {
      resultEl.innerHTML = '<div class="result-error">&#10060; Błąd połączenia: ' + escHtml(String(e.message)) + '</div>';
    }
  }

  function escHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function copyCode(btn, elId) {
    var text = document.getElementById(elId).innerText;
    navigator.clipboard.writeText(text).then(function() {
      btn.textContent = 'Skopiowano!';
      setTimeout(function() { btn.textContent = 'Kopiuj'; }, 1800);
    });
  }
</script>
</body>
</html>"""


def _json_response(handler, data: dict, status: int = 200):
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    for k, v in CORS_HEADERS.items():
        handler.send_header(k, v)
    handler.end_headers()
    handler.wfile.write(body)


def _html_response(handler, html: str):
    body = html.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default access log

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        params = urllib.parse.parse_qs(parsed.query)

        def p(key):
            vals = params.get(key, [])
            return vals[0] if vals else None

        # Landing page
        if path == "" or path == "/":
            _html_response(self, LANDING_HTML)
            return

        # /api — endpoint list
        if path == "/api":
            _json_response(self, {
                "name": "Polish Data API",
                "version": "1.0.0",
                "endpoints": [
                    {"path": "/api/krs", "params": ["nip", "krs"], "description": "KRS company registry"},
                    {"path": "/api/ceidg", "params": ["nip", "name", "regon", "surname"], "description": "CEIDG sole trader registry"},
                    {"path": "/api/gus", "params": ["type", "unit", "year"], "description": "GUS BDL statistics (type: unemployment|population)"},
                ],
                "source": "https://github.com/emilpinski/mcp-polish-data",
            })
            return

        # /api/krs
        if path == "/api/krs":
            nip = p("nip")
            krs = p("krs")
            if nip:
                result = asyncio.run(krs_search(nip=nip))
            elif krs:
                result = asyncio.run(krs_details(krs_number=krs))
            else:
                _json_response(self, {"error": "Provide ?nip= or ?krs= parameter", "status": 400}, 400)
                return
            status = 404 if "error" in result and not result.get("count") else 200
            _json_response(self, result, status)
            return

        # /api/ceidg
        if path == "/api/ceidg":
            nip = p("nip")
            name = p("name")
            regon = p("regon")
            surname = p("surname")
            if not any([nip, name, regon, surname]):
                _json_response(self, {"error": "Provide ?nip=, ?name=, ?regon= or ?surname= parameter", "status": 400}, 400)
                return
            result = asyncio.run(ceidg_search(nip=nip, name=name, regon=regon, surname=surname))
            status = 404 if "error" in result else 200
            _json_response(self, result, status)
            return

        # /api/gus
        if path == "/api/gus":
            gus_type = p("type")
            unit = p("unit")
            year_str = p("year")
            year = int(year_str) if year_str and year_str.isdigit() else 2023

            if gus_type == "unemployment":
                result = asyncio.run(get_unemployment_rate(year=year))
            elif gus_type == "population":
                result = asyncio.run(get_population(unit_name=unit, year=year))
            else:
                _json_response(self, {"error": "Provide ?type=unemployment or ?type=population", "status": 400}, 400)
                return
            status = 404 if "error" in result else 200
            _json_response(self, result, status)
            return

        # 404
        _json_response(self, {"error": "Not found", "path": path, "status": 404}, 404)
