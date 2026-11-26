"""Fractal (v0.191, first called Crackle): the instrument and the effect in the page. python3 tools/ui-tests/fractal.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('page errors on load',al.errors)
al.build({'bpm':128,'tracks':[{'name':'Crackle','preset':'crk','clips':[{'start':0,'len':16,'notes':[{'p':45,'s':0,'l':6,'v':.9},{'p':48,'s':6,'l':6,'v':.8}]}]},
  {'name':'Pad','preset':'pad','fx':[{'type':'crk'}],'clips':[{'start':0,'len':16,'notes':[{'p':57,'s':0,'l':16,'v':.8},{'p':60,'s':0,'l':16,'v':.8}]}]}]})
def sel(i):al.run("selT=S.tracks[%d].id;renderFx();1"%i);al.page.wait_for_timeout(900)
def box(D):return json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:Math.max(0,r.left),y:r.top,width:Math.min(r.width,1600-Math.max(0,r.left)),height:r.height})})()"%D))
def shot(D,n):al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.mouse.move(5,5);al.page.wait_for_timeout(600);al.page.screenshot(path=os.path.join(out,n),clip=box(D))
def inside(D,tag):
    print('%-22s %s'%(tag,al.run("(()=>{const d=document.querySelector('%s'),R=d.getBoundingClientRect(),bad=[];for(const el of d.querySelectorAll('[data-c],button,select')){const r=el.getBoundingClientRect();if(!r.width)continue;if(r.left<R.left-1||r.right>R.right+1||r.top<R.top-1||r.bottom>R.bottom+1)bad.push((el.textContent||el.dataset.c||'').trim().slice(0,16))}return 'device '+Math.round(R.width)+' x '+Math.round(R.height)+', outside: '+JSON.stringify(bad)})()"%D)))
def tips(D):
    al.page.mouse.move(5,5);al.page.wait_for_timeout(200)
    print('  no tooltip:',al.run("JSON.stringify([...document.querySelectorAll('%s [data-c],%s button,%s select,%s canvas')].filter(e=>e.getBoundingClientRect().width&&!(e.title||e.closest('[title]')||e.getAttribute('aria-label'))).map(e=>(e.textContent||e.dataset.c||e.tagName).trim().slice(0,14)))"%(D,D,D,D)),
      ' dash:',al.run("(()=>{const d=document.querySelector('%s');let s=d.textContent;for(const e of d.querySelectorAll('[title]'))s+=e.title;return /—|–/.test(s+JSON.stringify(CRKTIP)+JSON.stringify(CRKIPRE)+PRESETS.crk.desc+FXDESC.crk)})()"%D))
# ---- instrument
sel(0);D='.dev.idev.pbx'
print('title order',al.run("JSON.stringify([...document.querySelector('%s .devh').children].map(e=>(e.className||e.tagName).toString().slice(0,12)))"%D))
for tb in 'pfsa':
    al.page.click(D+' [data-ckb="tab:%s"]'%tb);al.page.wait_for_timeout(300);inside(D,'instrument page '+tb);tips(D);shot(D,'crk_inst_%s.png'%tb)
al.page.click(D+' [data-ckb="tab:p"]');al.page.wait_for_timeout(300)
print('preset groups',al.run("JSON.stringify([...document.querySelectorAll('%s select[data-s=ipre] optgroup')].map(g=>g.label+' '+g.children.length))"%D))
print('dials shown with 3 steps',al.run("JSON.stringify([...document.querySelectorAll('%s [data-c^=\"fx:ck:\"]')].map(e=>e.dataset.c.slice(6)))"%D))
al.run("S.tracks[0].inst.ns=6;crkPush(S.tracks[0].inst);changed(false);1");al.run("fxin.dispatchEvent(new Event('pointerup'));1");al.page.wait_for_timeout(500)
print('dials shown with 6 steps',al.run("JSON.stringify([...document.querySelectorAll('%s [data-c^=\"fx:ck:\"]')].map(e=>e.dataset.c.slice(6)))"%D))
for k in ('growl','crackle','pump4','space'):
    al.run("(()=>{const s=document.querySelector('%s select[data-s=ipre]');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}))})()"%(D,k));al.page.wait_for_timeout(500);print('preset',k,al.run("JSON.stringify([S.tracks[0].inst.ipk,S.tracks[0].inst.wv,S.tracks[0].inst.ns,S.tracks[0].inst.kf])"));shot(D,'crk_inst_%s.png'%k)
al.run("undo();undo();undo();undo();1");al.page.wait_for_timeout(300);print('after four undos',al.run("S.tracks[0].inst.ipk"))
al.page.click(D+' [data-ckb="md:s"]');al.page.wait_for_timeout(300);print('kind',al.run("S.tracks[0].inst.md"));shot(D,'crk_inst_pump.png');al.run("undo();1")
al.page.click(D+' [data-ckb="tab:a"]');al.page.wait_for_timeout(300);al.page.click(D+' [data-ckb="add:phaser"]');al.page.wait_for_timeout(400);print('after Add Phaser: track effects',al.run("JSON.stringify(S.tracks[0].fx.map(f=>f.type))"));al.run("undo();1")
# playing: the picture follows the song
al.run("ensureCtx();play.on||start();1");al.page.wait_for_timeout(1500);shot(D,'crk_inst_playing.png');al.run("play.on&&stop();1")
print('errors so far',al.errors)
# ---- effect
sel(1);D='.dev.pbx-crk'
print('effect title order',al.run("JSON.stringify([...document.querySelector('%s .devh').children].map(e=>(e.className||e.tagName).toString().slice(0,14)))"%D))
for tb in ('tp','tf','ta'):
    al.page.click(D+' [data-nact="%s"]'%tb);al.page.wait_for_timeout(300);inside(D,'effect page '+tb);tips(D);shot(D,'crk_fx_%s.png'%tb)
al.page.click(D+' [data-nact="xvd"]');al.page.wait_for_timeout(400);print('after + Vector Delay',al.run("JSON.stringify(S.tracks[1].fx.map(f=>f.type))"));al.run("undo();1")
al.page.click(D+' [data-nact="tp"]');al.page.wait_for_timeout(300)
for k in ('buzz','tg16'):
    al.run("(()=>{const t=S.tracks[1],f=t.fx[0];Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE.crk['%s'][1])));f.p.pre='%s';changed(true);renderFx()})()"%(k,k));al.page.wait_for_timeout(500);shot(D,'crk_fx_%s.png'%k)
print('effect latency',al.run("fxLat(S.tracks[1].fx[0],48000)"),'at mix 0',al.run("(()=>{const f=S.tracks[1].fx[0],m=f.p.mix;f.p.mix=0;const r=fxLat(f,48000);f.p.mix=m;return r})()"))
print('in the effect browser group',al.run("JSON.stringify(FBG.find(g=>g[2].includes('crk'))[0])"),'instrument group',al.run("JSON.stringify(IBG.find(g=>g[2].includes('crk'))[0])"))
print('errors',al.errors)
al.stop()
