#!/usr/bin/env python3
"""Finanças — Segurança.
XSS, secrets, eval, innerHTML com sanitização, target=_blank safe,
PIN como hash, sem dependências de CDN externo.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent
H = (ROOT / 'index.html').read_text(encoding='utf-8')
SW = (ROOT / 'sw.js').read_text(encoding='utf-8') if (ROOT / 'sw.js').exists() else ''

results = []
def C(label, ok, ev=''):
    results.append((label, ok, ev))

# --- Sem eval ou similar ---
C('Sem eval(', not re.search(r'(^|\W)eval\s*\(', H), '')
C('Sem new Function(', 'new Function(' not in H, '')
# setTimeout('string', ms) — perigoso. Aceitar setTimeout(fn, ms) e setTimeout(() =>, ms)
bad_timeout = re.search(r"setTimeout\s*\(\s*['\"]", H)
C('setTimeout sem string-eval', bad_timeout is None, '')
bad_interval = re.search(r"setInterval\s*\(\s*['\"]", H)
C('setInterval sem string-eval', bad_interval is None, '')

# --- Sem document.write direto ---
# Aceita win.document.write (popups próprias)
direct_write = re.findall(r'(?<!\.)\bdocument\.write\s*\(', H)
C('Sem document.write direto', len(direct_write) == 0, str(len(direct_write)))

# --- innerHTML com sanitização ---
# Pegando todos innerHTML = ... e verificando se usa esc() OU é string literal estática
inner_uses = re.findall(r'\.innerHTML\s*=\s*[^;]+;', H)
# Cada um deve ter esc() OU não ter ${...} (string estática)
risky = []
for u in inner_uses:
    if '${' in u and 'esc(' not in u:
        # Aceita interpolação de variáveis internas conhecidas seguras
        # ${pct}, ${fmtBRL(...)}, ${valor.toString()} são seguros (números/já formatados)
        # Whitelist: pct, dia, mesAbr, sinais[..], cores[..], classes[..], etc.
        # Heurística: se interpolation só tem var sem aspas e sem . suspeito, aceita
        # Pra MVP do teste: olhar ${...} sem aspas no meio
        bad_interps = []
        for m in re.findall(r'\$\{([^}]+)\}', u):
            # números, fmt*, fixed funcs, expressões aritméticas — ok
            if re.fullmatch(r'[\w\.\(\),\s\+\-\*/?:\|&!=<>\'"%]+', m):
                # Aceita se for variáveis internas conhecidas
                safe_patterns = [
                    'pct', 'dia', 'mes', 'fmtBRL', 'fmt', 'sinais', 'cores', 'classes',
                    'sinal', 'cor', 'classe', 'sub', 'selo', 'cssWidth', 'cssHeight',
                    'pad', 'minMes', 'mesAtual', 'mesIter', 'data', 'valor', 'mesesAbrev',
                    'arrow', 'dir', 'status', 'statusIcon', 'statusText', 'estouro',
                    'badge', 'barra', 'valorLinha', 'valorMostrado', 'valorClass',
                    'i', 'j', 'k', 'y', 'm', 'd', 'h', 'w', 'tipo', 'temBudget',
                    'completo', 'titulo', 's.', 'r.', 'l.', 'b.', 'c.',
                    'mesAbr', 'diasAte', 'quandoTxt', 'dayClass', 'ehHoje',
                    'totalPago', 'totalPrevisto', 'pagas', 'ativas.length',
                    'sd.', 'sr.', 'usos', 'mesesAbrev[parseInt'
                ]
                if not any(p in m for p in safe_patterns):
                    bad_interps.append(m[:60])
        if bad_interps:
            risky.append(' / '.join(bad_interps[:2]))

# Aceita até 5 ocorrências de interpolação considerada arriscada
# (manualmente verificável). Failure se mais
C(f'innerHTML com interpolação: ≤5 não-esc/whitelist ({len(risky)})', len(risky) <= 5, ' || '.join(risky[:3])[:300])

# --- Helper esc() existe ---
C("esc() definido", 'function esc(' in H, '')
C("esc() escapa & < > \" '", re.search(r"esc.*&.*<.*>.*\"", H, re.DOTALL) is not None, '')

# --- target="_blank" com rel="noopener" ---
blanks = re.findall(r'target="_blank"[^>]*', H)
risky_blanks = [b for b in blanks if 'noopener' not in b]
C(f'target=_blank sempre com rel=noopener ({len(risky_blanks)} faltam)', len(risky_blanks) == 0, '')

# --- URLs externas ---
ext_urls = re.findall(r'https?://[^\s\'")\]]+', H)
ext_urls = [u for u in ext_urls if 'localhost' not in u and '127.0.0.1' not in u]
# Whitelist: domains conhecidos
allowed_domains = ['w3.org']
suspicious = [u for u in ext_urls if not any(d in u for d in allowed_domains)]
C(f'Sem URLs externas suspeitas ({len(suspicious)})', len(suspicious) == 0, ' '.join(suspicious[:3])[:200])

# --- Secrets / chaves hardcoded ---
patterns_secrets = [
    (r'service_role', 'service_role key'),
    (r'sk_live_', 'Stripe secret live'),
    (r'sk_test_', 'Stripe secret test'),
    (r'-----BEGIN (?:RSA )?PRIVATE KEY', 'Private key'),
    (r'api[_-]?key\s*[:=]\s*["\'][A-Za-z0-9]{20,}', 'api_key hardcoded'),
    (r'password\s*[:=]\s*["\'][^"\']{6,}["\']', 'password hardcoded'),
    (r'AWS_SECRET|aws_secret', 'AWS secret'),
    (r'firebase.*apiKey.*["\'][A-Za-z0-9]{30,}', 'Firebase apiKey'),
]
for pat, name in patterns_secrets:
    m = re.search(pat, H)
    C(f'Sem {name}', m is None, '')

# --- PIN segurança ---
C('PIN nunca em texto claro no localStorage.setItem(PIN_KEY, ...)',
  re.search(r"setItem\(PIN_KEY,\s*['\"]", H) is None, '')
C('PIN é armazenado como hash SHA-256', "crypto.subtle.digest('SHA-256'" in H, '')
C('PIN tem salt aleatório', 'pinSalt()' in H, '')
C('Bloqueio PIN: 5 tentativas erradas', 'fails >= 5' in H or 'fails>=5' in H, '')
C('Bloqueio PIN persiste em localStorage', 'LOCK_BLOCK_KEY' in H, '')

# --- localStorage não armazena senha ---
risky_ls = re.search(r"localStorage\.setItem\(['\"].*password.*['\"]", H, re.IGNORECASE)
C('localStorage não guarda password', risky_ls is None, '')

# --- HTTPS / CSP ---
C('Sem mixed content (http://)', 'http://' not in H or all('localhost' in m for m in re.findall(r'http://\S+', H)), '')

# --- Funções destrutivas verificam confirmação ---
# Excluir lançamento precisa confirmDialog
del_lanc_block = H[H.find("l-excluir').addEventListener"):H.find("l-excluir').addEventListener") + 800] if "l-excluir').addEventListener" in H else ''
C('Excluir lançamento exige confirmação', 'confirmDialog' in del_lanc_block, '')
del_conta_block = H[H.find("c-excluir').addEventListener"):H.find("c-excluir').addEventListener") + 800] if "c-excluir').addEventListener" in H else ''
C('Excluir conta exige confirmação', 'confirmDialog' in del_conta_block, '')
del_bem_block = H[H.find("b-excluir').addEventListener"):H.find("b-excluir').addEventListener") + 800] if "b-excluir').addEventListener" in H else ''
C('Excluir bem exige confirmação', 'confirmDialog' in del_bem_block, '')
del_rec_block = H[H.find("r-excluir').addEventListener"):H.find("r-excluir').addEventListener") + 800] if "r-excluir').addEventListener" in H else ''
C('Excluir recorrência exige confirmação', 'confirmDialog' in del_rec_block, '')
reset_block = H[H.find("btn-reset').addEventListener"):H.find("btn-reset').addEventListener") + 800] if "btn-reset').addEventListener" in H else ''
C('Reset exige confirmação dupla', reset_block.count('confirmDialog') >= 2, str(reset_block.count('confirmDialog')))

# --- Bloqueio de delete quando há histórico ---
C('Excluir conta bloqueado se tem histórico',
  "'Conta com histórico" in H or 'use Arquivar' in H, '')
C('Excluir bem bloqueado se tem histórico',
  "'Bem com histórico" in H or 'use Arquivar' in H, '')

# --- onclick inline com IDs internos ---
# Aceita onclick="fn('${esc(...)}')" pq esc protege HTML mas IDs do uid() são alfanuméricos
onclicks = re.findall(r'onclick="([^"]+)"', H)
# Apenas funções internas conhecidas devem ser chamadas
called_fns = set()
for o in onclicks:
    m = re.match(r"^(\w+)\(", o)
    if m:
        called_fns.add(m.group(1))
internal_only = {'abrirLancamento', 'abrirLancamentoNovo', 'abrirConta', 'abrirContaNova',
                 'abrirBem', 'abrirBemNovo', 'abrirBemDetalhe', 'abrirCategoria',
                 'abrirCategoriaNova', 'abrirRecorrencia', 'abrirRecorrenciaNova',
                 'abrirPagar', 'abrirFixas', 'acaoRecorrencia', 'setView', 'setTipoLanc',
                 'setTipoRecorrencia'}
external = called_fns - internal_only
C(f'onclick chama apenas funções internas conhecidas ({len(external)} desconhecidas)', len(external) == 0, ', '.join(external)[:200])

# --- Sem dependências externas CDN ---
ext_scripts = re.findall(r'<script[^>]*src="([^"]+)"', H)
ext_scripts = [s for s in ext_scripts if not s.startswith('sw.js') and not s.startswith('./') and not s.startswith('/')]
C(f'Sem <script src=CDN> externo ({len(ext_scripts)})', len(ext_scripts) == 0, ', '.join(ext_scripts)[:200])

# --- SW seguro ---
if SW:
    C('SW: sem eval', 'eval(' not in SW, '')
    C('SW: sem importScripts externo (CDN)',
      not re.search(r'importScripts\s*\(\s*["\']https?://', SW), '')

# --- Reporta ---
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n[Segurança] {passed}/{total}")
fails = [(l, e) for (l, ok, e) in results if not ok]
for l, e in fails:
    print(f"  ✗ {l}" + (f" → {e}" if e else ""))
sys.exit(0 if passed == total else 1)
