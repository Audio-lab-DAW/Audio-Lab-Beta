"""Task IN-M (lane E, instruments): level meters, the user's pick M2 (peak and RMS in one bar).
Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/design-lab/in/in_m.py [index.html]
Does:
  1. adds the IN-M block (in_m_block.js) before askChoice: INS.pr (300 ms window: RMS AES17, highest sample, crest), INS.mbar (the one bar
     drawer for canvas meters, for DS-T2's TM1 to reuse), INM (the core as a veil on the page-element meters, read-outs), and wraps of
     mtrPeak (the same new samples feed the window), drawMixer, trackMeters, meters and mtrPv (veils and read-outs after their own drawing)
  2. the CSS for the master strip's RMS and crest box and the Settings preview read-outs, before .dacv
  3. the canvas meters draw through INS.mbar: the transport meter (#mtr), the mixer's meter view and the Settings preview (#mtrBigC);
     the mixer's meter view and the Settings preview now follow the fader taper (like the fader meters), with the M1 scale (INS.scaleTaper)
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane E (task IN-M)'
if MARK in s:
    print('IN-M already applied'); sys.exit(0)
assert '/* ===== end of lane E IN-A' in s, 'IN-A must be in first'

def rep(s, old, new, n=1):
    c = s.count(old)
    assert c == n, (old[:80], c, n)
    return s.replace(old, new)

# 3a. the transport meter: peak faint above the RMS core; the cache key includes the core
s = rep(s, "  const bar=(d,y)=>{const x1=sx(d);g.fillStyle=meters.gr;g.fillRect(0,y,x1,bh)};\n  bar(MT2.l,2);bar(MT2.r,3+bh);",
           "  const bar=(d,y,an)=>INS.mbar(g,0,y,w,bh,sx(d)/w,INM.rfr(an,v=>sx(v)/w),meters.gr,true);/* IN-M: M2, the RMS core */\n  bar(MT2.l,2,anL);bar(MT2.r,3+bh,anR);")
s = rep(s, "'|'+Math.round(sx(MT2.hr)*4),same=mk===meters.k;",
           "'|'+Math.round(sx(MT2.hr)*4)+'|'+Math.round(INM.rfr(anL,v=>sx(v))*4)+'|'+Math.round(INM.rfr(anR,v=>sx(v))*4),same=mk===meters.k;")

# 3b. the mixer's meter view: the fader taper, the RMS core, the M1 scale
s = rep(s, "const sy=d=>H-clamp((d+60)/66,0,1)*H,bw=(W-14)/2;for(const[k,v,hd] of[[0,H0.pl,H0.hl],[1,H0.pr,H0.hr]]){",
           "const sy=d=>H-dbN(d)*H,bw=(W-14)/2;/* IN-M: the fader taper (was linear) */for(const[k,v,hd] of[[0,H0.pl,H0.hl],[1,H0.pr,H0.hr]]){")
s = rep(s, "g.fillStyle='#14161c';g.fillRect(x,0,bw,H);g.fillStyle=gr;g.fillRect(x,sy(v),bw,H-sy(v));if(hd>-59)",
           "g.fillStyle='#14161c';g.fillRect(x,0,bw,H);INS.mbar(g,x,0,bw,H,dbN(v),INM.rfr(k?aR:aL,dbN),gr);if(hd>-59)")
s = rep(s, "if(mxOpt('meter','ticks')){g.fillStyle='rgba(255,255,255,.25)';for(const d of[0,-6,-12,-24,-48])g.fillRect(2,sy(d),3,1)}}",
           "if(mxOpt('meter','ticks'))INS.scaleTaper(g,5,0,H,{lab:false})}")

# 3c. the Settings preview: the fader taper, the core, the scale
s = rep(s, "hold=+o.hold,top=6,bot=H-16,sy=d=>bot-clamp((d+60)/66,0,1)*(bot-top);",
           "hold=+o.hold,top=6,bot=H-16,sy=d=>bot-dbN(d)*(bot-top);/* IN-M: the fader taper */")
s = rep(s, "for(let i=0;i<=10;i++)gr.addColorStop(i/10,heatCol(i/10));g.fillStyle=gr;g.fillRect(x,y,bw,bot-y);",
           "for(let i=0;i<=10;i++)gr.addColorStop(i/10,heatCol(i/10));INS.mbar(g,x,top,bw,bot-top,(bot-y)/(bot-top),live?INM.rfr(k?anR:anL,dbN):-1,gr);")
s = rep(s, "for(const d of[0,-6,-12,-18,-24,-36,-48,-60]){const y=sy(d);g.fillText(String(d),x0-8,y+6);g.fillRect(x0-5,y,3,2)}",
           "/* IN-M: the numbers did not fit beside the 50 px preview (cut off); the M1 tick scale below instead */")
s = rep(s, "g.textAlign='center';g.fillStyle='#7d8292';g.fillText('L',x0+bw/2,H-1);",
           "INS.scaleTaper(g,x0-1,top,bot-top,{lab:false,k:2});g.textAlign='center';g.fillStyle='#7d8292';g.fillText('L',x0+bw/2,H-1);")

# 2. CSS
css = (
       ".mxme .inslv{cursor:default}.mxme .inslv .mxmh+.mxmh{margin-top:1px}"
       ".mtrpk b.inmv{font-size:var(--fs2)}\n")
s = rep(s, ".dacv{display:flex;", css + ".dacv{display:flex;")

# 1. the block
js = open(os.path.join(HERE, 'in_m_block.js'), encoding='utf-8').read()
s = rep(s, "function askChoice(title,text,btns,icon){", js + "function askChoice(title,text,btns,icon){")
open(P, 'w', encoding='utf-8').write(s)
print('IN-M applied')
