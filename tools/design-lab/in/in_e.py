"""Task IN-E (lane E, instruments): the EQ displays, the user's pick E3 (bandwidth calipers).
Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/design-lab/in/in_e.py [index.html]
Does:
  1. adds the IN-E block (in_e_block.js) before askChoice: INSE (colours and the marks of one draw), ineBW (a bandwidth measured on a
     response), ineCaliper, ineCorners, ineAnaScale, ineBand, ineFill, ineMarks, ineFiltMarks, ineVizFilter, ineAfilt
  2. Pro EQ (vizEQ2): the gain scale on the left in the gain colour, the analyzer's dBFS scale and tilt on the right, the fill between the
     summed curve and 0 dB, a caliper under each bell (band-pass, notch), corner marks on shelves and cuts, note and octaves in the read-out
  3. Filter (vizFilter) and Auto Filter: the fill to 0 dB, the corner mark or caliper
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane E (task IN-E)' in s:
    print('IN-E already applied'); sys.exit(0)
assert '/* ===== end of lane E IN-S' in s, 'IN-S must be in first'

def rep(s, old, new, n=1):
    c = s.count(old)
    assert c == n, (old[:80], c, n)
    return s.replace(old, new)

# 2. Pro EQ
s = rep(s, "function vizEQ2(g,w,h,f,X){const p=f.p,sel=eqSel(f),R=24,dy=db=>h/2-db/R*(h/2-12),gs=(p.gs??100)/100;",
        "function vizEQ2(g,w,h,f,X){const p=f.p,sel=eqSel(f),R=24,dy=db=>h/2-db/R*(h/2-12),gs=(p.gs??100)/100;INSE.bw=[];INSE.cal=[];INSE.corner=[];/* IN-E */")
s = rep(s, "g.fillStyle='rgba(255,255,255,.3)';g.fillText((db>0?'+':'')+db,w-20,y-2)}",
        "g.fillStyle=db?INSE.gain:INS.look().ink;g.fillText(INS.num(db,0,true),3,y-2)}/* IN-E: the gain scale on the left, in its colour */")
s = rep(s, "sp(X.an,gr,'rgba(120,200,255,.45)')}", "sp(X.an,gr,'rgba(120,200,255,.45)');ineAnaScale(g,w,h)}")
s = rep(s, "g.strokeStyle=col+(hot?'ee':'70');g.lineWidth=hot?1.4:1;g.stroke();", "g.strokeStyle=col+(hot?'ee':'70');g.lineWidth=hot?1.4:1;g.stroke();ineBand(i,b,M2,n,w,dy);")
s = rep(s, "  const og=Math.pow(10,(p.out||0)/20);g.beginPath();", "  ineFill(g,p,n,dy);/* IN-E: E3 */const og=Math.pow(10,(p.out||0)/20);g.beginPath();")
s = rep(s, "g.strokeStyle='#ffd27a';g.lineWidth=2;g.stroke();g.restore();", "g.strokeStyle='#ffd27a';g.lineWidth=2;g.stroke();g.restore();ineMarks(g,w,h);")
s = rep(s, "${EQT[b.t]} · ${fmt(b.f,'Hz')}", "${EQT[b.t]} · ${fmt(b.f,'Hz')} ${INS.note(b.f).name}")
s = rep(s, ":' · Q '+b.q.toFixed(2)}", ":' · Q '+b.q.toFixed(2)+(INSE.bw[show]?' · '+ineOct(INSE.bw[show]):'')}")
# 3. Filter and Auto Filter
s = rep(s, "g.lineTo(w,h);g.lineTo(0,h);g.closePath();g.fillStyle='rgba(62,207,142,.14)';g.fill();",
        "g.lineTo(w,dbY(0));g.lineTo(0,dbY(0));g.closePath();g.fillStyle='rgba(62,207,142,.14)';g.fill();/* IN-E: the fill to 0 dB */")
s = rep(s, "g.fillText('10k',Math.log(500)/Math.log(1000)*w+3,h-4)}", "g.fillText('10k',Math.log(500)/Math.log(1000)*w+3,h-4);ineVizFilter(g,w,h,p)}")
s = rep(s, "g.lineTo(w,Bm);g.lineTo(0,Bm);g.closePath();g.fillStyle='rgba(245,200,76,.16)';g.fill();",
        "g.lineTo(w,Yd(0));g.lineTo(0,Yd(0));g.closePath();g.fillStyle='rgba(245,200,76,.16)';g.fill();/* IN-E: the fill to 0 dB */")
s = rep(s, "glow(g,'#f5c84c',7);g.strokeStyle='#f5c84c';g.lineWidth=2.2;g.stroke();g.shadowBlur=0;",
        "glow(g,'#f5c84c',7);g.strokeStyle='#f5c84c';g.lineWidth=2.2;g.stroke();g.shadowBlur=0;ineAfilt(g,p,fr,mg,N,w,Yd,Bm,m);")

# 1. the block
js = open(os.path.join(HERE, 'in_e_block.js'), encoding='utf-8').read()
s = rep(s, "function askChoice(title,text,btns,icon){", js + "function askChoice(title,text,btns,icon){")
open(P, 'w', encoding='utf-8').write(s)
print('IN-E applied')
