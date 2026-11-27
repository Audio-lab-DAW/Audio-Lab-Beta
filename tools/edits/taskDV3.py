#!/usr/bin/env python3
"""Task DV-3 (display-first devices, step 3: On the picture and the Pro EQ): python3 tools/edits/taskDV3.py index.html 0.290
New JS before askChoice, new CSS before .dacv; four small asserted changes inside lane I's own DV-1 block (the engine takes the chips as faces,
pictures are refreshed only while something moves, a tap on a chip does not toggle hover reveal). Every replacement asserted unique; running it twice changes nothing."""
import sys, os, re
F = sys.argv[1]; VER = sys.argv[2]
D = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if '(task DV-3)' in s:
    print('already applied'); sys.exit(0)
assert '(task DV-1)' in s and '(task DV-2)' in s, 'DV-1 and DV-2 first'
BLOCK = open(os.path.join(D, 'taskDV3_block.js'), encoding='utf-8').read().replace('v0.276', 'v' + VER)
CSS = open(os.path.join(D, 'taskDV3_css.txt'), encoding='utf-8').read().replace('v0.276', 'v' + VER)
old = re.findall(r"VERSION='(\d+\.\d+)'", s); assert len(old) == 1, old
assert tuple(map(int, VER.split('.'))) > tuple(map(int, old[0].split('.'))), (old, VER)
def rep(a, b):
    global s
    n = s.count(a); assert n == 1, (a[:70], n); s = s.replace(a, b)
# DV-1's engine: chips (.dvface) are faces too, with their own kind and radius
rep("for(const R of fi.querySelectorAll(':scope>.dev.dvf>.devb>.dvrail')){if(R.hidden)continue;",
    "for(const R of fi.querySelectorAll(':scope>.dev.dvf>.devb>.dvrail,:scope>.dev.dvf>.devb>.dvface')){if(R.hidden)continue;")
rep("g.addPanel({id,rect,radius:12,kind:'window',over:'flats'", "g.addPanel({id,rect,radius:R._dvgRad||12,kind:R._dvgKind||'window',over:'flats'")
# pictures under glass: refreshed while playing, and for two seconds after something changed or the song stopped; nothing at rest
# which pictures lie under a rail: those are refreshed 20 times a second while playing; a picture under small chips only (On the picture) is
# refreshed while something is being changed (10 a second) and once more after the song stops, so a live display under chips costs nothing while it plays
rep("const o=c.getBoundingClientRect(),seen=new Set(),fseen=new Set();", "DVG.fr=new Set();const o=c.getBoundingClientRect(),seen=new Set(),fseen=new Set();")
rep("fseen.add(fk);", "fseen.add(fk);if(!R._dvgKind)DVG.fr.add(fk);")
rep("if(DVG.flats.size&&now-DVG.fT>(play&&play.on?50:500)){DVG.fT=now;for(const k of DVG.flats.keys()){DVG.g.markFlatDirty(k);DVG.n.flatDirty++}}",
    "const dvLive=!!(play&&play.on),dvHot=now<DVG.hot+2000;if(dvLive)DVG.pT=now;const dvSettle=!dvLive&&now<(DVG.pT||0)+2000;\n"
    "  if(DVG.flats.size&&(dvLive||dvHot||dvSettle)&&now-DVG.fT>(dvLive?50:500)){DVG.fT=now;const fr=DVG.fr||new Set();DVG.fN=(DVG.fN||0)+1;"
    "for(const k of DVG.flats.keys()){if(dvLive&&!fr.has(k)&&!(dvHot&&DVG.fN%2===0))continue;DVG.g.markFlatDirty(k);DVG.n.flatDirty++}}")
# only the frame's own fades keep the page being read: the meters' transitions inside the devices (dozens a second while playing) no longer do
rep("for(const ty of['scroll','mouseover','mouseout','focusin','focusout','transitionend'])fi.addEventListener(ty,()=>dvgDirty(),{capture:true,passive:true})}",
    "for(const ty of['scroll','mouseover','mouseout','focusin','focusout'])fi.addEventListener(ty,()=>dvgDirty(),{capture:true,passive:true});\n"
    " fi.addEventListener('transitionend',e=>{const q=e.target;if(q&&q.matches&&q.matches('.dvrail,.dvface,.dfs,.eqside,.dug,.dvval'))dvgDirty()},{capture:true,passive:true})}")
rep("tg.closest('.dfs,.eqside,.dug,.dvtr,.devh')", "tg.closest('.dfs,.eqside,.dug,.dvtr,.devh,.dvface')")
rep('function askChoice(title,text,btns,icon){', BLOCK.rstrip('\n') + '\nfunction askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;', CSS.rstrip('\n') + '\n.dacv{display:flex;')
rep("VERSION='%s'" % old[0], "VERSION='%s'" % VER)
open(F, 'w', encoding='utf-8').write(s); print('task DV-3 applied to', F, 'version', VER)
