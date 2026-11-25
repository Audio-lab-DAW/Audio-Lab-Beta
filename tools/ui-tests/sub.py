"""Sub (v0.186): the device in the page. python3 tools/ui-tests/sub.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.build({'bpm':120,'tracks':[{'name':'Kick','preset':'kick','clips':[{'start':0,'len':16,'notes':[{'p':36,'s':i,'l':.5,'v':1} for i in range(16)]}]},
  {'name':'Sub','preset':'sbass','clips':[{'start':0,'len':16,'notes':[{'p':31,'s':0,'l':6,'v':.9},{'p':34,'s':6,'l':6,'v':.8}]}]}]})
al.run("selT=S.tracks[1].id;renderFx();1");al.page.wait_for_timeout(900)
D='.dev.idev.pbx'
def box():return json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:Math.max(0,r.left),y:r.top,width:Math.min(r.width,1600-Math.max(0,r.left)),height:r.height})})()"%D))
def shot(n):al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.mouse.move(5,5);al.page.wait_for_timeout(600);al.page.screenshot(path=os.path.join(out,n),clip=box())
I=lambda k:al.run("JSON.stringify(S.tracks[1].inst.%s)"%k)
def inside(tag):
    print('%-16s %s'%(tag,al.run("(()=>{const d=document.querySelector('%s'),R=d.getBoundingClientRect(),bad=[];for(const el of d.querySelectorAll('[data-c],button,select')){const r=el.getBoundingClientRect();if(!r.width)continue;if(r.left<R.left-1||r.right>R.right+1||r.top<R.top-1||r.bottom>R.bottom+1)bad.push((el.textContent||el.dataset.c||'').trim().slice(0,16))}return 'device '+Math.round(R.width)+' x '+Math.round(R.height)+', outside: '+JSON.stringify(bad)})()"%D)))
print('title order',al.run("JSON.stringify([...document.querySelector('%s .devh').children].map(e=>(e.className||e.tagName).toString().slice(0,12)))"%D))
inside('Tone');shot('sub_tone.png')
al.page.click(D+' [data-sbb="tab:p"]');al.page.wait_for_timeout(300);inside('Pitch and level');shot('sub_pitch.png')
al.page.click(D+' [data-sbb="tab:t"]');al.page.wait_for_timeout(300)
# every control has a plain tooltip, no em dash anywhere in the device
al.page.mouse.move(5,5);al.page.wait_for_timeout(300)
print('controls without a tooltip',al.run("JSON.stringify([...document.querySelectorAll('%s [data-c],%s button,%s select,%s canvas')].filter(e=>e.getBoundingClientRect().width&&!(e.title||e.dataset.tip||e.getAttribute('aria-label'))).map(e=>(e.textContent||e.dataset.c||e.tagName).trim().slice(0,14)))"%(D,D,D,D)))
print('em dash in device text or tooltips',al.run("(()=>{const d=document.querySelector('%s');let s=d.textContent;for(const e of d.querySelectorAll('[title]'))s+=e.title;return /—|–/.test(s+JSON.stringify(SBSTIP)+JSON.stringify(SBSPRE)+PRESETS.sbass.desc)})()"%D))
print('preset groups',al.run("JSON.stringify([...document.querySelectorAll('%s select[data-s=ipre] optgroup')].map(g=>g.label+' '+g.children.length))"%D))
# the picture is drawn once and only again when something changes
n0=al.run("SBSCV.get(S.tracks[1].inst).n");al.page.wait_for_timeout(1200);n1=al.run("SBSCV.get(S.tracks[1].inst).n")
al.run("S.tracks[1].inst.h3=40;sbsPush(S.tracks[1].inst);changed(false);1");al.page.wait_for_timeout(500);n2=al.run("SBSCV.get(S.tracks[1].inst).n")
print('picture paints: at rest',n1-n0,'in 1.2 s, after one knob change',n2-n1)
# presets
for k in ('k808','phone','psys'):
    al.run("(()=>{const s=document.querySelector('%s select[data-s=ipre]');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}))})()"%(D,k));al.page.wait_for_timeout(500);print('preset',k,I('ipk'),'drive',I('drv'),'small speakers',I('ss'));shot('sub_%s.png'%k)
al.run("undo();undo();undo();1");al.page.wait_for_timeout(300);print('after three undos: preset',I('ipk'))
# buttons
al.page.click(D+' [data-sbb="wv:q"]');al.page.wait_for_timeout(200);print('wave',I('wv'))
al.page.click(D+' [data-sbb="tab:p"]');al.page.wait_for_timeout(200);al.page.click(D+' [data-sbb="gm:a"]');al.page.wait_for_timeout(200);al.page.click(D+' [data-sbb="rt"]');al.page.wait_for_timeout(200)
al.run("(()=>{const s=document.querySelector('%s select[data-sbs=oc]');s.value='-1';s.dispatchEvent(new Event('change',{bubbles:true}))})()"%D);al.page.wait_for_timeout(200)
print('glide',I('gm'),'same start',I('rt'),'octave',I('oc'));al.run("undo();undo();undo();undo();1");al.page.wait_for_timeout(300);print('after undos: wave',I('wv'),'glide',I('gm'),'same start',I('rt'),'octave',I('oc'))
# duck to kick
al.page.click(D+' [data-sbb="tab:t"]');al.page.wait_for_timeout(200);al.page.click(D+' [data-sbb="duck"]');al.page.wait_for_timeout(400)
print('duck to kick: effects',al.run("JSON.stringify(S.tracks[1].fx.map(f=>f.type+' source '+trkById(f.p.src).name))"),'button',al.run("document.querySelector('%s [data-sbb=duck]').textContent"%D));shot('sub_duck.png')
al.page.click(D+' [data-sbb="duck"]');al.page.wait_for_timeout(400);print('duck off: effects',al.run("S.tracks[1].fx.length"));al.run("undo();1");al.page.wait_for_timeout(300);print('undo: effects',al.run("S.tracks[1].fx.length"));al.run("undo();1");al.page.wait_for_timeout(300)
# shut and open
al.run("(document.querySelector('%s .duar')||{click(){}}).click();1"%D);al.page.wait_for_timeout(500);inside('shut');shot('sub_shut.png');al.run("(document.querySelector('%s .duar')||{click(){}}).click();1"%D);al.page.wait_for_timeout(500);inside('open again')
# playing: the bars light up
al.run("pos=0;1");al.page.keyboard.press('Space');al.page.wait_for_timeout(1500);shot('sub_playing.png');al.page.keyboard.press('Space');al.page.wait_for_timeout(400)
# browser
print('in the instrument browser',al.run("JSON.stringify(IBG.filter(g=>g[2].includes('sbass')).map(g=>g[0]+': '+g[2].join(' ')))"),'name',al.run("PRESETS.sbass.name"))
al.run("openBrowser(S.tracks[1]);1");al.page.wait_for_timeout(2500)
r=al.run("(()=>{const el=document.querySelector('#ib [data-k=sbass]');if(!el)return '';el.scrollIntoView({block:'center'});return '1'})()")
if r:
    al.page.wait_for_timeout(1000);b=json.loads(al.run("(()=>{const r=document.querySelector('#ib [data-k=sbass]').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:r.width,height:r.height})})()"));al.page.screenshot(path=os.path.join(out,'sub_browser.png'),clip=b)
print('browser tile found',bool(r),'errors',al.errors);al.stop()
