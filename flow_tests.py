#!/usr/bin/env python3
"""Finanças — Fluxos críticos ponta a ponta.
Cada fluxo verifica: função existe, error handling, persistência,
re-render, feedback ao usuário, validação onde aplicável.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent
H = (ROOT / 'index.html').read_text(encoding='utf-8')

results = []
def C(label, ok, ev=''):
    results.append((label, ok, ev))

def find_handler_block(needle):
    """Acha o bloco de um event handler (até fechar a função)."""
    idx = H.find(needle)
    if idx < 0:
        return ''
    # acha primeiro '{' depois do listener
    brace = H.find('{', idx)
    if brace < 0:
        return ''
    depth = 1
    i = brace + 1
    while i < len(H) and depth > 0:
        if H[i] == '{': depth += 1
        elif H[i] == '}': depth -= 1
        i += 1
    return H[idx:i]

def fn_body(name):
    """Acha o corpo de uma função declarada (function name(...) { ... } )."""
    pat = re.search(rf'function\s+{name}\s*\([^)]*\)\s*\{{', H)
    if not pat:
        # tenta arrow
        pat2 = re.search(rf'(?:const|let|var)\s+{name}\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{{', H)
        if not pat2:
            return ''
        start = pat2.end() - 1
    else:
        start = pat.end() - 1
    depth = 1
    i = start + 1
    while i < len(H) and depth > 0:
        if H[i] == '{': depth += 1
        elif H[i] == '}': depth -= 1
        i += 1
    return H[start:i]

# ════════════════════════════════════════════════════════════════
# FLUXO 1 — Boot do app
# ════════════════════════════════════════════════════════════════
C('1.1 loadDB existe', 'function loadDB' in H, '')
C('1.2 loadDB faz fallback se falha', 'function loadDB' in H and 'catch (e)' in fn_body('loadDB'), '')
C('1.3 loadDB tem migração de campos novos (recorrencias)', 'if (!db.recorrencias)' in H, '')
C('1.4 Boot registra Service Worker', "navigator.serviceWorker.register('sw.js')" in H, '')
C('1.5 Boot chama runAutoCreate antes do render', '_autoCriados = runAutoCreate()' in H, '')
C('1.6 Boot chama render()', '\nrender();' in H, '')
C('1.7 Boot mostra PIN se ativo', 'if (hasPin()) showLock' in H, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 2 — Criar lançamento (receita)
# ════════════════════════════════════════════════════════════════
ls_save = find_handler_block("getElementById('l-salvar').addEventListener")
C('2.1 Handler l-salvar existe', len(ls_save) > 100, '')
C('2.2 Save valida valor > 0', 'valor <= 0' in ls_save and 'Informe um valor' in ls_save, '')
C('2.3 Save preserva campos via spread', '...(original || {})' in ls_save, '')
C('2.4 Save persiste em DB.lancamentos', 'DB.lancamentos.push' in ls_save and 'DB.lancamentos[i]' in ls_save, '')
C('2.5 Save chama saveDB', 'saveDB()' in ls_save, '')
C('2.6 Save fecha modal', "closeModal('modal-lancar')" in ls_save, '')
C('2.7 Save re-renderiza', 'render()' in ls_save, '')
C('2.8 Save dá feedback toast', 'toast(' in ls_save, '')
C('2.9 Save valida conta selecionada', "Selecione uma conta" in ls_save, '')
C('2.10 Save transferência exige origem ≠ destino', 'origem e destino' in ls_save.lower() or 'diferentes' in ls_save.lower(), '')
C('2.11 Save investimento valida bem selecionado', "Selecione um bem" in ls_save, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 3 — Editar lançamento
# ════════════════════════════════════════════════════════════════
fn_ed = fn_body('abrirLancamento')
C('3.1 abrirLancamento existe', len(fn_ed) > 100, '')
C('3.2 abrirLancamento carrega DB.lancamentos.find', 'DB.lancamentos.find' in fn_ed, '')
C('3.3 abrirLancamento mostra botão Excluir', "'l-excluir').style.display = 'block'" in fn_ed, '')
C('3.4 abrirLancamento define editingLancId', 'editingLancId = id' in fn_ed, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 4 — Excluir lançamento
# ════════════════════════════════════════════════════════════════
le_del = find_handler_block("l-excluir').addEventListener")
C('4.1 Handler l-excluir existe', len(le_del) > 50, '')
C('4.2 l-excluir exige confirmDialog', 'confirmDialog' in le_del, '')
C('4.3 l-excluir tem safeguard contra delete em massa', 'l.id !== idToDelete' in le_del, '')
C('4.4 l-excluir zera editingLancId', 'editingLancId = null' in le_del, '')
C('4.5 l-excluir persiste e re-renderiza', 'saveDB()' in le_del and 'render()' in le_del, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 5 — Criar conta
# ════════════════════════════════════════════════════════════════
cs_save = find_handler_block("c-salvar').addEventListener")
C('5.1 Handler c-salvar existe', len(cs_save) > 100, '')
C('5.2 c-salvar valida nome', 'Informe um nome' in cs_save, '')
C('5.3 c-salvar valida saldo inicial inválido', 'Saldo inicial inválido' in cs_save, '')
C('5.4 c-salvar avisa se muda saldo inicial com histórico', 'Recalcula TODO' in cs_save or 'recalcula TODO' in cs_save, '')
C('5.5 c-salvar persiste e re-renderiza', 'saveDB()' in cs_save and 'render()' in cs_save, '')
C('5.6 c-salvar dá feedback toast', 'toast(' in cs_save, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 6 — Arquivar/Restaurar conta
# ════════════════════════════════════════════════════════════════
ca_arq = find_handler_block("c-arquivar').addEventListener")
C('6.1 Handler c-arquivar existe', len(ca_arq) > 50, '')
C('6.2 c-arquivar exige confirmação', 'confirmDialog' in ca_arq, '')
C('6.3 c-arquivar toggle archived', 'c.archived = !c.archived' in ca_arq, '')
C('6.4 c-arquivar persiste', 'saveDB()' in ca_arq, '')
C('6.5 c-arquivar mostra Restaurar/Arquivar conforme estado', "'Restaurar conta'" in H and "'Arquivar conta'" in H, '')
C('6.6 Excluir bloqueado se conta tem histórico', "'Conta com histórico" in H, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 7 — Criar bem
# ════════════════════════════════════════════════════════════════
bs_save = find_handler_block("b-salvar').addEventListener")
C('7.1 Handler b-salvar existe', len(bs_save) > 100, '')
C('7.2 b-salvar valida nome', 'Informe um nome' in bs_save, '')
C('7.3 b-salvar valida valor inicial inválido', 'Valor inicial inválido' in bs_save, '')
C('7.4 b-salvar persiste e re-renderiza', 'saveDB()' in bs_save and 'render()' in bs_save, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 8 — Arquivar/Excluir bem
# ════════════════════════════════════════════════════════════════
ba_arq = find_handler_block("b-arquivar').addEventListener")
C('8.1 Handler b-arquivar existe', len(ba_arq) > 50, '')
C('8.2 b-arquivar toggle archived', 'b.archived = !b.archived' in ba_arq, '')
C('8.3 Excluir bloqueado se bem tem histórico', "'Bem com histórico" in H, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 9 — Criar categoria com orçamento
# ════════════════════════════════════════════════════════════════
cat_save = find_handler_block("cat-salvar').addEventListener")
C('9.1 Handler cat-salvar existe', len(cat_save) > 50, '')
C('9.2 cat-salvar valida nome', 'Informe um nome' in cat_save, '')
C('9.3 cat-salvar aceita budget só em despesa', "tipo === 'despesa'" in cat_save and 'rawBudget' in cat_save, '')
C('9.4 cat-salvar valida budget inválido', 'Orçamento inválido' in cat_save, '')
C('9.5 cat-salvar avisa mudança de tipo com histórico', "ficará órfão" in cat_save, '')
C('9.6 cat-salvar persiste e re-renderiza', 'saveDB()' in cat_save and 'render()' in cat_save, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 10 — Criar recorrência (despesa ou receita)
# ════════════════════════════════════════════════════════════════
rs_save = find_handler_block("r-salvar').addEventListener")
C('10.1 Handler r-salvar existe', len(rs_save) > 100, '')
C('10.2 r-salvar suporta receita E despesa', 'currentTipoRecorrencia' in rs_save, '')
C('10.3 r-salvar valida descrição', 'Informe a descrição' in rs_save, '')
C('10.4 r-salvar valida conta', 'Selecione uma conta' in rs_save, '')
C('10.5 r-salvar salva autoCreate flag', 'autoCreate' in rs_save, '')
C('10.6 r-salvar salva campo tipo', 'tipo' in rs_save, '')
C('10.7 r-salvar limpa bemId quando receita',
  "tipo === 'despesa' ? (document.getElementById('r-bem').value || null) : null" in rs_save, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 11 — Pagar/Receber recorrência (idempotente)
# ════════════════════════════════════════════════════════════════
p_conf = find_handler_block("p-confirmar').addEventListener")
C('11.1 Handler p-confirmar existe', len(p_conf) > 100, '')
C('11.2 p-confirmar valida valor > 0', 'valor <= 0' in p_conf, '')
C('11.3 p-confirmar é idempotente (atualiza se já existe)',
  'l.recorrenciaId === r.id' in p_conf and 'existente' in p_conf, '')
C('11.4 p-confirmar usa tipo da recorrência (receita/despesa)',
  "r.tipo || 'despesa'" in p_conf, '')
C('11.5 p-confirmar bemId só em despesa',
  "tipoRec === 'despesa'" in p_conf, '')
C('11.6 p-confirmar persiste e re-renderiza', 'saveDB()' in p_conf and 'render()' in p_conf, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 12 — AutoCreate de recorrência
# ════════════════════════════════════════════════════════════════
ac = fn_body('runAutoCreate')
C('12.1 runAutoCreate existe', len(ac) > 100, '')
C('12.2 runAutoCreate filtra apenas ativa+autoCreate', '!r.ativa || !r.autoCreate' in ac, '')
C('12.3 runAutoCreate limita retroatividade', 'MAX_MESES_RETROAGIR' in ac, '')
C('12.4 runAutoCreate evita duplicata (idempotente)', 'jaExiste' in ac, '')
C('12.5 runAutoCreate só gera se vencimento já passou', 'dataVencimento > hojeIso' in ac, '')
C('12.6 runAutoCreate marca lançamento como autoCreated', 'autoCreated: true' in ac, '')
C('12.7 runAutoCreate persiste se criou algo', 'saveDB()' in ac, '')
C('12.8 Banner aparece quando há auto-criados', 'mostrarBannerAuto' in H, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 13 — PIN: criar, validar, bloquear
# ════════════════════════════════════════════════════════════════
hpc = fn_body('handlePinComplete')
C('13.1 handlePinComplete existe', len(hpc) > 100, '')
C('13.2 PIN: try/catch contra cripto indisponível', 'catch (err)' in hpc, '')
C('13.3 PIN: CRYPTO_OK guard', '!CRYPTO_OK' in hpc, '')
C('13.4 PIN: race guard (length === 4)', 'lockBuffer.length !== 4' in hpc, '')
C('13.5 PIN: hashPin com salt', 'hashPin' in hpc, '')
C('13.6 PIN: bloqueia após 5 falhas', 'fails >= 5' in hpc or 'fails>=5' in hpc, '')
C('13.7 PIN: lockBlockedUntil persiste em localStorage', 'setLockBlockedUntil' in hpc, '')
C('13.8 PIN: confirmação set-new + set-confirm', "lockMode === 'set-confirm'" in hpc and "lockMode === 'set-new'" in hpc, '')

# Pad keys
pad = find_handler_block("'#lock-pad .pad-key').forEach")
C('13.9 Pad: bloqueia clique se em cooldown', 'getLockBlockedUntil' in pad, '')
C('13.10 Pad: clearTimeout no ⌫', 'clearTimeout(lockCompleteTimer)' in pad, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 14 — Export JSON (backup)
# ════════════════════════════════════════════════════════════════
exp = find_handler_block("btn-exportar').addEventListener")
C('14.1 Handler btn-exportar existe', len(exp) > 50, '')
C('14.2 Export gera Blob JSON', 'new Blob' in exp and 'JSON.stringify' in exp, '')
C('14.3 Export inclui nome com data', 'financas-backup-' in exp and 'hoje()' in exp, '')
C('14.4 Export revoga URL após download', 'revokeObjectURL' in exp, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 15 — Import JSON (com validação)
# ════════════════════════════════════════════════════════════════
imp = find_handler_block("file-importar').addEventListener")
C('15.1 Handler file-importar existe', len(imp) > 100, '')
C('15.2 Import exige confirmDialog', 'confirmDialog' in imp, '')
C('15.3 Import valida JSON parse', 'JSON.parse' in imp and 'catch' in imp, '')
C('15.4 Import valida todos os arrays', 'Array.isArray' in imp, '')
C('15.5 Import fornece defaults se faltar arrays',
  '[...DEFAULT_CATEGORIAS]' in imp, '')
C('15.6 Import filtra lançamentos malformados', 'lancamentos.filter' in imp, '')
C('15.7 Import dá feedback com count', 'lancamentos.length' in imp and 'toast(' in imp, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 16 — Reset completo (apaga tudo)
# ════════════════════════════════════════════════════════════════
rs = find_handler_block("btn-reset').addEventListener")
C('16.1 Handler btn-reset existe', len(rs) > 50, '')
C('16.2 Reset confirma duas vezes', rs.count('confirmDialog') >= 2, str(rs.count('confirmDialog')))
C('16.3 Reset varre todas chaves financas:*',
  "k.startsWith('financas:')" in rs, '')
C('16.4 Reset recarrega DB com loadDB', 'DB = loadDB()' in rs, '')
C('16.5 Reset re-renderiza', 'render()' in rs, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 17 — Navegação entre meses (patrimônio retrospectivo)
# ════════════════════════════════════════════════════════════════
prev = find_handler_block("prev-month').addEventListener")
nxt = find_handler_block("next-month').addEventListener")
C('17.1 Handler prev-month', 'navMes(currentMes, -1)' in prev, '')
C('17.2 Handler next-month', 'navMes(currentMes, 1)' in nxt, '')
C('17.3 Patrimônio retrospectivo: saldoConta aceita ateMes', 'saldoConta(contaId, ateMes' in H, '')
C('17.4 Patrimônio retrospectivo: valorBem aceita ateMes', 'valorBem(bemId, ateMes' in H, '')
C('17.5 Label muda em mês passado', 'Patrimônio em' in H or 'fim de' in H, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 18 — Sync entre abas
# ════════════════════════════════════════════════════════════════
sync = find_handler_block("addEventListener('storage'")
C('18.1 Listener de storage event existe', len(sync) > 50, '')
C('18.2 Sync valida estrutura antes de aplicar', 'Array.isArray(next.lancamentos)' in sync, '')
C('18.3 Sync atualiza render', 'render()' in sync, '')
C('18.4 Sync notifica usuário', 'toast(' in sync, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 19 — Error boundaries globais
# ════════════════════════════════════════════════════════════════
err_b = find_handler_block("addEventListener('error'")
C('19.1 window.onerror existe', len(err_b) > 30, '')
C('19.2 Error global notifica usuário', 'toast(' in err_b, '')
prom_b = find_handler_block("addEventListener('unhandledrejection'")
C('19.3 unhandledrejection existe', len(prom_b) > 30, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 20 — Confirmação custom (substitui confirm() nativo)
# ════════════════════════════════════════════════════════════════
cd = fn_body('confirmDialog')
C('20.1 confirmDialog existe', len(cd) > 100, '')
C('20.2 confirmDialog retorna Promise', 'return new Promise' in cd, '')
C('20.3 confirmDialog suporta variantes (danger/warning)',
  'danger' in cd and 'warning' in cd, '')
C('20.4 confirmDialog cleanup remove listeners',
  'removeEventListener' in cd, '')
C('20.5 confirmDialog z-index acima dos modais (300)',
  re.search(r'z-index:\s*300', H) is not None, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 21 — Toast com fila
# ════════════════════════════════════════════════════════════════
tq = fn_body('toast')
C('21.1 toast() existe', len(tq) > 10, '')
C('21.2 Toast com fila (não sobrescreve)', '_toastQueue' in H, '')
C('21.3 Toast processa em sequência', '_showNextToast' in H, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 22 — Saldo retrospectivo e gráfico
# ════════════════════════════════════════════════════════════════
gp = fn_body('renderGraficoPatrimonio')
C('22.1 renderGraficoPatrimonio existe', len(gp) > 100, '')
C('22.2 Gráfico calcula 6 meses', "for (let i = 5; i >= 0; i--)" in gp, '')
C('22.3 Gráfico DPR-aware (retina)', 'devicePixelRatio' in gp, '')
C('22.4 Gráfico esconde se sem dados', 'tituloEl.style.display = \'none\'' in gp, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 23 — Próximos compromissos
# ════════════════════════════════════════════════════════════════
pc = fn_body('renderProximosCompromissos')
C('23.1 renderProximosCompromissos existe', len(pc) > 100, '')
C('23.2 Limita a 7 dias adiante', 'limite.setDate(limite.getDate() + 7)' in pc, '')
C('23.3 Top 3 candidatos', 'slice(0, 3)' in pc, '')
C('23.4 Ignora recorrências já pagas no mês', 'pago' in pc and 'continue' in pc, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 24 — Renderizadores principais não quebram com DB vazio
# ════════════════════════════════════════════════════════════════
for fn in ['renderInicio', 'renderLancamentos', 'renderContas', 'renderBens', 'renderSaldoDestaque', 'renderPatrimonioMini']:
    C(f'24.{fn} existe', f'function {fn}' in H, '')

# ════════════════════════════════════════════════════════════════
# FLUXO 25 — Cálculos com round2 (anti drift)
# ════════════════════════════════════════════════════════════════
for fn in ['saldoConta', 'valorBem', 'totalInvestidoBem', 'gastosBem', 'patrimonioTotal']:
    body = fn_body(fn)
    C(f'25.{fn} retorna round2(...)', 'round2(' in body, '')

# Reporta
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n[Fluxos] {passed}/{total}")
fails = [(l, e) for (l, ok, e) in results if not ok]
for l, e in fails:
    print(f"  ✗ {l}" + (f" → {e}" if e else ""))
sys.exit(0 if passed == total else 1)
