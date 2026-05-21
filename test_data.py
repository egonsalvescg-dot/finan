#!/usr/bin/env python3
"""Finanças — Integridade de dados.
localStorage keys consistentes, IDs HTML referenciados existem,
handlers onclick chamam funções definidas, modelos de dados completos.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent
H = (ROOT / 'index.html').read_text(encoding='utf-8')

results = []
def C(label, ok, ev=''):
    results.append((label, ok, ev))

# --- localStorage keys consistentes ---
ls_keys_used = set(re.findall(r"localStorage\.\w+\(['\"]([^'\"]+)['\"]", H))
ls_keys_via_const = set()
for m in re.finditer(r"localStorage\.\w+\((\w+)\b", H):
    name = m.group(1)
    # Procura definição da constante
    cdef = re.search(rf"const\s+{name}\s*=\s*['\"]([^'\"]+)", H)
    if cdef:
        ls_keys_via_const.add(cdef.group(1))
all_ls_keys = ls_keys_used | ls_keys_via_const
expected_prefix = 'financas:'
keys_with_prefix = [k for k in all_ls_keys if k.startswith(expected_prefix)]
C(f'Todas as keys localStorage com prefixo "financas:" ({len(keys_with_prefix)}/{len(all_ls_keys)})',
  len(keys_with_prefix) == len(all_ls_keys), ' '.join(all_ls_keys - set(keys_with_prefix))[:200])

# --- Reset apaga todas as chaves financas:* ---
C('Reset varre Object.keys com filter financas:*',
  "Object.keys(localStorage).filter(k => k.startsWith('financas:'))" in H, '')

# --- IDs HTML referenciados via getElementById existem ---
ids_html = set(re.findall(r'\bid="([^"]+)"', H))
ids_html = {i for i in ids_html if '${' not in i}
gbid_calls = re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", H)
missing_ids = [g for g in gbid_calls if g not in ids_html]
C(f'getElementById sempre encontra id estático ({len(missing_ids)} faltam)',
  len(missing_ids) == 0, ', '.join(set(missing_ids))[:200])

# --- onclick="foo(...)" chama função definida ---
onclick_fns = set(re.findall(r'onclick="(\w+)\(', H))
fn_decls = set(re.findall(r'function\s+(\w+)\s*\(', H))
arrow_assigns = set(re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(', H))
defined_fns = fn_decls | arrow_assigns
missing_handlers = onclick_fns - defined_fns
C(f'onclick chama funções definidas ({len(missing_handlers)} órfãos)',
  len(missing_handlers) == 0, ', '.join(missing_handlers))

# --- Document.querySelector(id) também valido ---
qs_calls = re.findall(r"document\.querySelector\(['\"]#([^'\"\s]+)['\"]", H)
missing_qs = [q for q in qs_calls if q not in ids_html]
C(f'querySelector com #id válido ({len(missing_qs)} faltam)', len(missing_qs) == 0, ', '.join(missing_qs)[:200])

# --- DB.* arrays usados existem em loadDB ---
db_arrays_in_load = re.search(r'function loadDB[\s\S]*?return\s*\{([\s\S]*?)\};', H)
db_arrays = []
if db_arrays_in_load:
    db_arrays = re.findall(r'(\w+):\s*\[', db_arrays_in_load.group(1))
    # também pega "categorias: [...DEFAULT_CATEGORIAS]" e "categorias: [...]"
    db_arrays_alt = re.findall(r'(\w+):\s*\[\.\.\.', db_arrays_in_load.group(1))
    db_arrays = list(set(db_arrays + db_arrays_alt))
expected_arrays = {'contas', 'bens', 'categorias', 'lancamentos', 'recorrencias'}
got_arrays = set(db_arrays)
C(f'loadDB inclui {expected_arrays} ({got_arrays})',
  expected_arrays.issubset(got_arrays), ', '.join(expected_arrays - got_arrays))

# --- DB.* arrays acessados existem ---
db_access = set(re.findall(r'DB\.(\w+)', H))
db_access -= {'version', 'recorrencias', 'lancamentos', 'contas', 'bens', 'categorias'}
C(f'DB acessa apenas arrays conhecidos ({len(db_access)} desconhecidos)',
  len(db_access) == 0, ', '.join(db_access))

# --- Tipos de lançamento conhecidos ---
tipos = set(re.findall(r"l\.tipo\s*===?\s*'(\w+)'", H))
tipos |= set(re.findall(r"tipo:\s*'(\w+)'", H))
expected_tipos = {'receita', 'despesa', 'transferencia', 'investimento'}
unknown = tipos - expected_tipos
C(f'Tipos de lançamento conhecidos ({len(unknown)} desconhecidos)',
  len(unknown) == 0, ', '.join(unknown))

def extract_object_fields(obj_body):
    """Extrai campos de um objeto literal, suportando shorthand."""
    # Remove strings literais primeiro pra não confundir
    cleaned = re.sub(r'"[^"]*"', '""', obj_body)
    cleaned = re.sub(r"'[^']*'", "''", cleaned)
    fields = set()
    # Campo explícito: nome:
    fields.update(re.findall(r'(\w+):', cleaned))
    # Shorthand: ele aparece como token sozinho, geralmente após , ou {
    # Padrão: ", nome," ou ", nome\n" ou "{ nome," ou "{ nome }" (com whitespace antes do })
    # Usa um pass mais simples: separa por vírgulas/quebras de linha e olha cada item
    items = re.split(r'[,\n]', cleaned)
    for item in items:
        item = item.strip().rstrip('}').rstrip(';').strip()
        # Se item é apenas um identificador (shorthand)
        if re.fullmatch(r'\w+', item):
            if item not in ('return', 'true', 'false', 'null', 'undefined'):
                fields.add(item)
    return fields

# --- Recorrência tem campos esperados ---
rec_create = re.search(r"DB\.recorrencias\.push\(\{([\s\S]*?)\}\)", H)
expected_rec_fields = {'id', 'nome', 'valor', 'diaVencimento', 'tipo', 'contaId', 'categoriaId', 'bemId', 'ativa', 'autoCreate', 'criadaEm'}
if rec_create:
    got = extract_object_fields(rec_create.group(1))
    missing = expected_rec_fields - got
    C(f'Recorrência salva todos os campos esperados ({len(missing)} faltam)',
      len(missing) == 0, ', '.join(missing))

# --- Categoria tem campos esperados ---
cat_create = re.search(r"DB\.categorias\.push\(\{([\s\S]*?)\}\);", H)
if cat_create:
    got = extract_object_fields(cat_create.group(1))
    expected = {'id', 'nome', 'tipo', 'cor', 'budget'}
    missing = expected - got
    C(f'Categoria salva todos os campos (id,nome,tipo,cor,budget): {len(missing)} faltam',
      len(missing) == 0, ', '.join(missing))

# --- Lançamento save preserva campos com spread ---
C('Save lançamento usa spread do original', '...(original || {})' in H, '')
C('Save lançamento clean order: spread → tipo → valor → data', re.search(r'\.\.\.\(original \|\| \{\}\),[\s\S]*?id:[\s\S]*?tipo:', H) is not None, '')

# --- Filtros de chip mapeiam pra tipos válidos ---
filter_chips = re.findall(r'data-filter="(\w+)"', H)
chip_set = set(filter_chips) - {'todos'}
unknown_chips = chip_set - expected_tipos
C(f'Chips de filtro mapeiam pra tipos válidos ({len(unknown_chips)} desconhecidos)',
  len(unknown_chips) == 0, ', '.join(unknown_chips))

# --- View IDs ---
view_attrs = set(re.findall(r'data-view="(\w+)"', H))
view_html_ids = {i.replace('view-', '') for i in ids_html if i.startswith('view-')}
unknown_views = view_attrs - view_html_ids
C(f'data-view sempre aponta pra view existente ({len(unknown_views)} órfãos)',
  len(unknown_views) == 0, ', '.join(unknown_views))

# --- Categorias default têm IDs únicos ---
cat_defs = re.search(r'DEFAULT_CATEGORIAS\s*=\s*\[([\s\S]*?)\];', H)
if cat_defs:
    ids = re.findall(r"id:\s*'([^']+)'", cat_defs.group(1))
    C(f'DEFAULT_CATEGORIAS com IDs únicos ({len(ids)} cat / {len(set(ids))} únicos)',
      len(ids) == len(set(ids)), '')
    tipos_cats = re.findall(r"tipo:\s*'(\w+)'", cat_defs.group(1))
    invalid = [t for t in tipos_cats if t not in {'receita', 'despesa'}]
    C(f'DEFAULT_CATEGORIAS com tipo receita/despesa ({len(invalid)} inválidos)',
      len(invalid) == 0, '')

# --- IDs com formato consistente ---
# uid() gera base36 — ids no app não devem ter prefixo PREFIX-XXX pq são livres
# Skip esse check

# --- Conta usa saldoInicial (não "balance" ou outro) ---
C('Conta tem campo saldoInicial', 'saldoInicial' in H, '')
C('Bem tem campo valorInicial', 'valorInicial' in H, '')

# --- Campos calculados não persistem ---
# patrimonioTotal não deveria ser salvo no DB — sempre calculado
# Check: DB não tem patrimonio: setado em nenhum lugar
risky_field = re.search(r"DB\.patrimonio\s*=", H)
C('Patrimônio nunca salvo no DB (sempre derivado)', risky_field is None, '')

# --- Idempotência: pagar recorrência ---
C('Pagar fixa idempotente: busca lançamento existente do mês',
  'l.recorrenciaId === r.id && mesPertence(l.data, mesDest)' in H or
  'l.recorrenciaId === r.id\n    && mesPertence' in H, '')

# --- Validação básica em lançamentos importados ---
C('Import valida tipos e arrays', "Array.isArray" in H and 'lancamentos.filter' in H, '')

# --- Tipos de conta livres mas consistentes ---
# Conta tem campo `tipo` como string livre — não bloquear
# Aceito como string. Verificar que NÃO usa enum.
# Skip

# --- Reporta ---
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n[Integridade] {passed}/{total}")
fails = [(l, e) for (l, ok, e) in results if not ok]
for l, e in fails:
    print(f"  ✗ {l}" + (f" → {e}" if e else ""))
sys.exit(0 if passed == total else 1)
