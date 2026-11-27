"""Task IN-C and IN-D (lane E, instruments): the CPU graph, the user's pick C1 (load against budget), and the device previews, pick D1
(scope preview). Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/design-lab/in/in_cd.py [index.html]
Does:
  1. adds the block (in_cd_block.js) before askChoice: INC (C1) and IND (D1); one CSS line before .dacv
  2. cpuFrame: INC.tick every 100 ms; the button's graph drawn by INC.btn (budget tick, red only above 75 %)
  3. cpuPopFill: the pop-up keeps INC's large graph under its title (INC.pop after the pop-up's HTML is set)
  4. Soft Clipper: its waveform pane (and transfer dot) drawn by IND.clip (D1); Bitcrusher: IND.crush after its staircase
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane E (task IN-C and IN-D)' in s:
    print('IN-C/IN-D already applied'); sys.exit(0)
assert '/* ===== lane E (task IN-A)' in s, 'IN-A must be in first'

def rep(s, old, new, n=1):
    c = s.count(old)
    assert c == n, (old[:100], c, n)
    return s.replace(old, new)

s = rep(s, "if(now-CPU.last<100)return;CPU.last=now;", "if(now-CPU.last<100)return;CPU.last=now;INC.tick(now,load);/* IN-C */")
s = rep(s, "g.fillStyle='#050608';g.fillRect(0,0,w,h);g.beginPath();for(let k=0;k<120;k++){const v=CPU.hist[(CPU.i+1+k)%120],x=k/119*w,y=h-1-v*(h-2);k?g.lineTo(x,y):g.moveTo(x,y)}g.lineTo(w,h);g.lineTo(0,h);g.closePath();g.fillStyle=bad?'rgba(255,77,77,.5)':'rgba(62,207,142,.35)';g.fill();",
        "INC.btn(g,w,h);/* IN-C: C1, red only above the budget */")
s = rep(s, "{const P=$('#cpuPop');if(P._h!==_ph){P._h=_ph;P.innerHTML=_ph}}", "{const P=$('#cpuPop');if(P._h!==_ph){P._h=_ph;P.innerHTML=_ph}INC.pop(P)/* IN-C */}")
i = s.find("  if(X&&X.anI){const a=tdOf(X.anI),o=tdOf(X.anO)"); assert i > 0 and s.count("  if(X&&X.anI){const a=tdOf(X.anI),o=tdOf(X.anO)") == 1
E = "'rgba(255,255,255,.35)',9)}\n"; j = s.find(E, i); assert 0 < j - i < 1400, j - i
s = s[:i] + "  if(X&&X.anI)IND.clip(g,w,h,f,X,{ox,oy,S2,R,sx,sy,b});/* IN-D: D1 */\n" + s[j + len(E):]
s = rep(s, "glow(g,'#ff6b6b',8);g.strokeStyle='#ff6b6b';g.lineWidth=2;g.stroke();g.restore();g.shadowBlur=0},",
        "glow(g,'#ff6b6b',8);g.strokeStyle='#ff6b6b';g.lineWidth=2;g.stroke();g.restore();g.shadowBlur=0;IND.crush(g,w,h,f,X,T,Bm,N,dr)/* IN-D: D1 */},")
s = rep(s, ".dacv{display:flex;", "#cpuPop .incC{display:block;width:100%;height:98px;margin:8px 0 2px}/* IN-C */\n.dacv{display:flex;")
js = open(os.path.join(HERE, 'in_cd_block.js'), encoding='utf-8').read()
s = rep(s, "function askChoice(title,text,btns,icon){", js + "function askChoice(title,text,btns,icon){")
open(P, 'w', encoding='utf-8').write(s)
print('IN-C/IN-D applied')
