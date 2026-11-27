"""Task IN-O (lane E, instruments): stereo field and phase, the user's picks O0 (today's drawing kept), O1 (marks and afterglow) and
O4 (polar view as a menu choice).
Edit script with unique asserted anchors, so a rebase can re-run it on a fresh index.html.
  python3 tools/design-lab/in/in_o.py [index.html]
Does:
  1. adds the IN-O block (in_o_block.js) before askChoice: INSO, inoMarks, inoLayer, inoCols, inoField, inoPolBox, inoPol, inoPolBg,
     inoBox, inoCorr, inoBalTicks, inoMaster; wraps mxMenuItems to add the Picture choice to the stereo field's menu
  2. drawMixer's stereo view: the marks or the polar background after the L R M labels; the dots through inoField (taps stay at 256);
     the phase bar through inoCorr, ticks on the balance bar
  3. the master box's Stereo value through inoMaster (real minus, phase angle); CSS: its negative half hatched
  4. the overlay's stereo module: the O1 marks
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
if '/* ===== lane E (task IN-O)' in s:
    print('IN-O already applied'); sys.exit(0)
assert '/* ===== end of lane E IN-G' in s, 'IN-G must be in first'

def rep(s, old, new, n=1):
    c = s.count(old)
    assert c == n, (old[:90], c, n)
    return s.replace(old, new)

# 2. mixer stereo view
s = rep(s, "g.fillText('L',sx+3,sy0+9);g.fillText('R',sx+S0-9,sy0+9);g.fillText('M',cx-3,sy0+S0-3);",
        "g.fillText('L',sx+3,sy0+9);g.fillText('R',sx+S0-9,sy0+9);g.fillText('M',cx-3,sy0+S0-3);inoBox(g,sx,sy0,S0,cx,cy,R);/* IN-O: O1 marks or O4 */")
s = rep(s, """if(live){const n=Math.min(aL.fftSize,512),bl=new Float32Array(n),br=new Float32Array(n);aL.getFloatTimeDomainData(bl);aR.getFloatTimeDomainData(br);let sl=0,sr=0,sc=0;
        for(let i=0;i<n;i++){const l=bl[i],r=br[i];sl+=l*l;sr+=r*r;sc+=l*r;const s=(l+r)*.7071,d=(r-l)*.7071;
          g.fillStyle=mxC(cm,Math.min(1,Math.hypot(s,d)*1.4),col,H0.b3,0);g.globalAlpha=.6;const px=cx+d*R,py=cy-s*R;g.fillRect(px,py,1.6,1.6)}g.globalAlpha=1;""",
        """if(live){const bl=INS.td(aL),br=INS.td(aR),n=Math.min(bl.length,br.length,512);let sl=0,sr=0,sc=0;/* IN-O: read once a frame (INS.td) */
        for(let i=0;i<n;i++){const l=bl[i],r=br[i];sl+=l*l;sr+=r*r;sc+=l*r}inoField(cv,g,sx,sy0,S0,cx,cy,R,bl,br,n,cm,col,H0);/* IN-O: O1 afterglow and newest dot, O4 */""")
s = rep(s, "g.fillStyle='#14161c';g.fillRect(bx,yb,bw2,6);const cpos=bx+(corr+1)/2*bw2;g.fillStyle=corr<0?'#ff1d6e':mxC(cm,.5+corr*.4,col,H0.b3,0);g.fillRect(Math.min(cpos,bx+bw2/2),yb,Math.abs(cpos-(bx+bw2/2)),6);g.fillStyle='#fff';g.fillRect(cpos-1,yb-1,2,8);g.fillStyle='rgba(255,255,255,.25)';g.fillRect(bx+bw2/2,yb,1,6);",
        "inoCorr(g,bx,yb,bw2,corr,corr<0?'#ff1d6e':mxC(cm,.5+corr*.4,col,H0.b3,0));/* IN-O: O1 scale, hatching, value and angle */")
s = rep(s, "g.fillStyle='rgba(255,255,255,.25)';g.fillRect(bx+bw2/2,yb2,1,6);",
        "g.fillStyle='rgba(255,255,255,.25)';g.fillRect(bx+bw2/2,yb2,1,6);inoBalTicks(g,bx,yb2,bw2);")
# 3. master box
s = rep(s, "if(me._t!==t){me._t=t;me.querySelector('b').textContent=t;", "if(me._t!==t){me._t=t;inoMaster(me,MXCO);/* IN-O */")
s = rep(s, ".dacv{display:flex;", ".mxme .mxco .mxbar{background-image:repeating-linear-gradient(135deg,rgba(255,77,109,.32) 0 1px,transparent 1px 4px);background-size:50% 100%;background-repeat:no-repeat}/* IN-O: the negative half hatched */\n.dacv{display:flex;")
# 4. overlay stereo module
s = rep(s, "g.fillText('L',cx-r-1,cy-r+1);g.fillText('R',cx+r-5,cy-r+1);",
        "g.fillText('L',cx-r-1,cy-r+1);g.fillText('R',cx+r-5,cy-r+1);inoMarks(g,cx,cy,r*1.25,r,{a:Math.min(1,ga*3)});/* IN-O: O1 marks */")
# 1. the block
js = open(os.path.join(HERE, 'in_o_block.js'), encoding='utf-8').read()
s = rep(s, "function askChoice(title,text,btns,icon){", js + "function askChoice(title,text,btns,icon){")
open(P, 'w', encoding='utf-8').write(s)
print('IN-O applied')
