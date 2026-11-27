#!/usr/bin/env python3
"""Task LK (lane A): the look tokens. python3 tools/design-lab/lk/lk.py index.html
Every anchor is asserted (unique unless a count is given). Re-run on a fresh file after a rebase."""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
D = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
assert 'task LK (lane A): look tokens' not in s, 'already applied'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

# 0. blocks: JS before askChoice, CSS before .dacv
rep('function askChoice(title,text,btns,icon){', open(os.path.join(D, 'lk_block.js'), encoding='utf-8').read() + 'function askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;', open(os.path.join(D, 'lk_css.txt'), encoding='utf-8').read() + '.dacv{display:flex;')

# 1. the Settings look sliders give the name LOOK to the tokens
rep("const LOOK=[['#setGrid'", "const LOOK_SL=[['#setGrid'")
rep("for(const[id,k,d,f] of LOOK){", "for(const[id,k,d,f] of LOOK_SL){")
rep("for(const[id,k] of LOOK)$(id).oninput", "for(const[id,k] of LOOK_SL)$(id).oninput")

# 2. arrangement: G3 drafting grid in hairlines, lane quarter lines, hairline separators, ruler, A1 selection, L2 gain unit
rep("layoutRows();g.save();g.beginPath();g.rect(0,AY,w,h-AY);g.clip();/* track rows never paint above",
    "const LKG=lkGrid(DPX);layoutRows();g.save();g.beginPath();g.rect(0,AY,w,h-AY);g.clip();/* track rows never paint above")
rep("g.fillStyle=TH.sep;g.fillRect(0,y+V.th-1,w,1)});g.restore();",
    "if(LKG.rows&&V.th>=40){g.fillStyle=LKG.rowC;for(let r=1;r<4;r++)g.fillRect(X0,Math.round((y+V.th*r/4)*DPX)/DPX,w-X0,LKG.hp)}g.fillStyle=TH.sep;g.fillRect(0,Math.round((y+V.th)*DPX)/DPX-LKG.hp,w,LKG.hp)});g.restore();")
rep("g.fillStyle=`rgba(${TH.gr||'255,255,255'},${Math.min(1,(big?.15:bar?.1:beat?.055:.03)*gk*(TH.grk||1))})`;g.fillRect(Math.round((X0+(b-V.x)*V.ppb)*DPX)/DPX,AY,big?1.5:1,h)",
    "g.fillStyle=`rgba(${TH.gr||'255,255,255'},${Math.min(1,(big?LKG.phrase:bar?LKG.bar:beat?LKG.beat:LKG.six)*gk*(TH.grk||1))})`;g.fillRect(Math.round((X0+(b-V.x)*V.ppb)*DPX)/DPX,AY,LKG.hp,h)")
rep("g.fillStyle=TH.rulerLine;g.fillRect(x,TY,1,RUL);g.fillStyle=TH.rulerTxt;g.fillText(bar+1,x+4,TY+14)",
    "g.fillStyle=TH.rulerLine;g.fillRect(Math.round(x*DPX)/DPX,TY,1/DPX,RUL);g.fillStyle=TH.rulerTxt;g.fillText(bar+1,x+4,TY+14)", 3)
rep("g.fillStyle='#25252c';g.fillRect(RCL,TY+RUL-1,Math.max(0,w-RCL),1);",
    "g.fillStyle='#25252c';g.fillRect(RCL,TY+RUL-LKG.hp,Math.max(0,w-RCL),LKG.hp);")
rep("g.fillStyle='rgba(120,170,255,.16)';g.fillRect(x1,y1,x2-x1,y2-y1);g.strokeStyle='rgba(150,190,255,.95)';",
    "g.fillStyle=lkSel(.12);g.fillRect(x1,y1,x2-x1,y2-y1);g.strokeStyle=lkSel(.95);")
rep("g.setLineDash([]);g.fillStyle='#bcd4ff';g.font='600 10px Inter,sans-serif';",
    "g.setLineDash([]);g.fillStyle=lkT().sel;g.font='600 10px Inter,sans-serif';")
rep("if(sel){rr(g,G.x+.75,G.y+.75,G.w-1.5,G.h-1.5,CR);g.strokeStyle='rgba(80,160,255,.16)';g.lineWidth=5;g.stroke();g.strokeStyle='rgba(80,160,255,.3)';g.lineWidth=3;g.stroke();g.strokeStyle='#4ea2ff';g.lineWidth=1.6;g.stroke();g.strokeStyle='rgba(255,255,255,.95)';g.lineWidth=.6;g.stroke()}",
    "if(sel){rr(g,G.x+.75,G.y+.75,G.w-1.5,G.h-1.5,CR);g.strokeStyle=lkSel(.22);g.lineWidth=4;g.stroke();g.strokeStyle='rgba(0,0,0,.55)';g.lineWidth=2.6;g.stroke();g.strokeStyle=lkT().sel;g.lineWidth=1.4;g.stroke()}")
rep("g.font='600 10px Inter,system-ui,sans-serif';g.fillText(gl,lx+11,by-.5)}",
    "g.font='600 10px Inter,system-ui,sans-serif';lkVU(g,gl,lx+11,by-.5)}")

# 3. piano roll: the same levels in hairlines, octave lines, A1 selection
rep("g.fillStyle=isBar?'#3a3a46':isBeat?'#26262e':'#1b1b21';g.fillRect(Math.round(x),PRUL,1,gh)}",
    "g.fillStyle=isBar?LKP.bar:isBeat?LKP.beat:LKP.six;g.fillRect(Math.round(x*LKP.d)/LKP.d,PRUL,LKP.hp,gh)}")
i = s.index("g.fillStyle=isBar?LKP.bar:isBeat?LKP.beat:LKP.six;")
j = s.rindex("for(let b=Math.floor(b0/st)*st;b<=b1;b+=st){", 0, i)
assert i - j < 400
s = s[:j] + "const LKP=lkPR();" + s[j:]
rep("if(k===0){g.fillStyle='#2b2b34';g.fillRect(KEYW,y+PR.rh-1,w-KEYW,1)}",
    "if(k===0){const P=lkPR();g.fillStyle=P.oct;g.fillRect(KEYW,Math.round((y+PR.rh)*P.d)/P.d-P.hp,w-KEYW,P.hp)}")
rep("if(n.sel){g.strokeStyle='#fff';g.lineWidth=1.5;rr(g,x,y+1,nw,PR.rh-2,2);g.stroke()}",
    "if(n.sel){rr(g,x,y+1,nw,PR.rh-2,2);g.strokeStyle='rgba(0,0,0,.6)';g.lineWidth=2.6;g.stroke();g.strokeStyle=lkT().sel;g.lineWidth=1.4;g.stroke()}")
rep("if(pd&&pd.k==='rect'){g.fillStyle='rgba(76,141,255,.15)';g.strokeStyle='#4c8dff';",
    "if(pd&&pd.k==='rect'){g.fillStyle=lkSel(.12);g.strokeStyle=lkT().sel;")
rep("g.fillStyle=n.sel?'#fff':t.color;g.globalAlpha=n.m?.35:1;", "g.fillStyle=n.sel?lkT().sel:t.color;g.globalAlpha=n.m?.35:1;")
rep("const x=KEYW+(bar*4-PR.x)*PR.ppb;if(x<KEYW)continue;g.fillRect(x,0,1,PRUL);",
    "const x=KEYW+(bar*4-PR.x)*PR.ppb;if(x<KEYW)continue;{const P=lkPR();g.fillRect(Math.round(x*P.d)/P.d,0,P.hp,PRUL)}")

# 4. device displays: frequency grids with the three drafting levels in hairlines
rep("for(const f of[50,100,200,500,1000,2000,5000,10000]){const x=Math.round(fX(f,w))+.5;g.beginPath();g.moveTo(x,0);g.lineTo(x,h);g.stroke();g.fillText(f>=1000?f/1000+'k':f,x+2,h-3)}}",
    "const L=lkT(),d=INS.dpr(g),lc=g.fillStyle;for(const f of[50,100,200,500,1000,2000,5000,10000]){const x=Math.round(fX(f,w)*d)/d;g.fillStyle=f===100||f===1000||f===10000?L.gMaj:L.gMid;g.fillRect(x,0,1/d,h);g.fillStyle=lc;g.fillText(f>=1000?f/1000+'k':f,x+2,h-3)}}")
rep("for(const f of[30,50,100,200,500,1000,2000,5000,10000]){const x=Math.round(fX(f,w))+.5;g.beginPath();g.moveTo(x,0);g.lineTo(x,h);g.stroke();if(lab!==false)g.fillText(f>=1000?f/1000+'k':f,x+2,h-3)}}",
    "const L=lkT(),d=INS.dpr(g),lc=g.fillStyle;for(const f of[30,50,100,200,500,1000,2000,5000,10000]){const x=Math.round(fX(f,w)*d)/d;g.fillStyle=col||(f===100||f===1000||f===10000?L.gMaj:f===30?L.gMin:L.gMid);g.fillRect(x,0,1/d,h);g.fillStyle=lc;if(lab!==false)g.fillText(f>=1000?f/1000+'k':f,x+2,h-3)}}")
rep("g.font='9px Inter,system-ui,sans-serif';for(const fr of[30,50,100,200,300,500,1000,2000,3000,5000,10000,20000]){const x=Math.round(fX(fr,w))+.5;g.fillStyle=/^(1|2|5)/.test(String(fr))?'rgba(255,255,255,.07)':'rgba(255,255,255,.035)';g.fillRect(x,0,1,h);",
    "const L=lkT(),dd=INS.dpr(g);g.font='9px Inter,system-ui,sans-serif';for(const fr of[30,50,100,200,300,500,1000,2000,3000,5000,10000,20000]){const x=Math.round(fX(fr,w)*dd)/dd;g.fillStyle=/^10*$/.test(String(fr))?L.gMaj:/^(2|5)0*$/.test(String(fr))?L.gMid:L.gMin;g.fillRect(x,0,1/dd,h);")
rep("const y=Math.round(dy(db))+.5;g.fillStyle=db?'rgba(255,255,255,.05)':'rgba(255,255,255,.14)';g.fillRect(0,y,w,1);",
    "const y=Math.round(dy(db)*dd)/dd;g.fillStyle=db?(db%12?L.gMin:L.gMid):L.gMaj;g.fillRect(0,y,w,1/dd);")

# 5. L2 units in the page: every control's read-out, the channel volume
rep("if(o)o.textContent=C.spec.f(v)+(C.kind==='cs'&&C.spec===SPEC_VOL?' dB':'');", "if(o)lkOut(o,C.spec.f(v)+(C.kind==='cs'&&C.spec===SPEC_VOL?' dB':''));")
rep("const o=fxin.querySelector('.tdvo');if(o)o.textContent=SPEC_VOL.f(v)+' dB';", "const o=fxin.querySelector('.tdvo');if(o)lkOut(o,SPEC_VOL.f(v)+' dB');")
rep('<output class="tdvo" title="Channel volume">${SPEC_VOL.f(t.vol)} dB</output>', '<output class="tdvo" title="Channel volume">${SPEC_VOL.f(t.vol)} <span class="lku">dB</span></output>')
rep("const s=SPEC_VOL.f(t.vol)+' dB';if(o.textContent!==s)o.textContent=s", "const s=SPEC_VOL.f(t.vol)+' dB';if(o.textContent!==s)lkOut(o,s)")

# 6. M3: ambient drawings (splash, About) only at Ambient and never in Light mode; logos still at Signal only
rep("var b=D.body,lim=b&&(", "var b=D.body;if(b&&(b.classList.contains('lite')||b.classList.contains('lkstill'))){if(!S.lkS){S.lkS=1;var o0=S.still;S.still=true;draw(ts);S.still=o0}S.raf=W.requestAnimationFrame(tick);return}S.lkS=0;var lim=b&&(")
rep("const still=()=>AT.reduce||document.body.classList.contains('lite');", "const still=()=>AT.reduce||document.body.classList.contains('lite')||document.body.classList.contains('lkstill');")
rep("function aoStill(){return AT.red0!=null?!!AT.red0:!!AT.reduce}", "function aoStill(){return(AT.red0!=null?!!AT.red0:!!AT.reduce)||document.body.classList.contains('lkm1')}")

# 7. Settings: Density and Motion on the Layout page (until lane B's Appearance page)
rep('        <h4>Interface scale</h4>\n',
    '        <h4>Density and motion</h4>\n'
    '        <div class="row" title="How tightly tracks and lists are packed. Dense fits more tracks on the screen, Roomy gives each track more height. A project where you set the track height yourself keeps it."><span>Density</span><select id="lkDens" aria-label="Density"><option value="roomy">Roomy</option><option value="today">Today</option><option value="dense">Dense</option></select></div>\n'
    '        <div class="row" title="What may move on its own. Signal only: the playhead, meters and displays. Signal and transitions: also short animations when things open and close. Ambient: also slow drawings on empty and waiting screens, never in Light mode."><span>Motion</span><select id="lkMotion" aria-label="Motion"><option value="signal">Signal only</option><option value="trans">Signal and transitions</option><option value="ambient">Ambient</option></select></div>\n'
    '        <p class="hint">Dense fits more tracks on the screen; a project where you set the track height yourself keeps it. Motion: what may move on its own. The playhead, meters and displays always move.</p>\n'
    '        <h4>Interface scale</h4>\n')

# 8. a console error seen on the way (v0.245): a filter card with no resonance value
rep("if(PL2[k]){const act=hit&&I.a!=null?clamp(plEnvAt(I,age,hit.dur),0,1):0;PL2[k](g,w,h,I,tm,act,age,hit);continue}",
    "if(PL2[k]){/* task LK: a new project's first instrument can lack these values; the cards threw every frame */const I2=I.lfo==null||I.res==null||I.lamt==null||I.morph==null||I.cut==null?Object.assign({morph:0,cut:1800,res:1,lfo:.3,lamt:0},I):I;const act=hit&&I2.a!=null?clamp(plEnvAt(I2,age,hit.dur),0,1):0;PL2[k](g,w,h,I2,tm,act,age,hit);continue}")

open(F, 'w', encoding='utf-8').write(s)
print('task LK applied')
