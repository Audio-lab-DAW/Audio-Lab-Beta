#!/usr/bin/env python3
"""Task DS-P2 (lane A, design round 2, details PN3, PV3 and PG1): piano roll notes, velocity and ghost notes.
   python3 tools/design-lab/ds/ds_p2.py index.html
PN3: notes in the full track colour with a crisp dark edge and a lit top line, the note name inside notes wide enough
(26 px), 600 9 px in dark ink. PV3: the velocity lane shows a bar per note as wide as the note (tinted body, colour edge)
with its value 0 to 127 on bars of 30 px or more; a click or drag anywhere over a bar edits that note (today only near
its start). PG1: other tracks' notes as faint outlines only (no fill), grey or in their colour as the Ghost setting says.
Only the AudioLab look (dsAC3); the other looks keep today's notes. Needs DS-P1 (DQ). Every anchor is asserted.
Re-run on a fresh file after a rebase."""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
assert 'task DS-P2' not in s, 'already applied'
assert 'task DS-P1' in s, 'needs task DS-P1'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

BLOCK = r"""/* task DS-P2 (lane A, design round 2, PN3, PV3, PG1): piano roll notes with a crisp edge, lit top and name inside,
   velocity as bars with their value, other tracks' notes as faint outlines. Drawn with the piano roll (only on change). */
function dsP2Note(g,n,x,y,nw,col){rr(g,x,y+1,nw,PR.rh-2,2);g.fillStyle=col;g.fill();g.strokeStyle='rgba(0,0,0,.4)';g.lineWidth=1;rr(g,x+.5,y+1.5,nw-1,PR.rh-3,2);g.stroke();
  if(nw>5&&PR.rh>=6){g.fillStyle='rgba(255,255,255,.38)';g.fillRect(x+2,y+2,nw-4,1)}}
function dsP2Name(g,n,x,y,nw,col){if(nw<26||PR.rh<11)return;const f=g.font;g.font='600 9px Inter,system-ui,sans-serif';g.fillStyle=n.m?col:'rgba(0,0,0,.72)';g.fillText(dsNN(n.p),x+4,y+PR.rh/2+3.5);g.font=f}
function dsP2Ghost(g,x,y,nw,col){g.globalAlpha=1;g.strokeStyle=UI.ghostGrey?'rgba(236,236,241,.30)':col;if(!UI.ghostGrey)g.globalAlpha=.5;g.lineWidth=1;rr(g,x+1.5,y+2.5,Math.max(1,nw-3),Math.max(1,PR.rh-5),2);g.stroke()}
/* a bar per note in the velocity lane, lower velocities drawn last so every bar stays visible */
function dsP2Vel(g,c,t,w,h,gh){const L=c.notes.map(n=>{const x=KEYW+(n.s-PR.x)*PR.ppb+1,bw=Math.max(3,n.l*PR.ppb-3);return{n,x,bw}}).filter(o=>o.x<w&&o.x+o.bw>KEYW).sort((a,b)=>b.n.v-a.n.v);
  const H=VELH-12,sel=lkT().sel,txt=[];g.font='9.5px Inter,system-ui,sans-serif';g.textBaseline='middle';
  for(const o of L){const n=o.n,top=gh+6+(1-n.v)*H,bh=h-4-top,col=n.sel?sel:t.color;g.globalAlpha=n.m?.35:1;
    g.fillStyle=col;g.globalAlpha=(n.m?.35:1)*.22;g.fillRect(o.x,top,o.bw,bh);g.globalAlpha=n.m?.35:1;g.strokeStyle=col;g.globalAlpha*=.8;g.lineWidth=1;g.strokeRect(o.x+.5,top+.5,o.bw-1,Math.max(0,bh-1));
    g.globalAlpha=n.m?.35:1;g.fillStyle=col;g.fillRect(o.x,top,o.bw,1.5);
    if(o.bw>=30&&bh>=14){const ty=top+8;if(!txt.some(q=>Math.abs(q[0]-o.x)<30&&Math.abs(q[1]-ty)<11)){txt.push([o.x,ty]);g.fillStyle='#ececf1';g.fillText(String(Math.round(n.v*127)),o.x+3,ty)}}}
  g.globalAlpha=1;g.textBaseline='alphabetic'}
/* a click over a bar (not near its start): the notes whose bar is under the pointer, the latest start wins */
function dsP2VelHit(c,x){const b=PR.x+(x-KEYW)/PR.ppb;let hs=c.notes.filter(n=>b>=n.s&&b<n.s+n.l);if(!hs.length)return hs;const m=Math.max(...hs.map(n=>n.s));return hs.filter(n=>n.s===m)}
"""
rep("function askChoice(title,text,btns,icon){", BLOCK + "function askChoice(title,text,btns,icon){")
# ghosts: outlines only
rep("g.globalAlpha=UI.ghostGrey?.12:.22;g.fillRect(x,y+1,nw,PR.rh-2);g.globalAlpha=UI.ghostGrey?.3:.65;g.strokeRect(x+.5,y+1.5,nw-1,PR.rh-3)",
    "if(DQ.on)dsP2Ghost(g,x,y,nw,gc);else{g.globalAlpha=UI.ghostGrey?.12:.22;g.fillRect(x,y+1,nw,PR.rh-2);g.globalAlpha=UI.ghostGrey?.3:.65;g.strokeRect(x+.5,y+1.5,nw-1,PR.rh-3)}")
# notes: crisp edge and lit top
rep("    else{g.globalAlpha=.45+.55*n.v;g.fillStyle=t.color;rr(g,x,y+1,nw,PR.rh-2,2);g.fill();g.globalAlpha=1}",
    "    else if(DQ.on)dsP2Note(g,n,x,y,nw,t.color);else{g.globalAlpha=.45+.55*n.v;g.fillStyle=t.color;rr(g,x,y+1,nw,PR.rh-2,2);g.fill();g.globalAlpha=1}")
# name inside
rep("    if(nw>26&&PR.rh>=12){g.fillStyle=n.m?t.color:'#0b0b0e';g.fillText(nname(n.p),x+4,y+PR.rh/2+3.5)}",
    "    if(DQ.on)dsP2Name(g,n,x,y,nw,t.color);else if(nw>26&&PR.rh>=12){g.fillStyle=n.m?t.color:'#0b0b0e';g.fillText(nname(n.p),x+4,y+PR.rh/2+3.5)}")
# velocity lane
rep("  for(const n of c.notes){const x=KEYW+(n.s-PR.x)*PR.ppb+1,top=gh+6+(1-n.v)*(VELH-12);",
    "  if(DQ.on)dsP2Vel(g,c,t,w,h,gh);else for(const n of c.notes){const x=KEYW+(n.s-PR.x)*PR.ppb+1,top=gh+6+(1-n.v)*(VELH-12);")
# velocity edit over the whole bar
rep("let hits=o.c.notes.filter(n=>Math.abs(KEYW+(n.s-PR.x)*PR.ppb-x)<5);",
    "let hits=o.c.notes.filter(n=>Math.abs(KEYW+(n.s-PR.x)*PR.ppb-x)<5);if(!hits.length&&dsAC3())hits=dsP2VelHit(o.c,x);")
open(F, 'w', encoding='utf-8').write(s)
print('task DS-P2 applied')
