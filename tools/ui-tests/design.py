"""One design language (v0.182, task C): what the new title row and the gain bar do. python3 tools/ui-tests/design.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.build({'tracks':[{'name':'B','preset':'pluck','clips':[{'start':0,'len':4,'notes':[{'p':60,'s':0,'l':1,'v':.9}]}]}]})
R=al.run;W=al.page.wait_for_timeout
R("(()=>{const t=S.tracks[0];t.fx=[mkFx('comp'),mkFx('delay'),mkFx('reverb')];t.fx[1].on=false;selT=t.id;changed(true);renderFx();return 1})()");W(600)
FX="S.tracks[0].fx.map(f=>f.type+(f.on?'':'(off)')).join(' > ')"
print('chain',R(FX))
# 1. Change on an effect: the browser opens, the pick takes its place
al.page.click('#fxin .dev[data-d=fx]:nth-of-type(3) .duchg') if False else R("fxin.querySelectorAll('.dev[data-d=fx]')[1].querySelector('.duchg').click();1");W(500)
print('browser open',R("!$('#ib').hidden"),'| title:',R("$('#ibT').textContent"),'| button:',R("$('#ibAdd').textContent"),'| selected',R("ib.sel"))
al.page.screenshot(path=os.path.join(out,'design_change_browser.png'))
R("ib.sel='phaser';renderIB();1");W(300);al.page.click('#ibAdd');W(500)
print('after Use     ',R(FX),'| browser shut',R("$('#ib').hidden"))
R("undo();1");W(300);print('after undo    ',R(FX))
R("fxin.querySelectorAll('.dev[data-d=fx]')[1].querySelector('.duchg').click();1");W(400);al.page.click('#ibCancel');W(300);print('after Cancel  ',R(FX))
# adding an effect the usual way still adds at the end
R("openFxBrowser(S.tracks[0]);ib.sel='chorus';renderIB();1");W(300);al.page.click('#ibAdd');W(400);print('plain Add     ',R(FX));R("undo();1");W(300)
# 2. previous and next preset of an effect
P=lambda:R("S.tracks[0].fx[0].p.pre+' ratio '+S.tracks[0].fx[0].p.ratio")
print('comp preset',P());R("fxin.querySelector('.dev[data-d=fx] [data-dup=next]').click();1");W(300);a=P();R("fxin.querySelector('.dev[data-d=fx] [data-dup=next]').click();1");W(300);b=P();R("fxin.querySelector('.dev[data-d=fx] [data-dup=prev]').click();1");W(300);print('  next',a,'| next',b,'| previous',P(),'| menu shows',R("fxin.querySelector('.dev[data-d=fx] .kpre select').selectedOptions[0].textContent"))
# 3. presets of a basic instrument
I=lambda:R("(()=>{const I=S.tracks[0].inst;return [I.ipk,I.wave,I.cutoff,I.res,I.a,I.d,I.s,I.r,I.det,I.gain].join(' ')})()")
print('pluck',I(),'| menu',R("[...fxin.querySelector('.dev[data-d=inst] select[data-s=ipre]').options].map(o=>o.textContent).join(', ')"))
al.page.select_option('#fxin .dev[data-d=inst] select[data-s=ipre]','bright');W(400);print('  Bright pluck',I())
R("fxin.querySelector('.dev[data-d=inst] [data-ip=next]').click();1");W(400);print('  next        ',I())
al.page.select_option('#fxin .dev[data-d=inst] select[data-s=ipre]','def');W(400);print('  Default     ',I(),'| same as a new Pluck',R("(()=>{const I=S.tracks[0].inst,P=PRESETS.pluck;return ['wave','cutoff','res','a','d','s','r','det','gain'].every(k=>I[k]===P[k])})()"))
R("undo();undo();undo();1");W(300);print('  three undos ',I())
# 4. drum kits
R("(()=>{const t=S.tracks[0];for(const k of Object.keys(t.inst))delete t.inst[k];Object.assign(t.inst,JSON.parse(JSON.stringify(PRESETS.drums)),{preset:'drums'});t.fx=[];changed(true);renderFx();return 1})()");W(500)
K=lambda:R("S.tracks[0].inst.pads.slice(0,4).map(p=>p.type+(p.kp?':'+p.kp:'')+' '+p.tune+'/'+p.dec.toFixed(2)+'/'+p.tone.toFixed(2)).join(' | ')")
print('kit menu',R("[...fxin.querySelector('.dev[data-d=inst] select[data-s=ipre]').options].map(o=>o.textContent).join(', ')"));print('  default',K())
al.page.select_option('#fxin .dev[data-d=inst] select[data-s=ipre]','tight');W(400);print('  tight  ',K())
al.page.select_option('#fxin .dev[data-d=inst] select[data-s=ipre]','def');W(400);print('  default',K(),'| equal to defaultPads()',R("JSON.stringify(S.tracks[0].inst.pads)===JSON.stringify(defaultPads())"))
# 5. the gain bar is the device gain
R("(()=>{const t=S.tracks[0];for(const k of Object.keys(t.inst))delete t.inst[k];Object.assign(t.inst,JSON.parse(JSON.stringify(PRESETS.pluck)),{preset:'pluck'});t.fx=[mkFx('comp')];changed(true);renderFx();return 1})()");W(500)
print('gain bars',R("[...fxin.querySelectorAll('.dug [data-c]')].map(e=>e.dataset.c.replace(/:[a-z0-9]{6,}$/,':id')+'='+e.querySelector('output').textContent).join(', ')"),'| old title sliders left',R("fxin.querySelectorAll('.dgain').length"))
R("(()=>{const f=S.tracks[0].fx[0];CT.get('fx:og:'+f.id).set(-6);CT.get('fx:og:inst').set(3);renderFx();return 1})()");W(300)
print('  set by hand: effect og',R("S.tracks[0].fx[0].p.og"),'instrument og',R("S.tracks[0].inst.og"),'| shown',R("[...fxin.querySelectorAll('.dug output')].map(o=>o.textContent).join(', ')"))
R("fxin.querySelector('.dev[data-d=fx]').scrollIntoView({inline:'end'});1");W(300)
b=json.loads(R("(()=>{const r=fxin.querySelector('.dev[data-d=fx] .dug .vt').getBoundingClientRect();return JSON.stringify([r.left+r.width/2,r.top,r.height])})()"))
al.page.mouse.move(b[0],b[1]+b[2]/2);al.page.mouse.down();al.page.mouse.move(b[0],b[1]+b[2]/2-30,steps=4);al.page.mouse.up();W(300);print('  dragged up 30 px: effect og',R("S.tracks[0].fx[0].p.og.toFixed(2)"))
al.page.mouse.dblclick(b[0],b[1]+b[2]/2);W(300);print('  double-click: effect og',R("S.tracks[0].fx[0].p.og"))
# 6. the arrow, with animations on and off
for red in (False,True):
    R("AT.reduce=%s;1"%('true' if red else 'false'))
    for sel,get in (('.dev[data-d=inst]',"S.tracks[0].inst.kOpen"),('.dev[data-d=fx]',"S.tracks[0].fx[0].kOpen")):
        w0=R("fxin.querySelector('%s').offsetWidth"%sel);al.page.click('#fxin %s :is(.duar,.dveye)'%sel);W(450);w1=R("fxin.querySelector('%s').offsetWidth"%sel);k1=R(get);t1=R("fxin.querySelector('%s :is(.duar,.dveye)').getAttribute('aria-label')"%sel)
        al.page.click('#fxin %s :is(.duar,.dveye)'%sel);W(450);w2=R("fxin.querySelector('%s').offsetWidth"%sel)
        print('arrow %-18s animations %s: width %s > %s > %s, kOpen when shut %s, label when shut "%s", attribute %s'%(sel,'off' if red else 'on',w0,w1,w2,k1,t1,R("fxin.querySelector('%s :is(.duar,.dveye)').hasAttribute('data-kt')||fxin.querySelector('%s :is(.duar,.dveye)').hasAttribute('data-ikt')"%(sel,sel))))
R("AT.reduce=false;1")
# shut in the saved project, open again after loading
al.page.click('#fxin .dev[data-d=fx] :is(.duar,.dveye)');W(450);print('saved with the project: kOpen',R("JSON.parse(JSON.stringify(S)).tracks[0].fx[0].kOpen"),'| title when shut:',R("[...fxin.querySelector('.dev[data-d=fx] .devh').children].filter(e=>e.getBoundingClientRect().width>0&&!e.classList.contains('dusp')).map(e=>e.className||e.tagName).join(' ')"))
al.page.screenshot(path=os.path.join(out,'design_shut.png'));al.page.click('#fxin .dev[data-d=fx] :is(.duar,.dveye)');W(450)
# 7. title text has no em dash, every title control has a tooltip
print('em dashes in titles',R("[...fxin.querySelectorAll('.dev.du .devh [title]')].filter(e=>e.title.includes('\\u2014')).length"),'| title buttons without tooltip',R("[...fxin.querySelectorAll('.dev.du .devh button')].filter(e=>!e.title&&!e.getAttribute('aria-label')).map(e=>e.textContent).join(',')||'none'"))
# 8. the picture of the basic instrument follows the knobs
h=lambda:R("(()=>{const c=fxin.querySelector('canvas.duviz'),g=c.getContext('2d'),d=g.getImageData(0,0,c.width,c.height).data;let s=0;for(let i=0;i<d.length;i+=97)s=(s*31+d[i])>>>0;return s})()")
W(400);a=h();R("S.tracks[0].inst.cutoff=400;S.tracks[0].inst.a=.5;1");W(400);b2=h();print('basic picture changes with Cutoff and Attack:',a!=b2)
al.page.screenshot(path=os.path.join(out,'design_whole.png'))
# the instrument browser still shows the device
R("openBrowser(S.tracks[0]);1");W(900);al.page.screenshot(path=os.path.join(out,'design_inst_browser.png'));al.page.click('#ibCancel')
print('errors',al.errors);al.stop()
