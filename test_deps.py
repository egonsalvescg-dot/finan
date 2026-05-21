#!/usr/bin/env python3
"""Finanças — Dependências.
Stack vanilla puro: sem CDNs externos, sem package.json,
sem node_modules. Tudo é local e auto-suficiente.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent
H = (ROOT / 'index.html').read_text(encoding='utf-8')
SW = (ROOT / 'sw.js').read_text(encoding='utf-8') if (ROOT / 'sw.js').exists() else ''

results = []
def C(label, ok, ev=''):
    results.append((label, ok, ev))

# --- Sem CDN externo ---
ext_scripts = re.findall(r'<script[^>]*src="(https?://[^"]+)"', H)
C(f'Sem <script src=CDN externo> ({len(ext_scripts)})',
  len(ext_scripts) == 0, ', '.join(ext_scripts)[:200])

ext_styles = re.findall(r'<link[^>]+href="(https?://[^"]+)"[^>]*>', H)
ext_styles = [s for s in ext_styles if 'stylesheet' in H[H.find(s) - 100:H.find(s) + 200] or '.css' in s.lower()]
C(f'Sem <link rel=stylesheet href=CDN> ({len(ext_styles)})',
  len(ext_styles) == 0, ', '.join(ext_styles)[:200])

# --- Sem Google Fonts ---
C('Sem Google Fonts (fonts.googleapis.com)', 'fonts.googleapis.com' not in H, '')
C('Sem Google Fonts (fonts.gstatic.com)', 'fonts.gstatic.com' not in H, '')

# --- Sem Bootstrap, Tailwind, jQuery CDN ---
for lib in ['cdn.jsdelivr.net', 'unpkg.com', 'cdnjs.cloudflare.com', 'jquery', 'bootstrap', 'tailwindcss']:
    C(f'Sem dependência "{lib}"', lib not in H.lower(), '')

# --- Sem package.json / node_modules (vanilla puro) ---
C('Sem package.json (vanilla puro)', not (ROOT / 'package.json').exists(), '')
C('Sem package-lock.json', not (ROOT / 'package-lock.json').exists(), '')
C('Sem yarn.lock', not (ROOT / 'yarn.lock').exists(), '')
C('Sem node_modules/', not (ROOT / 'node_modules').exists(), '')

# --- SW: sem importScripts externo ---
if SW:
    C('SW: sem importScripts externo',
      not re.search(r'importScripts\s*\(\s*["\']https?://', SW), '')

# --- API Calls externas em runtime ---
fetch_calls = re.findall(r'fetch\s*\(\s*([^)]+)\)', H)
ext_fetches = []
for fc in fetch_calls:
    if 'http' in fc and 'localhost' not in fc:
        ext_fetches.append(fc[:80])
C(f'Sem fetch() pra URLs externas ({len(ext_fetches)})',
  len(ext_fetches) == 0, '; '.join(ext_fetches)[:200])

# --- XMLHttpRequest também ---
C('Sem XMLHttpRequest pra externos', not re.search(r'new\s+XMLHttpRequest', H), '')

# --- WebSocket externo ---
ws_match = re.search(r'new\s+WebSocket\s*\(\s*[\'"](?:wss?://[^\'"]+)', H)
C('Sem WebSocket externo', ws_match is None, '')

# --- Imports ES módulos externos ---
ext_imports = re.findall(r'import\s+.*from\s+[\'"]https?://', H)
C(f'Sem import ES de CDN ({len(ext_imports)})',
  len(ext_imports) == 0, '; '.join(ext_imports)[:200])

# --- Apenas SVG/PNG/ico locais ---
ext_imgs = re.findall(r'<img[^>]+src="(https?://[^"]+)"', H)
C(f'Sem <img src=CDN> ({len(ext_imgs)})',
  len(ext_imgs) == 0, '; '.join(ext_imgs)[:200])

# --- vercel.json sem dependências de build ---
vj = ROOT / 'vercel.json'
if vj.exists():
    import json
    v = json.loads(vj.read_text())
    C('vercel.json sem buildCommand (estático puro)', 'buildCommand' not in v, '')
    C('vercel.json sem framework declarado', 'framework' not in v or v.get('framework') in (None, ''), '')

# --- _redirects e netlify.toml (são opcionais, manter consistente) ---
# Não bloqueante

# --- Reporta ---
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n[Dependências] {passed}/{total}")
fails = [(l, e) for (l, ok, e) in results if not ok]
for l, e in fails:
    print(f"  ✗ {l}" + (f" → {e}" if e else ""))
sys.exit(0 if passed == total else 1)
