"""Bounce, the bouncing-ball instrument (v0.189): the device in the page. python3 tools/ui-tests/bounce_instrument.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('errors after load',al.errors)
al.build({'bpm':120,'tracks':[{'name':'Bounce','preset':'bball','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':2,'v':.9},{'p':67,'s':2,'l':2,'v':.8},{'p':64,'s':4,'l':4,'v':.7}]}]}]})
al.run("selT=S.tracks[0].id;renderFx();1");al.page.wait_for_timeout(900)
D='.dev.idev.pbx'
def box():return json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:Math.max(0,r.left),y:r.top,width:Math.min(r.width,1600-Math.max(0,r.left)),height:r.height})})()"%D))
def shot(n):al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.mouse.move(5,5);al.page.wait_for_timeout(600);al.page.screenshot(path=os.path.join(out,n),clip=box())
I=lambda k:al.run("JSON.stringify(S.tracks[0].inst.%s)"%k)
def inside(tag):
    print('%-12s %s'%(tag,al.run("(()=>{const d=document.querySelector('%s'),R=d.getBoundingClientRect(),bad=[];for(const el of d.querySelectorAll('[data-c],button,select')){const r=el.getBoundingClientRect();if(!r.width)continue;if(r.left<R.left-1||r.right>R.right+1||r.top<R.top-1||r.bottom>R.bottom+1)bad.push((el.textContent||el.dataset.c||'').trim().slice(0,16))}return 'device '+Math.round(R.width)+' x '+Math.round(R.height)+', outside: '+JSON.stringify(bad)})()"%D)))
print('title order',al.run("JSON.stringify([...document.querySelector('%s .devh').children].map(e=>(e.className||e.tagName).toString().slice(0,12)))"%D))
inside('Sound');shot('bounce_sound.png')
al.page.click(D+' [data-bbb="tab:b"]');al.page.wait_for_timeout(300);inside('Ball');shot('bounce_ball.png')
al.page.mouse.move(5,5);al.page.wait_for_timeout(300)
print('controls without a tooltip',al.run("JSON.stringify([...document.querySelectorAll('%s [data-c],%s button,%s select,%s canvas')].filter(e=>e.getBoundingClientRect().width&&!(e.title||e.dataset.tip||e.getAttribute('aria-label'))).map(e=>(e.textContent||e.dataset.c||e.tagName).trim().slice(0,14)))"%(D,D,D,D)))
print('em dash in device text or tooltips',al.run("(()=>{const d=document.querySelector('%s');let s=d.textContent;for(const e of d.querySelectorAll('[title]'))s+=e.title;return /—|–/.test(s+JSON.stringify(BBITIP)+JSON.stringify(BBIPRE)+PRESETS.bball.desc)})()"%D))
print('preset groups',al.run("JSON.stringify([...document.querySelectorAll('%s select[data-s=ipre] optgroup')].map(g=>g.label+' '+g.children.length))"%D))
# choices on the Ball page
for k,v in (('sync','1/4'),('bmode','half'),('hold','n'),('ivl','1/8')):
    al.run("(()=>{const s=document.querySelector('%s select[data-bbs=%s]');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}))})()"%(D,k,v));al.page.wait_for_timeout(250)
al.page.click(D+' [data-bbb="auto"]');al.page.wait_for_timeout(250)
print('Ball page choices: rhythm',I('sync'),'bounce',I('bmode'),'stops',I('hold'),'auto',I('auto'),'every',I('ivl'))
shot('bounce_ball_rhythm.png')
al.run("undo();undo();undo();undo();undo();1");al.page.wait_for_timeout(300);print('after five undos: rhythm',I('sync'),'bounce',I('bmode'),'stops',I('hold'),'auto',I('auto'),'every',I('ivl'))
al.page.click(D+' [data-bbb="tab:s"]');al.page.wait_for_timeout(300)
for m in ('g','m','s','d','w'):
    al.page.click(D+' [data-bbb="mat:%s"]'%m);al.page.wait_for_timeout(200)
    if m=='g':shot('bounce_glass.png')
print('material after clicks',I('mat'))
# presets
for k in ('ratchet','rain','beat'):
    al.run("(()=>{const s=document.querySelector('%s select[data-s=ipre]');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}))})()"%(D,k));al.page.wait_for_timeout(500);print('preset',k,I('ipk'),'material',I('mat'),'rhythm',I('sync'));shot('bounce_%s.png'%k)
al.run("undo();undo();undo();1");al.page.wait_for_timeout(300);print('after three undos: preset',I('ipk'))
# shut and open
al.run("(document.querySelector('%s .duar')||{click(){}}).click();1"%D);al.page.wait_for_timeout(500);inside('shut');shot('bounce_shut.png');al.run("(document.querySelector('%s .duar')||{click(){}}).click();1"%D);al.page.wait_for_timeout(500);inside('open again')
# playing: the balls of the clip
al.run("pos=0;1");al.page.keyboard.press('Space');al.page.wait_for_timeout(1300);shot('bounce_playing.png');al.page.wait_for_timeout(900);shot('bounce_playing2.png');al.page.keyboard.press('Space');al.page.wait_for_timeout(400)
# a key played by hand drops a ball in the picture
al.run("(()=>{const t=S.tracks[0];window._h=voiceOn(t,72,.9);setTimeout(()=>_h&&_h.off(),600);1})()");al.page.wait_for_timeout(500);print('balls from keys in the picture',al.run("(BBILV.get(S.tracks[0].inst)||[]).length"));shot('bounce_key.png')
# browser
print('in the instrument browser',al.run("JSON.stringify(IBG.filter(g=>g[2].includes('bball')).map(g=>g[0]+': '+g[2].join(' ')))"),'name',al.run("PRESETS.bball.name"))
al.run("openBrowser(S.tracks[0]);1");al.page.wait_for_timeout(2500)
r=al.run("(()=>{const el=document.querySelector('#ib [data-k=bball]');if(!el)return '';el.scrollIntoView({block:'center'});return '1'})()")
if r:
    al.page.wait_for_timeout(1000);b=json.loads(al.run("(()=>{const r=document.querySelector('#ib [data-k=bball]').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:r.width,height:r.height})})()"));al.page.screenshot(path=os.path.join(out,'bounce_browser.png'),clip=b)
print('browser tile found',bool(r),'errors',al.errors);al.stop()
