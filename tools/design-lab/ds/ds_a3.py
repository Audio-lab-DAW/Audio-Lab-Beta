#!/usr/bin/env python3
"""Task DS-A3 (lane A, design round 2, detail AC3): clips without a title band.
   python3 tools/design-lab/ds/ds_a3.py index.html
The name sits on the clip body in a lighter tone of the track colour, a 2 px colour edge on top, a one-device-pixel colour
hairline on the left, a darker body (the clip opacity setting times 0.42, so the default 36 % gives 15 %, as on the pick page).
Only the AudioLab look: the other looks (Live, FL, Cubase, Logic, Bitwig ... styles) keep their own title bars.
Geometry and hit areas are unchanged (clipGeom keeps its 14 px top zone, now for the name), so dragging, fades, gain and
envelopes work as before. The glass engine's rectangle list (gleBuild) follows: same body alpha, the edge instead of the band.
Every anchor is asserted. Re-run on a fresh file after a rebase."""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
assert 'task DS-A3' not in s, 'already applied'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

BLOCK = r"""/* task DS-A3 (lane A, design round 2, AC3): clips without a title band. Functions only (hoisted), so a drawing that runs before
   this line still finds them. dsAC3(): the AudioLab look is on (the other looks keep their title bars). dsBody(): the factor on
   the clip opacity setting (0.42: the default 36 % gives the pick page's 15 % body). */
function dsAC3(){try{return thGet().id==='audiolab'}catch(e){return true}}
function dsBody(){return dsAC3()?.42:1}
function dsClipName(g,c,G,col,mu,lx){const ln=shade(col,.45),label=(mu?'muted · ':'')+c.name,by=G.y+12,F1='600 11px Inter,system-ui,sans-serif',F2='500 9px Inter,system-ui,sans-serif';
  g.font=F1;g.fillStyle=ln;g.fillText(label,lx,by);const tw=g.measureText(label).width,vw=G.x+G.w-lx;
  const meta=c.notes?`${c.notes.length} notes · ${Math.round(c.len/4)} bars`:`${Math.round(c.len/4*10)/10} bars`;g.font=F2;const mw=g.measureText(meta).width,room=vw>tw+mw+30;
  g.globalAlpha=.6;if(room)g.fillText(meta,G.x+G.w-mw-7,by-.5);
  if(c.notes&&vw>tw+30){const ix=G.x+G.w-(room?mw+20:12);for(let k=0;k<3;k++)g.fillRect(ix+k*3,G.y+5+(k%2)*3,2,5-(k%2)*3)}g.globalAlpha=1}
function dsClipEdge(g,G,col,mu){const d=(window.devicePixelRatio||1)*ZOOM,hp=1/d,e2=Math.max(1,Math.round(2*d))/d;g.fillStyle=col;
  g.globalAlpha=mu?.3:.5;g.fillRect(G.x,G.y,hp,G.h);g.globalAlpha=mu?.5:1;g.fillRect(G.x,G.y,G.w,e2);g.globalAlpha=1}
"""
rep('function askChoice(title,text,btns,icon){', BLOCK + 'function askChoice(title,text,btns,icon){')

# drawClip: darker body, no outline (left hairline instead), no white lit line (colour edge instead), name on the body
rep("CA=(UI.clipA??36)/100,thin=V.ppb<8;", "CA=(UI.clipA??36)/100*dsBody(),DS3=dsAC3(),thin=V.ppb<8;")
rep("g.strokeStyle=col;g.globalAlpha=mu?.3:thin?.45:.7;g.lineWidth=thin?.6:1;g.strokeRect(G.x+.5,G.y+.5,G.w-1,G.h-1);g.globalAlpha=1;",
    "if(!DS3){g.strokeStyle=col;g.globalAlpha=mu?.3:thin?.45:.7;g.lineWidth=thin?.6:1;g.strokeRect(G.x+.5,G.y+.5,G.w-1,G.h-1);g.globalAlpha=1}")
rep("if(!thin){g.fillStyle='rgba(255,255,255,.14)';g.fillRect(G.x,G.y,G.w,1)}}",
    "if(!thin&&!DS3){g.fillStyle='rgba(255,255,255,.14)';g.fillRect(G.x,G.y,G.w,1)}}\n  if(DS3)dsClipEdge(g,G,col,mu);")
rep("  if(G.top){const hb=TH.hd==='none'", "  if(G.top&&DS3)dsClipName(g,c,G,col,mu,lx);\n  else if(G.top){const hb=TH.hd==='none'")

# glass engine rectangle list: same body, the colour edge instead of the band
rep("CA=(UI.clipA??36)/100,th=V.th,top=th>=40?14:0", "CA=(UI.clipA??36)/100*dsBody(),DS3=dsAC3(),th=V.th,top=th>=40?14:0")
rep("if(top&&TH.hd!=='none')clips.push(", "if(DS3)clips.push({x,y:y+2,w:c.len,h:2,color:q,alpha:mu?.5:1,titleH:0});else if(top&&TH.hd!=='none')clips.push(")

open(F, 'w', encoding='utf-8').write(s)
print('task DS-A3 applied to', F)
