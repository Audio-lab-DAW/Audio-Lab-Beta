"""Task IN-L (lane E, instruments): loudness, the user's pick L2 (the loudness history).
Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/design-lab/in/in_l.py [index.html]
Does:
  1. adds the IN-L block (in_l_block.js) before askChoice: INS.lhist (the one history drawer), INL (the master's momentary and short-term, 10 a second,
     60 s), the pop-up graph (10 a second while open), the top-bar graph, the mixer master box graph (wraps mxsMaster), the Meter device's history
     (msuHist through the drawer), the LRA settling count
  2. CSS before .dacv: the master box graph in place of its target bar
  3. the pop-up's and the top-bar box's own graph drawing go to the drawer; the Loudness device's history area draws through the drawer on its own
     scale (the dragged target line stays); LRA settling in the Loudness and Meter devices
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane E (task IN-L)' in s:
    print('IN-L already applied'); sys.exit(0)
assert '/* ===== end of lane E IN-A' in s, 'IN-A must be in first'

def rep(s, old, new, n=1):
    c = s.count(old)
    assert c == n, (old[:80], c, n)
    return s.replace(old, new)

def cut(s, a, b, new):
    """replace from the unique start a up to (not including) the unique end b that follows it"""
    assert s.count(a) == 1, ('start', a[:70], s.count(a))
    i = s.index(a); j = s.index(b, i); assert s.count(b) == 1, ('end', b[:70], s.count(b))
    return s[:i] + new + s[j:]

# 3a. the top-bar box's graph
s = cut(s, "{const cv=b.querySelector('.lfgr');if(cv&&cv.offsetParent){const{g,w,h}=fit(cv)", "const pos=v=>clamp((v+40)/40,0,1)*100;",
        "{const cv=b.querySelector('.lfgr');if(cv&&cv.offsetParent)inlTop(cv)}/* IN-L: L2 */\n    ")
# 3b. the pop-up's graph
s = cut(s, "  const cv=$('#lmC');const{g,w,h}=fit(cv),y=v=>8+(1-clamp((v+36)/36,0,1))*(h-16);", "setInterval(lmPaint,250);",
        "  inlPop()}/* IN-L: L2, the loudness history (also redrawn 10 times a second while the pop-up is open) */\n")
# 3c. the Loudness device: history area and LRA settling
s = cut(s, "g.save();g.beginPath();g.rect(GX,0,GW,h);g.clip();for(const db of[-40,-30,-20,-10,0])", "g.restore();const tyT=ty(p.target);",
        "g.save();g.beginPath();g.rect(GX,0,GW,h);g.clip();/* IN-L: L2 on the device's own scale (-40 to 0 LUFS, which the dragged target line uses) */"
        "{const H=X?X.H:[];INS.lhist(g,GX,10,GW,h-26,{lo:-40,hi:0,target:p.target,n:H.length,span:600,dt:.1,M:i=>H[i].M,S:i=>H[i].S,I:m.I,step:10,major:10,rel:false,labIn:true,fs:8,tlab:'in',legend:false})}\n  ")
s = rep(s, "txt(g,'LRA '+m.LRA.toFixed(1)+' LU',10,h-8,'#b583ff',10);",
        "{const stl=inlSettle(X&&X.H)<600;txt(g,'LRA '+m.LRA.toFixed(1)+' LU',10,h-8,stl?'rgba(181,131,255,.45)':'#b583ff',10)}/* IN-L: dim while the range settles (60 s, EBU Tech 3341) */")
# 3d. the Meter device's LRA row
s = rep(s, "row('Range (LRA)',X.I>-69?X.LRA.toFixed(1)+' LU':'–');",
        "row('Range (LRA)',X.I>-69?X.LRA.toFixed(1)+' LU'+(X.hn<600?' settling':''):'–',X.I>-69&&X.hn<600?MSUC.dim:null);/* IN-L: settling for 60 s (EBU Tech 3341) */")

# 2. CSS
css = ".mxme .mxtg .mxbar{display:none}.mxme .mxtg canvas.inlh{display:block;width:100%;height:16px;margin-top:3px;border-radius:3px;background:#181a21}\n"
s = rep(s, ".dacv{display:flex;", css + ".dacv{display:flex;")

# 1. the block
js = open(os.path.join(HERE, 'in_l_block.js'), encoding='utf-8').read()
s = rep(s, "function askChoice(title,text,btns,icon){", js + "function askChoice(title,text,btns,icon){")
open(P, 'w', encoding='utf-8').write(s)
print('IN-L applied')
