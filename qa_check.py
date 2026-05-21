#!/usr/bin/env python3
"""Finanças — Checks estruturais fundamentais.
Regras invioláveis: funções centrais existem, cálculos com round2,
parseValor robusto, timezone local, sem eval, secrets nem dependências externas.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent
H = (ROOT / 'index.html').read_text(encoding='utf-8')
SW = (ROOT / 'sw.js').read_text(encoding='utf-8') if (ROOT / 'sw.js').exists() else ''
MAN = (ROOT / 'manifest.json').read_text(encoding='utf-8') if (ROOT / 'manifest.json').exists() else ''

results = []
def C(label, ok, ev=''):
    results.append((label, ok, ev))

# --- Funções centrais ---
FUNCS_CENTRAIS = [
    'loadDB', 'saveDB', 'round2', 'parseValor', 'fmtBRL', 'mesIso', 'hoje',
    'saldoConta', 'valorBem', 'totaisDoMes', 'gastosPorCategoria',
    'render', 'renderInicio', 'renderSaldoDestaque', 'renderPatrimonioMini',
    'renderProximosCompromissos', 'renderGraficoPatrimonio',
    'openModal', 'closeModal', 'confirmDialog', 'toast', 'esc', 'uid',
    'runAutoCreate', 'recorrenciaPaga', 'hashPin', 'showLock', 'hideLock'
]
for fn in FUNCS_CENTRAIS:
    C(f'Função existe: {fn}', f'function {fn}' in H or f'{fn} = ' in H or f'{fn} =' in H, '')

# --- Regras invioláveis ---
C('round2 aplicado em saldoConta', 'return round2(s)' in H, '')
C('round2 aplicado em valorBem', 'return round2(v)' in H, '')
C('round2 aplicado em totalInvestidoBem', 'return round2(t)' in H, '')
C('parseValor robusto (Number.isFinite)', 'Number.isFinite' in H, '')
C('parseValor aplica Math.abs', 'Math.abs(n)' in H, '')
C('mesIso usa timezone local (getMonth)', "d.getMonth() + 1" in H, '')
C('hoje() usa timezone local', "d.getDate()" in H and 'function hoje' in H, '')
C('Helper pad2 existe', 'function pad2' in H, '')

# --- Segurança fundamental ---
C('Sem eval()', not re.search(r'(^|\W)eval\s*\(', H), '')
C('Sem new Function(', 'new Function(' not in H, '')
C('Sem service_role key', 'service_role' not in H, '')
C('Sem chave PIN em texto plano', "localStorage.setItem(PIN_KEY, '" not in H, '')
C('PIN armazenado como hash', "localStorage.setItem(PIN_KEY, hash)" in H, '')
C('PIN tem salt aleatório', "function pinSalt" in H, '')
C('CRYPTO_OK guard existe', "CRYPTO_OK" in H, '')

# --- Persistência ---
C('saveDB com try/catch', 'function saveDB' in H and 'catch (e)' in H[H.find('function saveDB'):H.find('function saveDB')+500], '')
C('saveDB detecta QuotaExceededError', 'QuotaExceededError' in H, '')
C('loadDB com fallback de DEFAULT_CATEGORIAS', 'DEFAULT_CATEGORIAS' in H, '')
C('Versão do DB armazenada', 'version: 1' in H or 'version:1' in H, '')

# --- Sync entre abas ---
C('Listener de storage event', "addEventListener('storage'" in H, '')

# --- Error boundaries ---
C("Handler de window.error", "addEventListener('error'" in H, '')
C("Handler de unhandledrejection", "unhandledrejection" in H, '')

# --- PWA básico ---
C('Service Worker registrado', "navigator.serviceWorker.register('sw.js')" in H, '')
C('Manifest linkado', '<link rel="manifest"' in H, '')
C('viewport-fit=cover (notch iOS)', 'viewport-fit=cover' in H, '')
C('apple-mobile-web-app-capable', 'apple-mobile-web-app-capable' in H, '')

# --- Service Worker ---
if SW:
    C('SW: handler install', "addEventListener('install'" in SW, '')
    C('SW: handler activate', "addEventListener('activate'" in SW, '')
    C('SW: handler fetch', "addEventListener('fetch'" in SW, '')
    C('SW: CACHE versionado', re.search(r"CACHE\s*=\s*['\"]financas-v\d+", SW) is not None, '')
    C('SW: network-first para HTML (deploy chega)', 'fetch(e.request)' in SW and 'isHTML' in SW, '')

# --- Manifest ---
if MAN:
    import json
    try:
        m = json.loads(MAN)
        C('Manifest: name', 'name' in m, '')
        C('Manifest: short_name', 'short_name' in m, '')
        C('Manifest: start_url', 'start_url' in m, '')
        C('Manifest: display standalone', m.get('display') == 'standalone', m.get('display', ''))
        C('Manifest: theme_color', 'theme_color' in m, '')
        C('Manifest: icons', isinstance(m.get('icons'), list) and len(m['icons']) > 0, '')
        C('Manifest: scope', 'scope' in m, '')
    except Exception as e:
        C('Manifest válido JSON', False, str(e))

# --- Render preservation ---
C('Edit lançamento preserva campos extras (spread)', '...(original || {})' in H, '')
C('Pagar fixa idempotente (atualiza se já pago)', "DB.lancamentos.find(l =>\n    l.recorrenciaId === r.id" in H, '')

# --- Sanitização ---
C("Helper esc() definido", 'function esc(' in H, '')
total_esc = H.count('esc(')
C(f'esc() usado ≥ 30 vezes (encontrei {total_esc})', total_esc >= 30, str(total_esc))

# --- Sem dependências externas ---
C('Sem CDN externo no HTML', not re.search(r'<script[^>]*src=["\']https?://(?!localhost)', H), '')
C('Sem fontes externas (Google Fonts etc)', 'fonts.googleapis.com' not in H and 'fonts.gstatic.com' not in H, '')
C('Sem package.json (vanilla puro)', not (ROOT / 'package.json').exists(), '')
C('Sem node_modules (vanilla puro)', not (ROOT / 'node_modules').exists(), '')

# --- Touch targets / mobile ---
C('Token --touch-min: 44px', '--touch-min: 44px' in H, '')
C('Safe-area no header', 'env(safe-area-inset-top)' in H, '')
C('Safe-area no bottom-nav', 'env(safe-area-inset-bottom)' in H and '.bottom-nav' in H, '')
C('Input font-size ≥16px (anti-zoom iOS)', 'font-size: 16px;' in H or 'font-size:16px' in H, '')

# --- Reporta ---
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n[Estrutural] {passed}/{total}")
fails = [(l, e) for (l, ok, e) in results if not ok]
for l, e in fails:
    print(f"  ✗ {l}" + (f" → {e}" if e else ""))
sys.exit(0 if passed == total else 1)
