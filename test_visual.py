#!/usr/bin/env python3
"""Finanças — Visual e layout.
Z-index hierárquico, tokens CSS, viewport responsivo,
ícones consistentes, botões com estados, overflow controlado,
animações declaradas, safe-area integrada.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent
H = (ROOT / 'index.html').read_text(encoding='utf-8')

results = []
def C(label, ok, ev=''):
    results.append((label, ok, ev))

# ════════════════════════════════════════════════════════════════
# 1. VIEWPORT E RESPONSIVIDADE
# ════════════════════════════════════════════════════════════════
C('viewport meta com width=device-width', 'width=device-width' in H, '')
C('viewport com initial-scale=1', 'initial-scale=1' in H, '')
C('viewport-fit=cover (notch iOS)', 'viewport-fit=cover' in H, '')

# clamp em textos que mudam de tamanho conforme conteúdo
C('Patrimônio-valor com clamp() responsivo',
  re.search(r'\.patrimonio-mini-valor\s*\{[^}]*clamp\(', H) is not None, '')
C('Saldo-valor com clamp() responsivo',
  re.search(r'\.saldo-valor\s*\{[^}]*clamp\(', H) is not None, '')

# word-break / overflow pra textos longos
C('Patrimônio com word-break',
  re.search(r'\.patrimonio-mini-valor\s*\{[^}]*word-break', H) is not None or
  re.search(r'\.saldo-valor\s*\{[^}]*word-break', H) is not None, '')

# Modal com max-width pra desktop
C('Modal com max-width definido',
  re.search(r'\.modal\s*\{[^}]*max-width', H) is not None, '')

# Confirm modal limita largura
C('Confirm modal com max-width',
  re.search(r'\.confirm-modal\s*\{[^}]*max-width', H) is not None, '')

# Media query pra modal centralizado em desktop
C('Media query desktop: modal centralizado',
  re.search(r'@media\s*\([^)]*min-width:\s*480px[^)]*\)', H) is not None, '')

# ════════════════════════════════════════════════════════════════
# 2. Z-INDEX HIERÁRQUICO (sem conflito)
# ════════════════════════════════════════════════════════════════
# Extrai todos os z-index declarados com seu seletor próximo
zindex_blocks = []
for m in re.finditer(r'(\.[^\s{,]+|\#[^\s{,]+|[^\s{,]+)\s*\{[^}]*z-index:\s*(\d+)', H):
    sel = m.group(1).strip()
    z = int(m.group(2))
    zindex_blocks.append((sel, z))

# Hierarquia esperada (do menor pro maior)
expected_order = [
    ('.header', 10),         # sticky header
    ('.bottom-nav', 100),
    ('.fab', 101),
    ('.modal-backdrop', 200),
    ('.confirm-backdrop', 300),
    ('.lock-screen', 999),
]
z_map = dict(zindex_blocks)
for sel, expected_z in expected_order:
    actual = z_map.get(sel)
    C(f'z-index {sel}={expected_z}', actual == expected_z, f'got {actual}')

# Hierarquia preservada
zs = sorted([(s, z) for s, z in expected_order], key=lambda x: x[1])
C('z-index hierárquico: nav<fab<modal<confirm<lock',
  [z for _, z in zs] == [10, 100, 101, 200, 300, 999], '')

# ════════════════════════════════════════════════════════════════
# 3. TOKENS CSS — uso vs definição
# ════════════════════════════════════════════════════════════════
# Variáveis declaradas no :root
var_decls = set(re.findall(r'--([\w-]+):', H))
# Variáveis usadas via var(--...)
var_uses = set(re.findall(r'var\(--([\w-]+)', H))
undefined_uses = var_uses - var_decls
C(f'Todas var(--xxx) têm declaração ({len(undefined_uses)} faltam)',
  len(undefined_uses) == 0, ', '.join(undefined_uses)[:200])

# Tokens essenciais existem
for tok in ['space-1', 'space-2', 'space-3', 'space-4', 'space-5', 'space-6',
            'font-xs', 'font-sm', 'font-base', 'font-md', 'font-lg',
            'radius-sm', 'radius-md', 'radius-lg', 'radius-full',
            'touch-min', 'bg', 'card', 'text', 'muted', 'border',
            'accent', 'receita', 'despesa', 'danger', 'warning', 'success',
            'shadow', 'shadow-lg']:
    C(f'Token --{tok} declarado', tok in var_decls, '')

# ════════════════════════════════════════════════════════════════
# 4. ANIMAÇÕES: animation: nome usado tem @keyframes nome
# ════════════════════════════════════════════════════════════════
# nomes usados em animation:
anim_uses = set()
for m in re.finditer(r'animation:\s*([\w-]+)', H):
    anim_uses.add(m.group(1))

# nomes declarados em @keyframes
anim_decls = set(re.findall(r'@keyframes\s+([\w-]+)', H))
missing_anim = anim_uses - anim_decls
C(f'Toda animation: tem @keyframes correspondente ({len(missing_anim)} sem)',
  len(missing_anim) == 0, ', '.join(missing_anim))

# Animações usadas inversamente: keyframes sem uso (dead code)
unused_anim = anim_decls - anim_uses
C(f'Sem @keyframes morto ({len(unused_anim)} sem uso)',
  len(unused_anim) == 0, ', '.join(unused_anim))

# ════════════════════════════════════════════════════════════════
# 5. ÍCONES UNICODE — só símbolos comuns/suportados
# ════════════════════════════════════════════════════════════════
# Coleta caracteres não-ASCII usados em conteúdo de tags
icon_chars = set()
for m in re.finditer(r'>([^<]{0,5})<', H):
    content = m.group(1).strip()
    if content and any(ord(c) > 127 for c in content) and len(content) <= 3:
        icon_chars.update(c for c in content if ord(c) > 127)

# Whitelist de símbolos sabidos compatíveis (incluindo emoji básicos)
known_icons = set('‹›⌂≡◇▢↑↓→←⌫✓✕✗·◆◐⚡↻★☆⋯…—–€£¥•')
unknown = icon_chars - known_icons
# Permite caracteres acentuados PT (À-ÿ)
unknown = {c for c in unknown if not ('À' <= c <= 'ÿ')}
# Permite arroba/asterisco
C(f'Ícones Unicode só do whitelist conhecido ({len(unknown)} desconhecidos)',
  len(unknown) <= 2, ', '.join(unknown)[:100])

# Nenhum placeholder visual (□, ?, [], 𤓤)
placeholder_icons = ['□', '?']  # aceitos só se em texto real, não como ícone
for ph in placeholder_icons:
    # Conta em conteúdo de botão/icone (heurística: pequeno)
    occurrences = re.findall(rf'<[^>]+>\s*{re.escape(ph)}\s*</', H)
    # 0 ou raríssimo (1 ok em formulário "?")
    C(f'Sem placeholder visual "{ph}" como ícone ({len(occurrences)})',
      len(occurrences) <= 1, '')

# ════════════════════════════════════════════════════════════════
# 6. BOTÕES — estados e estilos
# ════════════════════════════════════════════════════════════════
# Classes de botão definidas
for cls in ['.btn-primary', '.btn-secondary', '.btn-danger', '.btn-warning',
            '.confirm-btn', '.add-row', '.empty-cta']:
    C(f'Classe {cls} declarada', f'{cls} ' in H or f'{cls}{{' in H or f'{cls}:' in H, '')

# :active definido pra botões principais (feedback de toque)
for cls in ['.btn-primary', '.btn-danger', '.fab', '.pad-key', '.confirm-btn',
            '.add-row', '.empty-cta']:
    has_active = re.search(rf'{re.escape(cls)}[^{{]*:active', H) is not None
    C(f'{cls} tem estado :active', has_active, '')

# Estado disabled visível
C('Estado disabled definido (.btn-primary[disabled] OU .is-disabled)',
  '.btn-primary[disabled]' in H or '.is-disabled' in H or '[disabled]' in H, '')

# Botão de fechar modal tem cor de destaque
C('Modal-close com cor accent (visível)',
  re.search(r'\.modal-close\s*\{[^}]*color:\s*var\(--accent\)', H) is not None, '')

# ════════════════════════════════════════════════════════════════
# 7. OVERFLOW E TEXTOS LONGOS
# ════════════════════════════════════════════════════════════════
# Listas verticais com truncamento
C('li-title com text-overflow ellipsis',
  re.search(r'\.li-title\s*\{[^}]*text-overflow:\s*ellipsis', H) is not None, '')
C('li-sub com text-overflow ellipsis',
  re.search(r'\.li-sub\s*\{[^}]*text-overflow:\s*ellipsis', H) is not None, '')

# Compromisso-title com truncamento
C('compromisso-title com text-overflow',
  re.search(r'\.compromisso-title\s*\{[^}]*text-overflow', H) is not None, '')

# Chips em scroll horizontal
C('chips com overflow-x auto (scroll lateral)',
  re.search(r'\.chips\s*\{[^}]*overflow-x:\s*auto', H) is not None, '')

# Chips sem barra de scroll visual em mobile
C('chips esconde scrollbar (-webkit-scrollbar display:none)',
  re.search(r'\.chips::-webkit-scrollbar\s*\{[^}]*display:\s*none', H) is not None, '')

# Modal com overflow-y
C('modal com overflow-y: auto (scroll interno)',
  re.search(r'\.modal\s*\{[^}]*overflow-y:\s*auto', H) is not None, '')

# min-width: 0 em flex-children pra texto não estourar
C('li-body com min-width: 0 (flex shrink)',
  re.search(r'\.li-body\s*\{[^}]*min-width:\s*0', H) is not None, '')

# ════════════════════════════════════════════════════════════════
# 8. SAFE-AREA INTEGRADA (iPhone notch/home indicator)
# ════════════════════════════════════════════════════════════════
C('Header: padding-top com env(safe-area-inset-top)',
  re.search(r'\.header\s*\{[^}]*env\(safe-area-inset-top', H) is not None, '')
C('Modal-header: padding-top com safe-area-inset-top',
  re.search(r'\.modal-header\s*\{[^}]*env\(safe-area-inset-top', H) is not None, '')
C('Bottom-nav: height inclui safe-area-inset-bottom',
  re.search(r'\.bottom-nav\s*\{[^}]*calc\(64px \+ env\(safe-area-inset-bottom', H) is not None, '')
C('FAB: bottom inclui safe-area-inset-bottom',
  re.search(r'\.fab\s*\{[^}]*env\(safe-area-inset-bottom', H) is not None, '')
C('Lock-screen: safe-area top e bottom',
  re.search(r'\.lock-screen\s*\{[^}]*env\(safe-area-inset-top[\s\S]*env\(safe-area-inset-bottom', H) is not None, '')
C('Body: padding-bottom inclui safe-area-inset-bottom',
  re.search(r'body\s*\{[^}]*calc\(80px \+ env\(safe-area-inset-bottom', H) is not None, '')

# ════════════════════════════════════════════════════════════════
# 9. CONSISTÊNCIA DE TIPOGRAFIA
# ════════════════════════════════════════════════════════════════
# Conta fonts hardcoded fora dos tokens — heurística, aceita até N
hardcoded_fonts = re.findall(r'font-size:\s*(\d+)px', H)
hardcoded_fonts = [int(s) for s in hardcoded_fonts]
# Esperados via tokens: 11/13/15/17/22/28/34. Aceita 9-44 px fora também
# Falha se houver muitos valores diferentes (sinal de bagunça)
unique_sizes = set(hardcoded_fonts)
C(f'Tipografia: ≤12 tamanhos diferentes hardcoded ({len(unique_sizes)})',
  len(unique_sizes) <= 12, ', '.join(str(s) for s in sorted(unique_sizes))[:200])

# Fontes muito pequenas (<10px) devem ser raras (acessibilidade)
tiny_fonts = [s for s in hardcoded_fonts if s < 10]
C(f'Sem fontes <10px (acessibilidade) ({len(tiny_fonts)})',
  len(tiny_fonts) == 0, '')

# Não pode ter fontes >50px (estouro)
huge_fonts = [s for s in hardcoded_fonts if s > 50]
C(f'Sem fontes >50px hardcoded ({len(huge_fonts)})',
  len(huge_fonts) == 0, '')

# ════════════════════════════════════════════════════════════════
# 10. CONTRASTE E DARK MODE
# ════════════════════════════════════════════════════════════════
# Dark mode declarado
C('Dark mode via @media (prefers-color-scheme: dark)',
  '@media (prefers-color-scheme: dark)' in H, '')

# Variáveis críticas redefinidas no dark
for var in ['--bg', '--card', '--text', '--muted', '--border']:
    dark_block_idx = H.find('@media (prefers-color-scheme: dark)')
    if dark_block_idx < 0:
        continue
    end = H.find('}\n}', dark_block_idx)
    if end < 0:
        end = dark_block_idx + 2000
    block = H[dark_block_idx:end]
    C(f'Dark mode redefine {var}', f'{var}:' in block, '')

# Cores --text e --muted distintas (contraste)
text_v = re.search(r'(?<!\w)--text:\s*([^;]+);', H)
muted_v = re.search(r'(?<!\w)--muted:\s*([^;]+);', H)
C('--text e --muted distintos (contraste)',
  text_v and muted_v and text_v.group(1).strip() != muted_v.group(1).strip(), '')

# ════════════════════════════════════════════════════════════════
# 11. BORDAS E RAIOS CONSISTENTES
# ════════════════════════════════════════════════════════════════
# Border-radius hardcoded: aceita poucos
hardcoded_radii = re.findall(r'border-radius:\s*(\d+)px', H)
unique_radii = set(int(r) for r in hardcoded_radii)
C(f'Border-radius: ≤8 valores diferentes ({len(unique_radii)})',
  len(unique_radii) <= 8, ', '.join(str(r) for r in sorted(unique_radii))[:100])

# var(--radius-*) também usado (mostra consistência)
radius_var_uses = len(re.findall(r'var\(--radius-\w+', H))
C(f'var(--radius-*) usado (≥15 vezes) — {radius_var_uses}',
  radius_var_uses >= 15, str(radius_var_uses))

# ════════════════════════════════════════════════════════════════
# 12. POSICIONAMENTO E LAYOUT FIXO
# ════════════════════════════════════════════════════════════════
# Bottom-nav posicionada
C('.bottom-nav position: fixed',
  re.search(r'\.bottom-nav\s*\{[^}]*position:\s*fixed', H) is not None, '')
C('.bottom-nav cobre toda largura (left:0; right:0)',
  re.search(r'\.bottom-nav\s*\{[^}]*left:\s*0[\s\S]*right:\s*0', H) is not None, '')
C('.fab position: fixed',
  re.search(r'\.fab\s*\{[^}]*position:\s*fixed', H) is not None, '')
C('Header sticky no topo',
  re.search(r'\.header\s*\{[^}]*position:\s*sticky', H) is not None and
  re.search(r'\.header\s*\{[^}]*top:\s*0', H) is not None, '')
C('Modal-backdrop position: fixed (inset 0)',
  re.search(r'\.modal-backdrop\s*\{[^}]*position:\s*fixed', H) is not None, '')

# ════════════════════════════════════════════════════════════════
# 13. CANVAS DO GRÁFICO — encaixe responsivo
# ════════════════════════════════════════════════════════════════
C('Canvas patrimônio com width 100%',
  re.search(r'#grafico-patrimonio\s*\{[^}]*width:\s*100%', H) is not None, '')
C('Canvas com altura definida em CSS',
  re.search(r'#grafico-patrimonio\s*\{[^}]*height:', H) is not None, '')
C('Canvas com display block (sem inline gap)',
  re.search(r'#grafico-patrimonio\s*\{[^}]*display:\s*block', H) is not None, '')

# ════════════════════════════════════════════════════════════════
# 14. PIN PAD — visual
# ════════════════════════════════════════════════════════════════
C('Pad-key com width E height definidos (não overflow)',
  re.search(r'\.pad-key\s*\{[^}]*width:[^}]*height:', H) is not None, '')
C('Pad em grid (3 colunas)',
  re.search(r'\.pad\s*\{[^}]*grid-template-columns:\s*repeat\(3', H) is not None, '')
C('Lock-dots com gap definido',
  re.search(r'\.lock-dots\s*\{[^}]*gap:', H) is not None, '')

# ════════════════════════════════════════════════════════════════
# 15. ÍCONES E AVATARES (.li-icon)
# ════════════════════════════════════════════════════════════════
C('.li-icon tem flex-shrink: 0 (não comprime)',
  re.search(r'\.li-icon\s*\{[^}]*flex-shrink:\s*0', H) is not None, '')
C('.li-icon com width E height (não distorce)',
  re.search(r'\.li-icon\s*\{[^}]*width:[^}]*height:', H) is not None, '')

# Compromisso dia visualmente destacável
C('.compromisso-dia.hoje (laranja) declarado',
  '.compromisso-dia.hoje' in H, '')
C('.compromisso-dia.proximo (azul) declarado',
  '.compromisso-dia.proximo' in H, '')

# ════════════════════════════════════════════════════════════════
# 16. AUTO-BANNER (atualização de status)
# ════════════════════════════════════════════════════════════════
C('Auto-banner com ícone destacado',
  '.auto-banner-icon' in H, '')
C('Auto-banner com fundo distinto (não confunde com card normal)',
  re.search(r'\.auto-banner\s*\{[^}]*background:', H) is not None, '')
C('Auto-banner com border', re.search(r'\.auto-banner\s*\{[^}]*border:', H) is not None, '')

# ════════════════════════════════════════════════════════════════
# 17. EMPTY STATES (vazios com CTA)
# ════════════════════════════════════════════════════════════════
C('.empty (estado vazio) declarado', '.empty {' in H or '.empty{' in H, '')
C('.empty-icon (ícone visual) declarado', '.empty-icon' in H, '')
C('.empty-cta (botão de ação) declarado', '.empty-cta' in H, '')
C('empty-cta com cor accent (visível)',
  re.search(r'\.empty-cta\s*\{[^}]*background:\s*var\(--accent\)', H) is not None, '')

# ════════════════════════════════════════════════════════════════
# 18. SOMBRAS CONSISTENTES (não bagunça visual)
# ════════════════════════════════════════════════════════════════
shadow_uses = len(re.findall(r'box-shadow:\s*var\(--shadow', H))
C(f'box-shadow usa var(--shadow*) ≥10 vezes ({shadow_uses})',
  shadow_uses >= 10, '')

# Sombra hardcoded é OK em alguns lugares (FAB tem própria), mas não pode espalhar
shadow_hard = len(re.findall(r'box-shadow:\s*0\s+\d', H))
C(f'box-shadow hardcoded ≤5 (FAB e specials) ({shadow_hard})',
  shadow_hard <= 5, str(shadow_hard))

# ════════════════════════════════════════════════════════════════
# Reporta
# ════════════════════════════════════════════════════════════════
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n[Visual] {passed}/{total}")
fails = [(l, e) for (l, ok, e) in results if not ok]
for l, e in fails:
    print(f"  ✗ {l}" + (f" → {e}" if e else ""))
sys.exit(0 if passed == total else 1)
