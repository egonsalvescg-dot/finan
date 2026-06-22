# CLAUDE.md

Guidance for AI assistants (and humans) working in this repository.

## What this is

**Finanças** is a personal finance / net-worth ("patrimônio") tracker built as a
single-file, offline-first **PWA**. The entire application — HTML, CSS, and
JavaScript — lives in **`index.html`**. There is no build step, no framework,
no package manager, and no external runtime dependencies. The app is "vanilla
puro" and that constraint is enforced by the test suite (see below).

The UI and all code comments / commit messages are written in **Brazilian
Portuguese (pt-BR)**. Match that language when editing app strings, comments,
and commits.

### Core principles (do not break these)

1. **Zero external dependencies at runtime.** No CDNs, no Google Fonts, no
   `package.json`, no `node_modules`, no external `fetch`/WebSocket/import.
   Everything ships in-repo and works fully offline.
2. **All data is local.** State persists to `localStorage` only. There is no
   backend, no server, no account sync. The user owns their data (export/import
   is JSON).
3. **Money math always goes through `round2()`** to avoid floating-point drift.
4. **All user-supplied strings rendered into HTML must pass through `esc()`.**
5. **Dates use local timezone** (never UTC `toISOString()` for date keys).

## File layout

| Path | Purpose |
|------|---------|
| `index.html` | The entire app — single `<style>` block + single `<script>` block (~3.5k lines). |
| `sw.js` | Service Worker. Network-first for HTML (so deploys land), cache-first for assets. Cache name is **versioned** (`financas-vN`) — bump it when assets change. |
| `manifest.json` | PWA manifest (standalone, portrait, dark theme). |
| `icon.svg` | App icon (also `apple-touch-icon`). |
| `_redirects` / `netlify.toml` / `vercel.json` | Static-host config (SPA fallback + cache headers). Deploys to Netlify/Vercel as a static site, `publish = "."`. |
| `run_tests.py` | Test orchestrator — runs all suites, prints consolidated report. |
| `qa_check.py` | Structural invariants suite. |
| `flow_tests.py`, `test_*.py` | Individual static-analysis suites (see Testing). |
| `.githooks/pre-commit` | Runs `run_tests.py` before each commit; aborts on failure. |

## Architecture of `index.html`

It is one file but mentally divided into sections (search for the banner
comments like `HELPERS`, `CÁLCULOS`):

- **Config / keys** — `DB_KEY = 'financas:db:v1'`, `PIN_KEY = 'financas:pin:v1'`,
  `DEFAULT_CATEGORIAS`.
- **Persistence** — `loadDB()` / `saveDB()`. `saveDB` is wrapped in try/catch and
  handles `QuotaExceededError` gracefully. `loadDB` defensively normalizes every
  array field. A `storage` event listener syncs state across tabs.
- **Helpers** — `esc`, `round2`, `pad2`, `fmtBRL`, `parseValor`, `fmtData`,
  `mesIso`, `hoje`, `nomeMes`, `navMes`, `uid`, `toast`, `confirmDialog`.
- **Calculations** — `saldoConta`, `valorBem`, `totaisDoMes`,
  `gastosPorCategoria`, `runAutoCreate` (materializes recurring entries).
- **Views / render** — `currentView` holds one of `inicio | lancamentos |
  contas | bens`; `setView()` switches and `render()` dispatches to the matching
  `renderX()`. Bottom-nav buttons use `data-view`.
- **Modals** — declared as `.modal-backdrop` blocks in markup; opened/closed via
  `openModal` / `closeModal`. Confirmation uses custom `confirmDialog()` (never
  native `confirm()`/`alert()` for flow control).
- **PIN lock** — optional app PIN. Stored as a **salted SHA-256 hash** via
  `crypto.subtle` (`hashPin`, `pinSalt`, `CRYPTO_OK` guard — requires HTTPS).
  Never store the PIN in plain text.
- **Boot** — registers `sw.js`, installs `error` / `unhandledrejection` handlers.

### Data model (`DB` in localStorage)

```
{
  version: 1,
  contas:       [{ id, nome, tipo, saldoInicial, cor, criadoEm, arquivada? }],
  bens:         [{ id, nome, tipo, valorInicial, cor, criadoEm, arquivada? }],
  categorias:   [{ id, nome, tipo:'receita'|'despesa', cor }],
  lancamentos:  [ ...see below ],
  recorrencias: [{ id, nome, valor, diaVencimento, contaId, categoriaId,
                   bemId, tipo, ativa, autoCreate }]
}
```

A **lançamento** (transaction) has `tipo` of `receita | despesa | transferencia
| investimento`, plus `id, valor, data (YYYY-MM-DD), descricao, criadoEm`, and
type-specific fields:
- `receita`/`despesa`: `contaId`, `categoriaId` (despesa may have `bemId` link)
- `transferencia`: `contaOrigemId`, `contaDestinoId`
- `investimento`: `contaOrigemId`, `bemId`

When editing, the original object is spread (`...(original || {})`) so unknown
fields survive, and orphan fields are deleted if `tipo` changes. Preserve this
behavior. Recurring-entry materialization (`runAutoCreate` / "pagar fixa") must
stay **idempotent** — keyed on `recorrenciaId` + month.

## Development workflow

There is no build and no server requirement, but the Service Worker and
`crypto.subtle` (PIN) need an `http://`/`https://` origin — don't open via
`file://`.

```bash
# Serve locally (any static server works):
python3 -m http.server 8000        # then open http://localhost:8000
```

Edit `index.html` directly. After changing cached assets, **bump the SW cache
version** in `sw.js` (`financas-vN`).

### Testing — run before every commit

All tests are **static analysis** (regex/structure checks over the source) —
they run in well under a second and need only Python 3, no dependencies.

```bash
python3 run_tests.py          # full consolidated suite (must be 100% green)
python3 qa_check.py           # or run any single suite directly
```

Suites (all must pass — currently **523/523**):

| Suite | Checks |
|-------|--------|
| `qa_check.py` | Structural invariants: central functions exist, `round2` usage, `parseValor` robustness, local timezone, no `eval`, PIN hashing, PWA basics. |
| `flow_tests.py` | End-to-end critical flows: function exists + error handling + persistence + re-render + feedback. |
| `test_syntax.py` | Valid HTML5, parseable JSON, balanced JS braces, unique HTML IDs. |
| `test_security.py` | XSS / `esc()` usage, no secrets, no `eval`/`new Function`, safe `target=_blank`, PIN-as-hash. |
| `test_a11y.py` | ARIA, labels, touch targets ≥44px, input `font-size ≥16px` (anti iOS zoom). |
| `test_visual.py` | Z-index hierarchy, CSS tokens, responsive viewport, safe-area, animations. |
| `test_performance.py` | Bundle size, function count, render complexity, listener cleanup. |
| `test_data.py` | localStorage key consistency, referenced HTML IDs exist, `onclick` handlers defined, data models complete. |
| `test_pwa.py` | Manifest fields/icons, SW registration + handlers + versioning, offline detection. |
| `test_deps.py` | No external CDN/fonts/imports/fetch, no `package.json`/`node_modules`. |

When you add a feature, the suites will often need a corresponding new
invariant — extend the relevant `test_*.py` rather than weakening it.

### Git hooks

The repo ships a pre-commit hook at `.githooks/pre-commit` that runs the full
suite. It is **not active until installed**:

```bash
git config core.hooksPath .githooks
```

The hook skips tests when a commit touches no runtime files, and runs the full
suite otherwise. Bypass (discouraged) with `git commit --no-verify`.

## Conventions

- **Language:** pt-BR for UI strings, comments, and commit messages.
- **Commit style:** Conventional-commit prefixes in Portuguese context, e.g.
  `feat: ...`, `fix: ...`, `test: ...`. Often grouped as waves/phases
  ("Onda 3", "5.4 — orçamento por categoria"). Keep messages descriptive.
- **CSS:** Design tokens via CSS custom properties on `:root` (`--space-*`,
  `--font-*`, `--radius-*`, semantic colors, `--touch-min: 44px`). Respect the
  8px spacing grid and iOS safe-area insets (`env(safe-area-inset-*)`).
- **No native dialogs for flow control** — use `toast()` and `confirmDialog()`.
- **Always** `esc()` interpolated user data and `round2()` money math.
- **IDs** in markup must be unique (enforced by `test_syntax.py`) and every ID
  referenced from JS must exist (enforced by `test_data.py`).

## When making changes — checklist

1. Edit `index.html` (keep single `<style>` / single `<script>`).
2. Preserve the core principles above (offline, no deps, `round2`, `esc`, local
   dates, PIN hashing).
3. If assets/markup changed, bump `sw.js` cache version.
4. Add/extend the relevant `test_*.py` invariant for new behavior.
5. Run `python3 run_tests.py` — it must be 100% green.
6. Commit in pt-BR with a `feat:`/`fix:`/`test:` prefix.
