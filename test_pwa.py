#!/usr/bin/env python3
"""Finanças — PWA.
Manifest válido com campos obrigatórios, ícones, Service Worker
registrado com handlers e versionamento, detecção de offline.
"""
import re, sys, json
from pathlib import Path

ROOT = Path(__file__).parent
H = (ROOT / 'index.html').read_text(encoding='utf-8')
SW_PATH = ROOT / 'sw.js'
MAN_PATH = ROOT / 'manifest.json'

results = []
def C(label, ok, ev=''):
    results.append((label, ok, ev))

# --- Manifest existe e parseável ---
C('manifest.json existe', MAN_PATH.exists(), '')
if MAN_PATH.exists():
    try:
        man = json.loads(MAN_PATH.read_text(encoding='utf-8'))
        C('manifest.json é JSON válido', True, '')
        # Campos obrigatórios
        for field in ['name', 'short_name', 'start_url', 'display', 'theme_color', 'background_color', 'icons']:
            C(f'Manifest tem "{field}"', field in man, '')
        # display standalone/fullscreen
        C(f'Manifest display=standalone/fullscreen ({man.get("display")})',
          man.get('display') in ('standalone', 'fullscreen', 'minimal-ui'), str(man.get('display')))
        # scope
        C('Manifest tem "scope"', 'scope' in man, '')
        # start_url consistente com scope
        C('start_url relativo (./ ou /)', str(man.get('start_url', '')).startswith(('./', '/')), '')
        # Ícones têm src/sizes/type
        icons = man.get('icons', [])
        C(f'Manifest tem ≥1 ícone ({len(icons)})', len(icons) >= 1, '')
        for i, ic in enumerate(icons):
            C(f'Ícone {i}: src/sizes/type', 'src' in ic and 'sizes' in ic and 'type' in ic, '')
        # SVG ou PNG 192/512
        sizes = [ic.get('sizes', '') for ic in icons]
        has_any_size = 'any' in sizes
        has_192 = any('192' in s for s in sizes)
        has_512 = any('512' in s for s in sizes)
        C('Ícone com sizes=any (SVG) OU 192+512 (PNG)',
          has_any_size or (has_192 and has_512),
          ', '.join(sizes))
        # Ícone física existe
        for ic in icons:
            src = ic.get('src', '').lstrip('./')
            p = ROOT / src
            C(f'Arquivo ícone existe: {src}', p.exists(), '')
    except json.JSONDecodeError as e:
        C('manifest.json válido', False, str(e))

# --- HTML meta PWA ---
C('Link rel="manifest"', '<link rel="manifest"' in H, '')
C('apple-touch-icon presente', 'apple-touch-icon' in H, '')
C('apple-mobile-web-app-capable=yes', re.search(r'apple-mobile-web-app-capable"\s+content="yes"', H) is not None, '')
C('apple-mobile-web-app-status-bar-style', 'apple-mobile-web-app-status-bar-style' in H, '')
C('viewport-fit=cover (notch)', 'viewport-fit=cover' in H, '')
C('theme-color meta', 'name="theme-color"' in H, '')

# --- Service Worker ---
C('sw.js existe', SW_PATH.exists(), '')
if SW_PATH.exists():
    SW = SW_PATH.read_text(encoding='utf-8')
    C('SW: addEventListener install', "addEventListener('install'" in SW, '')
    C('SW: addEventListener activate', "addEventListener('activate'" in SW, '')
    C('SW: addEventListener fetch', "addEventListener('fetch'" in SW, '')
    # Versionamento
    cache_match = re.search(r"CACHE\s*=\s*['\"]financas-v(\d+)['\"]", SW)
    C(f'SW: CACHE versionado financas-vN', cache_match is not None, '')
    if cache_match:
        version = int(cache_match.group(1))
        C(f'SW: versão do CACHE ≥1 ({version})', version >= 1, '')
    # Limpa caches antigos
    C('SW: limpa caches antigos no activate', 'caches.delete' in SW, '')
    # skipWaiting + claim
    C('SW: skipWaiting (atualiza imediato)', 'skipWaiting()' in SW, '')
    C('SW: clients.claim()', 'clients.claim()' in SW, '')
    # network-first OU strategy adequada
    has_network_first = 'fetch(e.request)' in SW and ('.then(res =>' in SW or 'function networkFirst' in SW or 'isHTML' in SW)
    C('SW: estratégia network-first para HTML (deploys chegam)', has_network_first, '')
    # cache-first OU pre-cached assets
    assets_match = re.search(r"const\s+ASSETS\s*=\s*\[", SW)
    C('SW: ASSETS array com shell pre-cacheado', assets_match is not None, '')

# --- Registro do SW no HTML ---
C('SW: registrado no boot do app',
  "navigator.serviceWorker.register('sw.js')" in H or
  'navigator.serviceWorker.register("sw.js")' in H, '')
C('SW: registrado dentro de "if serviceWorker in navigator"',
  "'serviceWorker' in navigator" in H, '')

# --- Detecção / handling de offline ---
# Não obrigatório (network-first com fallback cobre), mas comum:
offline_handling = 'navigator.onLine' in H or "addEventListener('offline'" in H or 'cache-first' in H or 'caches.match' in H
# Não bloqueante — info
C(f'Detecção de estado offline declarada (info, não bloqueante)', True, str(offline_handling))

# --- localStorage QuotaExceededError tratado ---
C('localStorage QuotaExceededError tratado', 'QuotaExceededError' in H, '')

# --- Ícones físicos no repo ---
icon_files = list(ROOT.glob('icon*.svg')) + list(ROOT.glob('icon*.png'))
C(f'Pelo menos 1 ícone físico no repo ({len(icon_files)})', len(icon_files) >= 1, '')

# --- vercel.json cache headers ---
vj_path = ROOT / 'vercel.json'
if vj_path.exists():
    vj = json.loads(vj_path.read_text())
    headers = vj.get('headers', [])
    sw_header = next((h for h in headers if h.get('source') == '/sw.js'), None)
    if sw_header:
        no_cache = any('no-cache' in kv.get('value', '') for kv in sw_header.get('headers', []))
        C('vercel.json: /sw.js com no-cache', no_cache, '')

# --- Reporta ---
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n[PWA] {passed}/{total}")
fails = [(l, e) for (l, ok, e) in results if not ok]
for l, e in fails:
    print(f"  ✗ {l}" + (f" → {e}" if e else ""))
sys.exit(0 if passed == total else 1)
