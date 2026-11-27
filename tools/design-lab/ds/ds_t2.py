#!/usr/bin/env python3
"""Task DS-T2 (lane A, design round 2, details TM1, TC1 and TS1): the transport's master meter, the CPU read-out and
the top bar.
   python3 tools/design-lab/ds/ds_t2.py index.html
TM1: the transport meter as a peak meter with a dB scale and hold: tick marks above the two bars (-48 to 0, 0 in red)
and a row of labels under them (-48, -24, -12, 0) instead of lines through the bars; the white hold marks stay; the
read-out says dBFS. The bars are lane E's INS.mbar (RMS core, M2), unchanged.
TC1: the CPU read-out as the last 10 seconds as a line (40 points, one per 250 ms, the highest load in each), on a
fixed 0 to 100 % scale with a faint base line, red while there is a problem; redrawn only when the line changes.
TS1: a quiet status line in the middle of the top bar: the engine's audio format (sample rate, 32-bit float) and the
project's save state (saved n min ago, unsaved changes, not saved to a file yet) with a coloured dot; refreshed every
5 s and when the tabs change, text only written when it changes; hidden when the tabs or buttons would touch it.
DS_HOOKS.status (a function returning extra text) is the place for X10's signal path (task SC-K).
Only the AudioLab look (dsAC3); the other looks keep today's meter, CPU graph and top bar. Every anchor is asserted.
Re-run on a fresh file after a rebase."""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
assert 'task DS-T2 (lane A' not in s, 'already applied'
assert 'function dsAC3()' in s, 'needs task DS-A3'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

BLOCK = r"""/* task DS-T2 (lane A, design round 2, TM1, TC1, TS1): the transport meter with a dB scale and hold, the CPU as the
   last 10 seconds as a line, the top bar's status line (audio format and save state). Only the AudioLab look; drawn
   only on change. DS_HOOKS.status: a function returning extra text for the status line (X10's signal path, task SC-K). */
const DS_HOOKS={status:null};
const DST2={h:new Float32Array(40),i:0,n:0,dn:-1,acc:0,t:0,k:''};
/* TM1: ticks above, two bars (lane E's INS.mbar with the RMS core), labels under; sx is the meter's own dB to x */
function dsT2Mtr(g,w,h,sx){const tk=3,lb=h>=20?7:0,y0=tk+1,bh=Math.max(2,(h-y0-lb-1)/2),y1=y0+bh+1;
  INS.mbar(g,0,y0,w,bh,sx(MT2.l)/w,INM.rfr(anL,v=>sx(v)/w),meters.gr,true);INS.mbar(g,0,y1,w,bh,sx(MT2.r)/w,INM.rfr(anR,v=>sx(v)/w),meters.gr,true);
  g.fillStyle='#fff';g.fillRect(sx(MT2.hl)-1,y0,2,bh);g.fillRect(sx(MT2.hr)-1,y1,2,bh);
  for(const d of[-48,-36,-24,-12,-6,-3,0]){const x=Math.round(sx(d));g.fillStyle=d===0?'rgba(255,77,77,.9)':d%12===0?'rgba(255,255,255,.55)':'rgba(255,255,255,.3)';g.fillRect(x,0,1,d%12===0?tk:tk-1)}
  g.fillStyle='rgba(255,77,77,.55)';g.fillRect(Math.round(sx(0)),y0,1,bh*2+1);
  if(lb){g.font='500 7px Inter,system-ui,sans-serif';g.textBaseline='alphabetic';g.textAlign='center';g.fillStyle='rgba(236,236,241,.5)';
    for(const d of[-48,-24,-12,0])g.fillText(d?String(d).replace('-','−'):'0',Math.min(w-3,Math.round(sx(d))+.5),h-1);g.textAlign='left'}}
function dsT2Unit(){return dsAC3()?' dBFS':' dB'}
/* TC1: the highest load of every 250 ms, 40 of them = the last 10 seconds */
function dsT2CpuPush(load,now){DST2.acc=Math.max(DST2.acc,load);if(now-DST2.t<250)return;DST2.t=now;DST2.i=(DST2.i+1)%40;DST2.h[DST2.i]=DST2.acc;DST2.acc=0;DST2.n++}
function dsT2Cpu(cv,bad){const r=fitRect(cv),H=r.height/ZOOM,ys=[];for(let k=0;k<40;k++){const v=Math.min(1,Math.max(0,DST2.h[(DST2.i+1+k)%40]));ys.push(Math.round((H-1.5-v*(H-3))*2))}
  const key=r.width+'|'+r.height+'|'+(bad?1:0)+'|'+ys.join(','),now=performance.now();if(key===DST2.k&&cv.width>1){DST2.dn=DST2.n;return}
  if(!play.on&&!bad&&DST2.k&&now-(DST2.dt||0)<1000)return;/* stopped: the line catches up once a second at most, as the old graph */DST2.dn=DST2.n;DST2.k=key;DST2.dt=now;
  const{g,w,h}=fit(cv);g.fillStyle='#050608';g.fillRect(0,0,w,h);g.fillStyle='rgba(255,255,255,.12)';g.fillRect(0,h-1,w,1);
  g.beginPath();for(let k=0;k<40;k++){const x=k/39*(w-1)+.5,y=ys[k]/2;k?g.lineTo(x,y):g.moveTo(x,y)}g.strokeStyle=bad?'#ff4d4d':'rgba(62,207,142,.9)';g.lineWidth=1.2;g.lineJoin='round';g.stroke()}
/* TS1: the status line */
function dsT2Ago(t){const m=Math.floor((Date.now()-t)/60000);return m<1?'just now':m<60?m+' min ago':Math.floor(m/60)+' h ago'}
function dsT2Stat(){const tb=$('#ptabs');if(!tb)return;let el=$('#dsStat');
  if(!el){el=document.createElement('div');el.id='dsStat';el.setAttribute('role','status');el.innerHTML='<i></i><span></span>';el.title='Audio format of the engine and whether this project is saved to its file. Save with ⌘S.';tb.appendChild(el)}
  if(!dsAC3()||!PJ){if(!el.hidden){el.hidden=true;try{TMRC=null}catch(e){}}return}
  const p=PJ.list.find(q=>q.id===PJ.cur),fmt=ctx?(ctx.sampleRate/1000)+' kHz · 32-bit float':'audio engine not started',
    st=!p?'':p.dirty?'unsaved changes':p.file&&p.savedAt?'saved '+dsT2Ago(p.savedAt):'not saved to a file yet',
    sc=!p?'':p.dirty?'chg':p.file&&p.savedAt?'ok':'none';
  let x='';try{if(typeof DS_HOOKS.status==='function')x=DS_HOOKS.status()||''}catch(e){}
  const txt=[fmt,x,st].filter(Boolean).join(' · ');
  const h0=el.hidden;let ch=false;if(el.dataset.t!==txt){el.dataset.t=txt;el.lastChild.textContent=txt;ch=true}if(el.dataset.s!==sc){el.dataset.s=sc}
  el.hidden=false;const a=el.getBoundingClientRect(),pl=$('#ptl'),cb=tb.querySelector(':scope>.cb');
  const lt=pl&&pl.lastElementChild?pl.lastElementChild.getBoundingClientRect().right:0,ad=$('#pAdd'),lr=ad?ad.getBoundingClientRect().right:lt,rt=cb?cb.getBoundingClientRect().left:Infinity;
  if(Math.max(lt,lr)+12>a.left||rt-12<a.right)el.hidden=true;
  if(ch||h0!==el.hidden){try{TMRC=null;TMFX=-1e9}catch(e){}}}/* the playhead time in the bar hides behind it like behind a tab (tmRects) */
setInterval(()=>{try{if(document.visibilityState==='visible')dsT2Stat()}catch(e){}},5000);
setTimeout(()=>{try{dsT2Stat();const m=$('#mtr');if(m&&!m.title)m.title='Master peak meter, left and right, on a dBFS scale (−48 to 0). The white marks hold the peaks; the thin core is the RMS level.';const c=$('#cpuC');if(c&&!c.title)c.title='CPU load over the last 10 seconds. Click for the performance panel.'}catch(e){}},1500);
"""
rep("function askChoice(title,text,btns,icon){", BLOCK + "function askChoice(title,text,btns,icon){")

CSS = ("#dsStat{position:absolute;left:50%;top:0;height:100%;transform:translateX(-50%);display:flex;align-items:center;gap:6px;"
       "font:400 11px/1 Inter,system-ui,sans-serif;color:#8b8b97;white-space:nowrap;font-variant-numeric:tabular-nums;z-index:1}"
       "#dsStat[hidden]{display:none}#dsStat>i{width:6px;height:6px;border-radius:50%;background:#5a5d68;flex:none}"
       "#dsStat[data-s=ok]>i{background:#3ecf8e}#dsStat[data-s=chg]>i{background:#f5c84c}\n")
rep(".dacv{display:flex;", CSS + ".dacv{display:flex;")

# TM1: the meter's scale and hold (only the AudioLab look)
rep("  bar(MT2.l,2,anL);bar(MT2.r,3+bh,anR);g.fillStyle='#fff';g.fillRect(sx(MT2.hl)-1,2,2,bh);g.fillRect(sx(MT2.hr)-1,3+bh,2,bh);\n"
    "  g.fillStyle='rgba(255,255,255,.35)';for(const d of[-48,-36,-24,-12,-6,-3,0])g.fillRect(sx(d),0,1,h);g.fillStyle='rgba(255,77,77,.8)';g.fillRect(sx(0),0,1,h)}",
    "  if(dsAC3())dsT2Mtr(g,w,h,sx);else{/* task DS-T2: TM1 above */\n"
    "  bar(MT2.l,2,anL);bar(MT2.r,3+bh,anR);g.fillStyle='#fff';g.fillRect(sx(MT2.hl)-1,2,2,bh);g.fillRect(sx(MT2.hr)-1,3+bh,2,bh);\n"
    "  g.fillStyle='rgba(255,255,255,.35)';for(const d of[-48,-36,-24,-12,-6,-3,0])g.fillRect(sx(d),0,1,h);g.fillStyle='rgba(255,77,77,.8)';g.fillRect(sx(0),0,1,h)}}")
# the meter redraws when the look changes (its key)
rep("Math.round(INM.rfr(anR,v=>sx(v))*4),same=mk===meters.k;",
    "Math.round(INM.rfr(anR,v=>sx(v))*4)+'|'+dsAC3(),same=mk===meters.k;")
rep("{const s1=(pk<=-89?'-∞':(pk>0?'+':'')+pk.toFixed(1))+' dB';",
    "{const s1=(pk<=-89?'-∞':(pk>0?'+':'')+pk.toFixed(1))+dsT2Unit();")
# TC1: the 10 s history and the line
rep("CPU.i=(CPU.i+1)%120;CPU.hist[CPU.i]=load;",
    "CPU.i=(CPU.i+1)%120;CPU.hist[CPU.i]=load;dsT2CpuPush(load,now);")
rep("if(pv===CPU.dv&&bd===CPU.db&&now-(CPU.dt||0)<1000){",
    "if(pv===CPU.dv&&bd===CPU.db&&now-(CPU.dt||0)<1000&&!(DST2.n!==DST2.dn&&dsAC3())){")
rep("const{g,w,h}=fit(cv),bad=cpuBad();g.fillStyle='#050608';g.fillRect(0,0,w,h);g.beginPath();for(let k=0;k<120;k++){const v=CPU.hist[(CPU.i+1+k)%120],x=k/119*w,y=h-1-v*(h-2);k?g.lineTo(x,y):g.moveTo(x,y)}g.lineTo(w,h);g.lineTo(0,h);g.closePath();g.fillStyle=bad?'rgba(255,77,77,.5)':'rgba(62,207,142,.35)';g.fill();",
    "const bad=cpuBad();if(dsAC3())dsT2Cpu(cv,bad);else{DST2.k='';const{g,w,h}=fit(cv);g.fillStyle='#050608';g.fillRect(0,0,w,h);g.beginPath();for(let k=0;k<120;k++){const v=CPU.hist[(CPU.i+1+k)%120],x=k/119*w,y=h-1-v*(h-2);k?g.lineTo(x,y):g.moveTo(x,y)}g.lineTo(w,h);g.lineTo(0,h);g.closePath();g.fillStyle=bad?'rgba(255,77,77,.5)':'rgba(62,207,142,.35)';g.fill()}")
# TS1: refresh with the tabs
rep("function renderTabs(){setTimeout(fileUI,0);",
    "function renderTabs(){setTimeout(fileUI,0);setTimeout(()=>{try{dsT2Stat()}catch(e){}},0);")
open(F, 'w', encoding='utf-8').write(s)
print('task DS-T2 applied')
