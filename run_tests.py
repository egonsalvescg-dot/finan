#!/usr/bin/env python3
"""Finanças — Orquestrador de testes estáticos.
Roda todas as suítes e imprime relatório consolidado.
Retorna exit 0 se tudo verde, 1 se alguma suíte falhar.
"""
import subprocess, sys, re, time
from pathlib import Path

ROOT = Path(__file__).parent

SUITES = [
    ('Estrutural (qa_check)',  'qa_check.py'),
    ('Fluxos (flow_tests)',    'flow_tests.py'),
    ('Sintaxe',                'test_syntax.py'),
    ('Segurança',              'test_security.py'),
    ('Acessibilidade',         'test_a11y.py'),
    ('Visual / Layout',        'test_visual.py'),
    ('Performance',            'test_performance.py'),
    ('Integridade de dados',   'test_data.py'),
    ('PWA',                    'test_pwa.py'),
    ('Dependências',           'test_deps.py'),
]

print("\n" + "═" * 72)
print("  SUÍTE COMPLETA DE TESTES — Finanças")
print("═" * 72)

results = []
t_total = time.time()
for name, script in SUITES:
    t = time.time()
    try:
        out = subprocess.run(
            ['python3', str(ROOT / script)],
            capture_output=True, text=True, timeout=60
        )
        elapsed = time.time() - t
        score_m = re.search(r'(\d+)/(\d+)', out.stdout)
        if score_m:
            passed, total = int(score_m.group(1)), int(score_m.group(2))
        else:
            passed, total = 0, 0
        status = '✓' if out.returncode == 0 else '✗'
        results.append((name, status, passed, total, elapsed, out.stdout))
    except Exception as e:
        results.append((name, '!', 0, 0, 0, str(e)))

t_total = time.time() - t_total

print(f"\n{'Suíte':<26} {'Status':<8} {'Score':<12} {'Tempo':<8}")
print("─" * 72)
total_pass = total_checks = 0
all_ok = True
for name, status, p, t_count, elapsed, _ in results:
    print(f"{name:<26} {status:<8} {p}/{t_count}".ljust(48) + f"{elapsed:.2f}s")
    total_pass += p
    total_checks += t_count
    if status != '✓':
        all_ok = False
print("─" * 72)
print(f"{'TOTAL':<26} {('✓' if all_ok else '✗'):<8} {total_pass}/{total_checks}".ljust(48) + f"{t_total:.2f}s")

if not all_ok:
    print("\n" + "═" * 72)
    print("  FALHAS — DETALHES")
    print("═" * 72)
    for name, status, _, _, _, out in results:
        if status != '✓':
            print(f"\n▶ {name}")
            for line in out.split('\n'):
                if '✗' in line:
                    print(f"  {line.strip()}")

print("\n" + "═" * 72)
if all_ok:
    print(f"  ✅ TUDO VERDE — {total_pass}/{total_checks} checks ({t_total:.1f}s)")
    sys.exit(0)
else:
    print(f"  ⚠  Suítes falhando — corrigir antes de publicar")
    sys.exit(1)
