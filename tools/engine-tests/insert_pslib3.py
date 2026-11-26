"""Puts the preset library part 3 block (effects) into index.html: python3 insert_pslib3.py index.html block.js
Every replaced string must occur exactly once. Running it again replaces the block between the markers."""
import sys, re
p, bp = sys.argv[1], sys.argv[2]
s = open(p, encoding='utf-8').read(); blk = open(bp, encoding='utf-8').read().rstrip('\n') + '\n'
def rep(old, new):
    global s
    n = s.count(old); assert n == 1, (n, old[:80]); s = s.replace(old, new)
if '/*PSLIB3-START*/' in s:
    i = s.index('/*PSLIB3-START*/'); j = s.index('/*PSLIB3-END*/') + len('/*PSLIB3-END*/\n'); s = s[:i] + blk + s[j:]
else:
    rep('function askChoice(title,text,btns,icon){', blk + 'function askChoice(title,text,btns,icon){')
    rep('psLib2();/* preset library, part 2 (defined before askChoice) */', 'psLib2();/* preset library, part 2 (defined before askChoice) */\nfxLib();/* preset library, part 3: effects (defined before askChoice) */')
    # preset menus: tooltips per entry, hidden near copies left out (unless in use); the Pro EQ menu too
    rep("function preOpts(O,cur){const G=new Map();for(const[k,v]of Object.entries(O)){const i=v[0].indexOf('|'),g=i<0?'Basics':v[0].slice(0,i),n=i<0?v[0]:v[0].slice(i+1);if(!G.has(g))G.set(g,[]);G.get(g).push(`<option value=\"${k}\"${cur===k?' selected':''}>${esc(n)}</option>`)}",
        "function preOpts(O,cur){let ty=O===EQPRE?'eq':null;if(!ty)for(const t in FXPRE)if(FXPRE[t]===O){ty=t;break}const M=(ty&&FXMETA[ty])||{};const G=new Map();for(const[k,v]of Object.entries(O)){if(M[k]&&M[k].h&&cur!==k)continue;const i=v[0].indexOf('|'),g=i<0?'Basics':v[0].slice(0,i),n=i<0?v[0]:v[0].slice(i+1);if(!G.has(g))G.set(g,[]);const tp=ty?fxTip(ty,k):'';G.get(g).push(`<option value=\"${k}\"${cur===k?' selected':''}${tp?` title=\"${esc(tp)}\"`:''}>${esc(n)}${M[k]&&M[k].psy&&g!=='Psytrance'?' · psy':''}</option>`)}")
    # chord shapes grouped with tooltips
    rep("<select data-x=\"cp\" aria-label=\"Chord shape\">${Object.entries(CHPRE).map(([k,v])=>`<option value=\"${k}\"${k===f.p.cp?' selected':''}>${v[0]}</option>`).join('')}",
        "<select data-x=\"cp\" aria-label=\"Chord shape\">${chOpts(f.p.cp)}")
    # choosing a preset copies its values (before, the effect shared arrays such as drawn shapes with the preset table)
    rep("if(el.dataset.x==='pre'){Object.assign(f.p,FXPRE[f.type][el.value][1]);f.p.pre=el.value}",
        "if(el.dataset.x==='pre'){Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE[f.type][el.value][1])));f.p.pre=el.value}")
open(p, 'w', encoding='utf-8').write(s); print('ok', len(s))
