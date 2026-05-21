#!/usr/bin/env python3
"""Finanças — Sintaxe e estrutura.
HTML5 válido, JSON parseável, balanceamento de chaves JS,
IDs HTML únicos, Service Worker com handlers.
"""
import re, sys, json
from pathlib import Path

ROOT = Path(__file__).parent
H = (ROOT / 'index.html').read_text(encoding='utf-8')
SW = (ROOT / 'sw.js').read_text(encoding='utf-8') if (ROOT / 'sw.js').exists() else ''

results = []
def C(label, ok, ev=''):
    results.append((label, ok, ev))

# --- HTML meta ---
C('Doctype HTML5', H.lstrip().lower().startswith('<!doctype html>'), '')
C('lang="pt-BR"', '<html lang="pt-BR">' in H, '')
C('charset UTF-8', 'charset="UTF-8"' in H or 'charset=utf-8' in H, '')
C('viewport meta', '<meta name="viewport"' in H, '')
C('viewport sem maximum-scale > 1 com user-scalable=no', 'user-scalable=no' not in H, '')
C('<title>', re.search(r'<title>\s*\S', H) is not None, '')
C('theme-color', 'name="theme-color"' in H, '')
C('manifest link', 'rel="manifest"' in H, '')
C('apple-touch-icon', 'apple-touch-icon' in H, '')

# --- HTML balanceamento ---
def count_tag(tag):
    open_c = len(re.findall(rf'<{tag}(?:\s[^>]*)?>', H, re.IGNORECASE))
    close_c = H.lower().count(f'</{tag}>')
    return open_c, close_c

for tag in ['html', 'head', 'body', 'style', 'script', 'nav', 'select', 'datalist']:
    o, c = count_tag(tag)
    C(f'<{tag}> balanceado ({o}={c})', o == c, f'{o}/{c}')

# div, button, input não são pareados via tag count limpa por causa de auto-closing — skip

# --- HTML IDs únicos ---
ids = re.findall(r'\bid="([^"]+)"', H)
# Filtra IDs dinâmicos com ${...}
ids_static = [i for i in ids if '${' not in i]
dups = [i for i in ids_static if ids_static.count(i) > 1]
C(f'IDs HTML únicos ({len(set(dups))} duplicados)', len(dups) == 0, ', '.join(sorted(set(dups)))[:200])

# --- JS: extrai todos os blocos <script> (sem src) ---
scripts = re.findall(r'<script>([\s\S]*?)</script>', H)
js_code = '\n'.join(scripts)
C('Bloco <script> presente', len(scripts) >= 1, str(len(scripts)))

# --- JS: stripping de strings, template, comentários, regex ---
def strip_js(code):
    """Remove strings, template literals, comentários e regex literais."""
    out = []
    i = 0
    n = len(code)
    while i < n:
        ch = code[i]
        # Comentário de linha
        if ch == '/' and i + 1 < n and code[i + 1] == '/':
            while i < n and code[i] != '\n':
                i += 1
            continue
        # Comentário de bloco
        if ch == '/' and i + 1 < n and code[i + 1] == '*':
            i += 2
            while i + 1 < n and not (code[i] == '*' and code[i + 1] == '/'):
                i += 1
            i += 2
            continue
        # String simples
        if ch in ('"', "'"):
            quote = ch
            out.append(ch)
            i += 1
            while i < n and code[i] != quote:
                if code[i] == '\\' and i + 1 < n:
                    i += 2
                    continue
                i += 1
            out.append(quote)
            i += 1
            continue
        # Template literal
        if ch == '`':
            out.append('`')
            i += 1
            depth = 0
            while i < n:
                if code[i] == '\\' and i + 1 < n:
                    i += 2
                    continue
                if code[i] == '$' and i + 1 < n and code[i + 1] == '{':
                    depth += 1
                    out.append('${')
                    i += 2
                    continue
                if code[i] == '}' and depth > 0:
                    depth -= 1
                    out.append('}')
                    i += 1
                    continue
                if code[i] == '`' and depth == 0:
                    out.append('`')
                    i += 1
                    break
                if depth > 0:
                    out.append(code[i])  # preserva expressão dentro de ${...}
                i += 1
            continue
        # Regex literal: / após token "fork" — heurística
        if ch == '/':
            # Antes precisa ter operador/keyword (não termo)
            prev = ''
            j = len(out) - 1
            while j >= 0 and out[j] in ' \t\n':
                j -= 1
            if j >= 0:
                prev = out[j]
            if prev in '=(,;!&|?:[{}+-*<>~^%':
                # parece ser regex
                out.append('/')
                i += 1
                in_class = False
                while i < n:
                    if code[i] == '\\' and i + 1 < n:
                        i += 2
                        continue
                    if code[i] == '[':
                        in_class = True
                    elif code[i] == ']':
                        in_class = False
                    elif code[i] == '/' and not in_class:
                        out.append('/')
                        i += 1
                        # flags
                        while i < n and code[i].isalpha():
                            i += 1
                        break
                    elif code[i] == '\n':
                        # regex não cruza linha — provavelmente era divisão
                        break
                    i += 1
                continue
        out.append(ch)
        i += 1
    return ''.join(out)

js_clean = strip_js(js_code)

# Balanceamento
def count_unbal(code, ch_open, ch_close):
    op = code.count(ch_open)
    cl = code.count(ch_close)
    return op, cl

bo, bc = count_unbal(js_clean, '{', '}')
po, pc = count_unbal(js_clean, '(', ')')
ko, kc = count_unbal(js_clean, '[', ']')
C(f'JS chaves {{}} balanceadas ({bo}={bc})', bo == bc, f'{bo}/{bc}')
C(f'JS parênteses () balanceados ({po}={pc})', po == pc, f'{po}/{pc}')
C(f'JS colchetes [] balanceados ({ko}={kc})', ko == kc, f'{ko}/{kc}')

# --- JSON validações ---
for jf in ['manifest.json', 'vercel.json']:
    p = ROOT / jf
    if p.exists():
        try:
            json.loads(p.read_text(encoding='utf-8'))
            C(f'{jf} é JSON válido', True, '')
        except Exception as e:
            C(f'{jf} é JSON válido', False, str(e)[:100])

# --- Encoding ---
try:
    H.encode('utf-8')
    C('index.html é UTF-8 limpo', True, '')
except Exception as e:
    C('index.html é UTF-8 limpo', False, str(e))

# --- Service Worker ---
if SW:
    C('SW: install handler', "addEventListener('install'" in SW, '')
    C('SW: activate handler', "addEventListener('activate'" in SW, '')
    C('SW: fetch handler', "addEventListener('fetch'" in SW, '')
    C('SW: CACHE constant', re.search(r"const\s+CACHE\s*=", SW) is not None, '')
    C('SW: skipWaiting (atualiza rápido)', 'skipWaiting()' in SW, '')
    C('SW: clients.claim (controla abas existentes)', 'clients.claim()' in SW, '')

# --- vercel.json ---
vj = ROOT / 'vercel.json'
if vj.exists():
    vj_content = json.loads(vj.read_text())
    headers = vj_content.get('headers', [])
    sw_no_cache = any(
        h.get('source') == '/sw.js' and any('no-cache' in kv.get('value', '') for kv in h.get('headers', []))
        for h in headers
    )
    C('vercel.json: /sw.js com no-cache', sw_no_cache, '')

# --- Reporta ---
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n[Sintaxe] {passed}/{total}")
fails = [(l, e) for (l, ok, e) in results if not ok]
for l, e in fails:
    print(f"  ✗ {l}" + (f" → {e}" if e else ""))
sys.exit(0 if passed == total else 1)
