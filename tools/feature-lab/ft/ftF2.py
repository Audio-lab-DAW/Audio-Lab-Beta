#!/usr/bin/env python3
"""Task FT-F2 (lane C): arranger moves. Anchored edit; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftF2.py [index.html] [version]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
VER = sys.argv[2] if len(sys.argv) > 2 else None
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-F2)' in s: sys.exit('already applied')
assert 'task FT-F1' in s, 'needs FT-F1'
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)
# 1. the block, after FT-F1's
a = "FT_HOOKS.clipLinks={group:id=>lkGroup(id).map(x=>x.c.id),linkedCopy:id=>{const f=findClip(id);if(f)lkDup(f.t,f.c)},unique:id=>{const f=findClip(id);return f?lkUnique([f]):0},sync:()=>lkSweep()};\n"
blk = open(os.path.join(H, 'ftF2_block.js'), encoding='utf-8').read().rstrip('\n')
if VER: blk = blk.replace('/* v0.262 (task FT-F2)', '/* v%s (task FT-F2)' % VER, 1)
rep(a, a + blk + "\n")
# 2. dragging a section: Alt copies
rep("if(ad.mode==='move'){const want=ad.s0+(b-ad.b0),bd=[...new Set((S.sections||[]).flatMap(q=>[q.start,q.start+q.len]).concat([0]))].filter(q=>q<ad.s0-1e-6||q>ad.s0+ad.l0+1e-6);let best=null,bv=1e9;for(const q of bd){const tgt=q>ad.s0?q-ad.l0:q,dd=Math.abs(tgt-want);if(dd<bv){bv=dd;best=q}}ad.dst=best;PREVT=null;PREVMAP=best==null?null:rippleMap(ad.s0,ad.l0,best);dirty=true;return}",
    "if(ad.mode==='move'){ftAmDrag(ad,b,e);return}")
rep("const xd=X0+((ad.dst>ad.s0?ad.dst-ad.l0:ad.dst)-V.x)*V.ppb;g.fillStyle='#fff';g.fillRect(xd-1,sy,2,h-sy)",
    "const xd=X0+((ad.cp?ad.dst:ad.dst>ad.s0?ad.dst-ad.l0:ad.dst)-V.x)*V.ppb;g.fillStyle='#fff';g.fillRect(xd-1,sy,2,h-sy);if(ad.cp)ftAmGhost(g,xd,sy,ad)")
# 3. the drop: move or copy with the automation, tempo and signatures
rep("if(a2.dst!=null&&rippleMove(a2.s0,a2.l0,a2.dst,S.tracks))toast(`Moved “${a2.sc.name}”. The rest of the song moved out of the way.`);changed(false);return}",
    "if(a2.dst!=null)ftAmDrop(a2);else changed(false);return}")
# 4. the section menu and the empty strip's menu
rep("'-',{label:'Delete section',danger:1,act:()=>{pushUndo();S.sections=S.sections.filter(q=>q!==sc);",
    "...ftAmSecItems(sc),'-',{label:'Remove the marker only',sub:'The music stays where it is',act:()=>{pushUndo();S.sections=S.sections.filter(q=>q!==sc);")
rep("{label:'Loop the whole song',dis:!S.loopRange,act:()=>{S.loopRange=null;syncTransportUI();changed(false)}},'-',{label:(UI.tempoLane",
    "{label:'Loop the whole song',dis:!S.loopRange,act:()=>{S.loopRange=null;syncTransportUI();changed(false)}},{label:'Insert empty bars here…',act:()=>ftAmInsertAsk(b)},'-',{label:(UI.tempoLane")
# 5. three commands in the registry, before Duplicate clip
cmds = (" {id:'arr.secDup',g:'edit',l:'Duplicate the section at the playhead',d:'',ic:'M3 6h7v8H3zM10 6h7v8h-7',run:()=>ftAmCmd('dup')},\n"
        " {id:'arr.insertBars',g:'edit',l:'Insert empty bars at the playhead…',d:'',ic:'M10 4v12M4 7v6M16 7v6M7 10h6',run:()=>ftAmInsertAsk(play.on?curDisp():pos)},\n"
        " {id:'arr.secDelete',g:'edit',l:'Delete the section at the playhead and close the gap',d:'',ic:'M4 6h12M7 6V4h6v2M6 6l1 10h6l1-10',run:()=>ftAmCmd('del')},\n")
a = " {id:'dup',g:'edit',l:'Duplicate clip',"
rep(a, cmds + a)
open(F, 'w', encoding='utf-8').write(s); print('FT-F2 applied')
