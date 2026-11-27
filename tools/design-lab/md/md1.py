#!/usr/bin/env python3
"""Task MD1: the measurement details (M1 readouts with units, M2 orbit loader, M3 caliper). python3 tools/design-lab/md/md1.py index.html
Every anchor is asserted unique. Re-run on a fresh file after a rebase."""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
D = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
assert 'task MD1: the measurement details' not in s, 'already applied'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:140])
    s = s.replace(old, new)

# 0. blocks: JS before askChoice, CSS before .dacv
rep('function askChoice(title,text,btns,icon){', open(os.path.join(D, 'md1_block.js'), encoding='utf-8').read() + 'function askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;', open(os.path.join(D, 'md1_css.txt'), encoding='utf-8').read() + '.dacv{display:flex;')

# 1. M1: units as small capitals (LOOK says so; the canvas helper draws them so)
rep("digits:'tabular',unitCase:'as written',", "digits:'tabular',unitCase:'small caps',")
rep("const a=m[1]+m[2],wa=g.measureText(a).width;g.fillText(a,x,y);const f=g.fillStyle;g.fillStyle=lkT().unit;g.fillText(m[3],x+wa,y);g.fillStyle=f;return wa+g.measureText(m[3]).width}",
    "const a=m[1]+m[2],wa=g.measureText(a).width;g.fillText(a,x,y);const f=g.fillStyle,sc='fontVariantCaps' in g&&lkT().unitCase==='small caps';g.fillStyle=lkT().unit;if(sc)g.fontVariantCaps='all-small-caps';g.fillText(m[3],x+wa,y);const wu=g.measureText(m[3]).width;if(sc)g.fontVariantCaps='normal';g.fillStyle=f;return wa+wu}")
# transport read-outs: amber small-capital units, fixed decimals
rep("$('#cpuV').textContent=Math.round(load*100)+'%';", "lkOut($('#cpuV'),Math.round(load*100)+'%');")
rep("el.textContent=(ms<10?ms.toFixed(1):Math.round(ms))+' ms';", "lkOut(el,ms.toFixed(1)+' ms');")
rep("if(meters.a!==s1){meters.a=s1;$('#pkNow').textContent=s1}", "if(meters.a!==s1){meters.a=s1;lkOut($('#pkNow'),s1)}")
rep("S.master=v;const e=$('#mBtnV');if(e)e.textContent=SPEC_MASTER.f(v);", "S.master=v;const e=$('#mBtnV');if(e)lkOut(e,SPEC_MASTER.f(v));")
rep("after:v=>{$('#mBtnV').textContent=SPEC_MASTER.f(v);", "after:v=>{lkOut($('#mBtnV'),SPEC_MASTER.f(v));")
rep("S.master=v;$('#mBtnV').textContent=SPEC_MASTER.f(v);", "S.master=v;lkOut($('#mBtnV'),SPEC_MASTER.f(v));")

# 2. M2: the orbit loader replaces the old busy badge, the update window's bar, the export bars, the AI voice bar and the bounce bar
rep("const ldBadge=(px,txt)=>`<span class=\"ldb\" style=\"--s:${px||28}px\"><canvas class=\"ldbc\" aria-hidden=\"true\"></canvas>${txt?`<span>${esc(txt)}</span>`:''}</span>`;",
    "const ldBadge=(px,txt)=>`<span class=\"ldb\" style=\"--s:${mdOrbPx(px||28)}px\">${mdOrb(px||28,null,txt||'Working')}${txt?`<span>${esc(txt)}</span>`:''}</span>`;/* task MD1: the orbit loader */")
rep("if(sp)sp.textContent='Rendering… '+Math.round(f*100)+'%'", "if(sp)sp.textContent='Rendering… '+Math.round(f*100)+'%';mdOrbSet(st,f)")
rep("s.innerHTML=(cls==='busy'?'<i class=\"updbar\"></i>':'')+'<span>'+msg+'</span>';", "s.innerHTML=(cls==='busy'?mdOrb(16,null,'Working'):'')+'<span>'+msg+'</span>';")
rep("function exProg(p,t,det){exTop(p,t);", "function exProg(p,t,det){exTop(p,t);mdExpSet(p);")
rep("function exTop(p,t){let b=document.getElementById('exTop');if(!b){b=document.createElement('div');b.id='exTop';b.innerHTML='<i></i><span></span><b></b>';document.body.appendChild(b)}const done=p>=1;b.hidden=false;b.classList.toggle('done',done);b.firstChild.style.width=",
    "function exTop(p,t){let b=document.getElementById('exTop');if(!b){b=document.createElement('div');b.id='exTop';b.innerHTML='<i></i><span></span><b></b>';document.body.appendChild(b)}const done=p>=1;b.hidden=false;b.classList.toggle('done',done);b.querySelector('i').style.width=")
rep("<div class=\"vaprog\" title=\"Progress\"><i></i></div>", "<div class=\"vaprog mdvap\" title=\"Progress\" hidden>${mdOrb(24,0,'Progress')}<b></b></div>")
rep("function vaiPaintBar(){const W=VAI.W;if(!W||W.hidden)return;const b=W.querySelector('.vaprog i'),m=W.querySelector('.vamsg');if(b)b.style.width=Math.round(Math.max(0,Math.min(1,VAI.prog))*100)+'%';",
    "function vaiPaintBar(){const W=VAI.W;if(!W||W.hidden)return;const b=W.querySelector('.vaprog'),m=W.querySelector('.vamsg');if(b){const q=Math.max(0,Math.min(1,VAI.prog||0));mdOrbSet(b,q);const pc=b.querySelector('b');if(pc)pc.textContent=Math.round(q*100)+'%';b.hidden=!(VAI.busy||(q>0&&q<1))}")
# the stem splitter: progress in the job pill instead of a toast every few percent
rep("try{const all=await neuSeparate(src,PS.engine,PS.keep,(ph,p,mb)=>{if(ph==='dl')say(`Downloading the stem model… ${Math.round(p*100)}% of ${M.mb} MB (only the first time)`);else if(ph==='init')say('Loading the stem model…');else if(ph==='run')say(`Separating with HTDemucs… ${Math.round(p*100)}%`)});",
    "try{const all=await neuSeparate(src,PS.engine,PS.keep,(ph,p,mb)=>{if(ph==='dl')mdJob('stem',`Downloading the stem model, ${M.mb} MB (only the first time)`,p);else if(ph==='init')mdJob('stem','Loading the stem model',null);else if(ph==='run')mdJob('stem','Separating with HTDemucs',p)});mdJobEnd('stem');")
rep("catch(e){const ok=await askChoice('The neural split could not run',", "catch(e){mdJobEnd('stem');const ok=await askChoice('The neural split could not run',")
rep("toast('Splitting into stems… 0%');let last=0;try{const all=await stemSplit(src,p=>{const q=Math.round(p*100);if(q-last>=8){last=q;toast('Splitting into stems… '+q+'%')}},PS);",
    "mdJob('stem','Splitting into stems',0);try{const all=await stemSplit(src,p=>mdJob('stem','Splitting into stems',p),PS);mdJobEnd('stem');")
rep("c.mute=true;changed(true);toast('Done. '+bufs.length+' stem track'+(bufs.length===1?'':'s')+' added below. The original clip is muted. Quick split is approximate: use it for sketching and remixing.')}catch(e){toast(",
    "c.mute=true;changed(true);toast('Done. '+bufs.length+' stem track'+(bufs.length===1?'':'s')+' added below. The original clip is muted. Quick split is approximate: use it for sketching and remixing.')}catch(e){mdJobEnd('stem');toast(")
# the bounce of a MIDI clip on an audio track (task AK): the orbit fills at the left of the busy clip instead of the bar along its bottom
rep("g.fillStyle='#4cc9f0';g.fillRect(G.x,G.y+G.h-4,G.w*Math.max(.02,J.p),4);g.fillStyle='#e8f6ff';g.font='600 11px Inter,system-ui,sans-serif';if(G.w>60)g.fillText((J.label||'Bouncing to audio')+(J.nopct?'':'… '+Math.round(J.p*100)+'%'),Math.max(G.x,X0)+8,G.y+G.h/2+4);",
    "{const op=G.h>=40?24:16,ox=Math.max(G.x,X0)+6+op/2;if(G.w>op+12)mdOrbDraw(g,ox,G.y+G.h/2,op,J.nopct?null:J.p,now);g.fillStyle='#e8f6ff';g.font='600 11px Inter,system-ui,sans-serif';if(G.w>60+op)g.fillText((J.label||'Bouncing to audio')+(J.nopct?'':'… '+Math.round(J.p*100)+'%'),ox+op/2+6,G.y+G.h/2+4)}")

# 3. the version
import re
m = re.search(r"const VERSION='0\.(\d+)'", s); v = int(m.group(1))
if len(sys.argv) > 2 and sys.argv[2] == 'bump':
    rep("const VERSION='0.%03d'" % v, "const VERSION='0.%03d'" % (v + 1))
open(F, 'w', encoding='utf-8').write(s)
print('applied; version', '0.%03d' % (v + (1 if len(sys.argv) > 2 and sys.argv[2] == 'bump' else 0)))
