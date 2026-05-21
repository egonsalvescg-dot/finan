#!/usr/bin/env python3
"""Finanças — Performance e complexidade.
Tamanho do bundle, número de funções, complexidade de render,
listeners não limpos, queries pesadas, animações.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent
H = (ROOT / 'index.html').read_text(encoding='utf-8')
SW = (ROOT / 'sw.js').read_text(encoding='utf-8') if (ROOT / 'sw.js').exists() else ''

results = []
def C(label, ok, ev=''):
    results.append((label, ok, ev))

# --- Tamanho ---
size = (ROOT / 'index.html').stat().st_size
C(f'index.html < 500 KB ({size//1024} KB)', size < 500_000, f'{size} bytes')
C(f'index.html < 1 MB hard limit ({size//1024} KB)', size < 1_000_000, f'{size} bytes')

# --- Scripts externos ---
ext_scripts = re.findall(r'<script[^>]*src="([^"]+)"', H)
ext_scripts = [s for s in ext_scripts if not s.startswith('sw.js') and not s.startswith('./') and not s.startswith('/')]
C(f'Scripts externos ≤5 ({len(ext_scripts)})', len(ext_scripts) <= 5, '')

# --- Funções ---
fn_decls = re.findall(r'\bfunction\s+(\w+)\s*\(', H)
arrow_assigns = re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', H)
total_fns = len(set(fn_decls)) + len(set(arrow_assigns))
C(f'Funções entre 30 e 200 ({total_fns})', 30 <= total_fns <= 200, str(total_fns))

# --- Funções gigantes (> 5000 chars no corpo) ---
# Heurística: extrair função por função e contar corpo
def extract_function_bodies(code):
    """Retorna {nome: body} para function decls."""
    bodies = {}
    for m in re.finditer(r'function\s+(\w+)\s*\([^)]*\)\s*\{', code):
        name = m.group(1)
        start = m.end()
        depth = 1
        i = start
        while i < len(code) and depth > 0:
            c = code[i]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            i += 1
        bodies[name] = code[start:i-1]
    return bodies

bodies = extract_function_bodies(H)
big_fns = [(n, len(b)) for n, b in bodies.items() if len(b) > 5000]
C(f'Funções gigantes (>5000 chars): ≤7 ({len(big_fns)})', len(big_fns) <= 7, ', '.join(f'{n}({sz})' for n, sz in big_fns)[:200])

# --- Renders / scheduleRender ---
render_calls = H.count('render()') + H.count('renderInicio()') + H.count('renderLancamentos()') + H.count('renderContas()') + H.count('renderBens()') + H.count('renderListaFixas()')
C(f'render() chamadas ≤60 ({render_calls})', render_calls <= 60, str(render_calls))

# --- innerHTML usos ---
ih = len(re.findall(r'\.innerHTML\s*[=+]', H))
C(f'innerHTML usos ≤100 ({ih})', ih <= 100, str(ih))

# --- @keyframes ---
kf = len(re.findall(r'@keyframes\s+\w+', H))
C(f'@keyframes ≤15 ({kf})', kf <= 15, str(kf))

# --- document.addEventListener (listeners não limpos = memory leak) ---
doc_listeners = len(re.findall(r'document\.addEventListener', H))
C(f'document.addEventListener ≤15 ({doc_listeners})', doc_listeners <= 15, str(doc_listeners))

# --- window.addEventListener ---
win_listeners = len(re.findall(r'window\.addEventListener', H))
C(f'window.addEventListener ≤10 ({win_listeners})', win_listeners <= 10, str(win_listeners))

# --- setInterval com clearInterval ---
si = len(re.findall(r'setInterval\s*\(', H))
ci = len(re.findall(r'clearInterval\s*\(', H))
C(f'setInterval pareado com clearInterval ({si} si / {ci} ci)', si == 0 or ci >= si, '')

# --- setTimeout sem ID (não-cancelável vs com ID) ---
# Aceitar — setTimeout sem ID é OK pra animações curtas
st_count = len(re.findall(r'setTimeout\s*\(', H))
C(f'setTimeout usos ≤30 (heurística) ({st_count})', st_count <= 30, str(st_count))

# --- localStorage chamadas ---
ls_set = len(re.findall(r'localStorage\.setItem', H))
C(f'localStorage.setItem ≤30 ({ls_set})', ls_set <= 30, str(ls_set))

# --- Cache no SW ---
if SW:
    C('SW versionado (cache-name com versão)', re.search(r"financas-v\d", SW) is not None, '')

# --- Loops gigantes (mais que 100 iterações esperadas) ---
# Conta MAX_MESES_RETROAGIR e similares
backfill_limit = re.search(r'MAX_MESES_RETROAGIR\s*=\s*(\d+)', H)
if backfill_limit:
    n = int(backfill_limit.group(1))
    C(f'AutoCreate retroage no máximo {n} meses (≤12)', n <= 12, '')

# --- Memory leak: variáveis de timer globais ---
# _toastTimer, lockCompleteTimer existem
timer_vars_ok = '_toastTimer' in H or 'lockCompleteTimer' in H or 'clearTimeout' in H
C('Timers cancelados com clearTimeout', 'clearTimeout' in H, '')

# --- Inputs com input event (debounce não usado mas tudo bem em app pequeno) ---
# Não bloqueante

# --- CSS: seletor universal abusado ---
star_sel = len(re.findall(r'(?:^|\W)\*\s*\{', H))
C(f'CSS: ≤2 usos de seletor universal *{{ ({star_sel})', star_sel <= 2, str(star_sel))

# --- Imagens grandes embutidas como data: ---
data_imgs = re.findall(r'data:image/[^;]+;base64,([^"\')\s]{500,})', H)
C(f'Sem imagens base64 grandes (>500 chars) ({len(data_imgs)})', len(data_imgs) == 0, '')

# --- Cálculos pesados: saldoConta deve usar round2 (já no qa_check mas relevante perf) ---
# Saldos chamados em loops devem ser O(n) onde n é número de lançamentos
# Heurística: saldoConta itera DB.lancamentos uma vez
sc_block = bodies.get('saldoConta', '')
C('saldoConta itera DB.lancamentos uma vez', 'for (const l of DB.lancamentos)' in sc_block, '')

# --- Render: NÃO faz fetch de rede (offline-first) ---
fetch_in_render = False
for fn_name in ['renderInicio', 'renderLancamentos', 'renderContas', 'renderBens']:
    if 'fetch(' in bodies.get(fn_name, ''):
        fetch_in_render = True
        break
C('Funções de render não chamam fetch() (offline-first)', not fetch_in_render, '')

# --- Reporta ---
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n[Performance] {passed}/{total}")
fails = [(l, e) for (l, ok, e) in results if not ok]
for l, e in fails:
    print(f"  ✗ {l}" + (f" → {e}" if e else ""))
sys.exit(0 if passed == total else 1)
