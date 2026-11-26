"""Psy Bass (v0.190): the device in the page. python3 tools/ui-tests/psybass.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.build({'bpm':145,'tracks':[{'name':'Kick','preset':'kick','clips':[{'start':0,'len':16,'notes':[{'p':36,'s':i,'l':.5,'v':1} for i in range(16)]}]},
  {'name':'Bass','preset':'psyb','clips':[{'start':0,'len':16,'notes':[{'p':33,'s':i*.25,'l':.25,'v':.8 if i%4==1 else 1} for i in range(64) if i%4]}]}]})
al.run("selT=S.tracks[1].id;renderFx();1");al.page.wait_for_timeout(900)
D='.dev.idev.pbx'
def box():return json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:Math.max(0,r.left),y:r.top,width:Math.min(r.width,1600-Math.max(0,r.left)),height:r.height})})()"%D))
def shot(n):al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.mouse.move(5,5);al.page.wait_for_timeout(600);al.page.screenshot(path=os.path.join(out,n),clip=box())
I=lambda k:al.run("JSON.stringify(S.tracks[1].inst.%s)"%k)
def inside(tag):
    print('%-16s %s'%(tag,al.run("(()=>{const d=document.querySelector('%s'),R=d.getBoundingClientRect(),bad=[];for(const el of d.querySelectorAll('[data-c],button,select')){const r=el.getBoundingClientRect();if(!r.width)continue;if(r.left<R.left-1||r.right>R.right+1||r.top<R.top-1||r.bottom>R.bottom+1)bad.push((el.textContent||el.dataset.c||'').trim().slice(0,16))}return 'device '+Math.round(R.width)+' x '+Math.round(R.height)+', outside: '+JSON.stringify(bad)})()"%D)))
print('title order',al.run("JSON.stringify([...document.querySelector('%s .devh').children].map(e=>(e.className||e.tagName).toString().slice(0,12)))"%D))
inside('Roll and gate');shot('psb_roll.png')
al.page.click(D+' [data-psb="tab:s"]');al.page.wait_for_timeout(300);inside('Sound');shot('psb_sound.png')
al.page.click(D+' [data-psb="tab:e"]');al.page.wait_for_timeout(300);inside('Envelopes');shot('psb_env.png')
al.page.click(D+' [data-psb="tab:r"]');al.page.wait_for_timeout(300)
al.page.mouse.move(5,5);al.page.wait_for_timeout(300)
def tips():
    return al.run("JSON.stringify([...document.querySelectorAll('%s [data-c],%s button,%s select,%s canvas')].filter(e=>e.getBoundingClientRect().width&&!(e.title||e.dataset.tip||e.getAttribute('aria-label'))).map(e=>(e.textContent||e.dataset.c||e.tagName).trim().slice(0,14)))"%(D,D,D,D))
print('controls without a tooltip (roll tab)',tips())
for tb in 'se':
    al.page.click(D+' [data-psb="tab:%s"]'%tb);al.page.wait_for_timeout(250);print('controls without a tooltip (tab %s)'%tb,tips())
al.page.click(D+' [data-psb="tab:r"]');al.page.wait_for_timeout(250)
print('em dash in device text or tooltips',al.run("(()=>{const d=document.querySelector('%s');let s=d.textContent;for(const e of d.querySelectorAll('[title]'))s+=e.title;return /\u2014|\u2013/.test(s+JSON.stringify(PSBTIP)+JSON.stringify(PSBPRE)+JSON.stringify(PSBPAT)+PRESETS.psyb.desc)})()"%D))
print('preset groups',al.run("JSON.stringify([...document.querySelectorAll('%s select[data-s=ipre] optgroup')].map(g=>g.label+' '+g.children.length))"%D))
print('presets without a tooltip',al.run("JSON.stringify([...document.querySelectorAll('%s select[data-s=ipre] option')].filter(o=>!o.title).map(o=>o.value))"%D))
n0=al.run("PSBCV.get(S.tracks[1].inst).n");al.page.wait_for_timeout(1200);n1=al.run("PSBCV.get(S.tracks[1].inst).n")
al.run("S.tracks[1].inst.cut=600;psbPush(S.tracks[1].inst);changed(false);1");al.page.wait_for_timeout(500);n2=al.run("PSBCV.get(S.tracks[1].inst).n")
print('picture paints: at rest',n1-n0,'in 1.2 s, after one knob change',n2-n1)
for k in ('dark','progoff','trip','goa'):
    al.run("(()=>{const s=document.querySelector('%s select[data-s=ipre]');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}))})()"%(D,k));al.page.wait_for_timeout(500);print('preset',k,I('ipk'),'cutoff',I('cut'),'pattern',I('ppk'),I('pat'),'steps per beat',I('pdv'));shot('psb_%s.png'%k)
al.run("undo();undo();undo();undo();1");al.page.wait_for_timeout(300);print('after four undos: preset',I('ipk'),'pattern',I('pat'))
# step row: click step 1 (off -> on), step 2 twice (on -> accent -> off), octave of step 4
al.page.click(D+' [data-psbs="0"]');al.page.wait_for_timeout(150);al.page.click(D+' [data-psbs="1"]');al.page.wait_for_timeout(150);al.page.click(D+' [data-psbs="1"]');al.page.wait_for_timeout(150);al.page.click(D+' [data-psbo="3"]');al.page.wait_for_timeout(150)
print('after step clicks: pattern',I('pat'),'octaves',I('poc'),'pattern name',I('ppk'))
al.run("undo();undo();undo();undo();1");al.page.wait_for_timeout(300);print('after four undos: pattern',I('pat'),'octaves',I('poc'),I('ppk'))
al.page.click(D+' [data-psb="pon"]');al.page.wait_for_timeout(200);al.page.click(D+' [data-psb="go"]');al.page.wait_for_timeout(200);al.page.click(D+' [data-psb="pdv:3"]');al.page.wait_for_timeout(300)
print('roll',I('pon'),'gate',I('go'),'steps per beat',I('pdv'),'pattern',I('ppk'),I('pat'));shot('psb_triplet.png')
al.run("(()=>{const s=document.querySelector('%s select[data-pss=ppk]');s.value='gal';s.dispatchEvent(new Event('change',{bubbles:true}))})()"%D);al.page.wait_for_timeout(300);print('pattern menu: galloping',I('ppk'),I('pat'),I('pdv'))
al.run("undo();undo();undo();undo();1");al.page.wait_for_timeout(300);print('after undos: roll',I('pon'),'gate',I('go'),'steps per beat',I('pdv'),I('ppk'))
al.page.click(D+' [data-psb="tab:s"]');al.page.wait_for_timeout(200);al.page.click(D+' [data-psb="ft:12"]');al.page.wait_for_timeout(200);al.page.click(D+' [data-psb="rt"]');al.page.wait_for_timeout(200)
al.run("(()=>{const s=document.querySelector('%s select[data-pss=so]');s.value='1';s.dispatchEvent(new Event('change',{bubbles:true}))})()"%D);al.page.wait_for_timeout(200)
print('filter',I('ft'),'restart',I('rt'),'sub octave',I('so'));al.run("undo();undo();undo();1");al.page.wait_for_timeout(300);print('after undos: filter',I('ft'),'restart',I('rt'),'sub octave',I('so'))
al.page.click(D+' [data-psb="tab:r"]');al.page.wait_for_timeout(200)
al.run("(document.querySelector('%s .duar')||{click(){}}).click();1"%D);al.page.wait_for_timeout(500);inside('shut');shot('psb_shut.png');al.run("(document.querySelector('%s .duar')||{click(){}}).click();1"%D);al.page.wait_for_timeout(500);inside('open again')
al.run("pos=0;1");al.page.keyboard.press('Space');al.page.wait_for_timeout(1500);shot('psb_playing.png');al.page.keyboard.press('Space');al.page.wait_for_timeout(400)
# live keys with the roll on: a held key plays the pattern, no errors
al.run("S.tracks[1].inst.pon=true;psbPush(S.tracks[1].inst);1");h=al.run("(()=>{window._h=voiceOn(S.tracks[1],33,.9);return !!window._h})()");al.page.wait_for_timeout(800);al.run("window._h&&window._h.off();1");al.page.wait_for_timeout(300);print('live key with the roll on: started',h,'errors',al.errors)
al.run("S.tracks[1].inst.pon=false;1")
print('in the instrument browser',al.run("JSON.stringify(IBG.filter(g=>g[2].includes('psyb')).map(g=>g[0]+': '+g[2].join(' ')))"),'name',al.run("PRESETS.psyb.name"))
al.run("openBrowser(S.tracks[1]);1");al.page.wait_for_timeout(2500)
r=al.run("(()=>{const el=document.querySelector('#ib [data-k=psyb]');if(!el)return '';el.scrollIntoView({block:'center'});return '1'})()")
if r:
    al.page.wait_for_timeout(1000);b=json.loads(al.run("(()=>{const r=document.querySelector('#ib [data-k=psyb]').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:r.width,height:r.height})})()"));al.page.screenshot(path=os.path.join(out,'psb_browser.png'),clip=b)
print('browser tile found',bool(r),'errors',al.errors);al.stop()
