"""Change with live browsing (v0.183, task D): the browsers in change mode, driven with the mouse and the keyboard.
python3 tools/ui-tests/change_live.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
notes=[{'p':57+(i%4)*3,'s':i*.5,'l':.45,'v':.9} for i in range(64)]+[{'p':45,'s':i*8,'l':7.9,'v':.8} for i in range(4)]
al.build({'bpm':120,'tracks':[{'name':'Lead','preset':'pluck','clips':[{'start':0,'len':32,'notes':notes}]},{'name':'Other','preset':'sub','clips':[{'start':0,'len':32,'notes':[{'p':36,'s':0,'l':1,'v':.5}]}]}]})
R=al.run;W=al.page.wait_for_timeout;M=al.page.mouse;K=al.page.keyboard
al.page.on('pageerror',lambda e:print('  PAGE ERROR',str(getattr(e,'stack',e))[:700]))
R("(()=>{const t=S.tracks[0];t.fx=[mkFx('comp'),mkFx('delay'),mkFx('reverb')];t.fx[1].on=true;t.fx[1].p.feedback=61;t.inst.cutoff=1234;t.inst.r=.33;S.loop=true;selT=t.id;UNDO=[];REDO=[];changed(true);renderFx();ensureCtx();syncGraph();return 1})()");W(700)
# a level meter on the track: the loudest 20 ms block (RMS, dB) seen in the next ms milliseconds
R("window.__lv=function(ms){const N=NODES.get(S.tracks[0].id);if(!N.__a){N.__a=ctx.createAnalyser();N.__a.fftSize=1024;N.pan.connect(N.__a)}const a=N.__a,b=new Float32Array(1024);let mx=0,mn=9;return new Promise(res=>{const t0=performance.now(),iv=setInterval(()=>{a.getFloatTimeDomainData(b);let s=0;for(const x of b)s+=x*x;const r=Math.sqrt(s/1024);mx=Math.max(mx,r);mn=Math.min(mn,r);if(performance.now()-t0>ms){clearInterval(iv);res([+(20*Math.log10(mx+1e-9)).toFixed(1),+(20*Math.log10(mn+1e-9)).toFixed(1)])}},20)})};1")
LV=lambda ms=700:al.page.evaluate("ms=>window.__lv(ms)",ms)
INST="S.tracks[0].inst.preset";CH="S.tracks[0].fx.map(f=>f.type+(f.on?'':'(off)')).join(' > ')"
SNAP=lambda:R("JSON.stringify([S.tracks[0].inst,S.tracks[0].fx,S.tracks[0].name])")
R("UI.ibView='cards';1")  # this test drives today's plane of live cards (the catalogue, DS-B1a, has its own test taskDS_B1a.py)
def pt(k,mode='tile'):
    """a point on tile k that the mouse can really hit (the plane is moved so the tile is in view)"""
    R("chgSee(document.querySelector('#ibPlane .ibc[data-k=\"%s\"]'));1"%k);W(600)
    for n in range(8):
        r=json.loads(R("""(()=>{const c=document.querySelector('#ibPlane .ibc[data-k="%s"]'),want='%s',r=(want==='name'?c.querySelector('.ibdl'):want==='pic'?c.querySelector('.ibdv'):c).getBoundingClientRect(),P=[];
          const add=(x,y)=>{const e=document.elementFromPoint(x,y);if(e&&c.contains(e))P.push([x,y,e.tagName+'.'+(e.className&&e.className.baseVal!==undefined?e.className.baseVal:e.className)])};
          for(const fy of [.5,.3,.7,.15,.85])for(const fx of [.5,.3,.7,.15,.85,.05])add(r.left+r.width*fx,r.top+r.height*fy);return JSON.stringify(P[0]||null)})()"""%(k,mode)))
        if r:break
        W(300)
    if n:print('    (tile %s was free to click after %d more ms)'%(k,n*300))
    if not r:
        al.page.screenshot(path=os.path.join(out,'change_fail.png'));print(R("(()=>{const c=document.querySelector('#ibPlane .ibc[data-k=\"%s\"]'),r=c.getBoundingClientRect(),e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return JSON.stringify([r.left,r.top,r.width,r.height,e&&e.tagName+'.'+e.className+'#'+e.id,IBV2])})()"%k))
    assert r,'no free point on tile '+k
    return r
def click(k,mode='tile'):
    x,y,e=pt(k,mode);M.click(x,y);return e
def dbl(k,mode='tile'):
    x,y,e=pt(k,mode);M.dblclick(x,y);return e
def open_inst():
    R("fxin.querySelector('.dev[data-d=inst]').scrollIntoView({inline:'start'});1");W(200)
    b=json.loads(R("(()=>{const r=fxin.querySelector('.dev[data-d=inst] .duchg').getBoundingClientRect();return JSON.stringify([r.left+r.width/2,r.top+r.height/2])})()"));M.click(*b);W(700)
def open_fx(i=1):
    R("fxin.querySelectorAll('.dev[data-d=fx]')[%d].scrollIntoView({inline:'center'});1"%i);W(200)
    b=json.loads(R("(()=>{const r=fxin.querySelectorAll('.dev[data-d=fx]')[%d].querySelector('.duchg').getBoundingClientRect();return JSON.stringify([r.left+r.width/2,r.top+r.height/2])})()"%i));M.click(*b);W(700)
STATE=lambda:R("'open '+!$('#ib').hidden+' | '+$('#ibT').textContent+' | button '+$('#ibAdd').textContent+' | selected '+ib.sel+' | change mode '+!!(CHG&&ib.chg)")
before=SNAP()
print('== INSTRUMENT, song stopped ==')
open_inst();print(STATE());print('  the open tile is the track\'s own device:',R("ib.t.inst===S.tracks[0].inst"),'| cutoff shown',R("ib.t.inst.cutoff"),'| hint:',R("$('#ibFoot').textContent"))
al.page.screenshot(path=os.path.join(out,'change_inst_open.png'))
for k in ('saw','reese','wtab'):
    e=click(k);lv=LV(600);print('  click %-6s (hit %s): track holds %-6s | level %s dB | undo steps %s | controls left in the device behind the browser %s'%(k,e[:22],R(INST),lv[0],R("UNDO.length"),R("fxin.querySelectorAll('.dev[data-d=inst] [data-c]').length")));W(500)
al.page.screenshot(path=os.path.join(out,'change_inst_swapped.png'))
print('== INSTRUMENT, song playing ==')
R("pos=0;start();1");W(900);print('  playing, level',LV(500))
for k in ('pad','keys','acid','orb','pluck'):
    R("window.__sw=0;1");t=R("(()=>{const c=document.querySelector('#ibPlane .ibc[data-k=\"%s\"]');return 1})()"%k);e=click(k);lv=LV(900);print('  click %-6s: track holds %-6s | loudest %s dB, quietest 20 ms %s dB | playing %s'%(k,R(INST),lv[0],lv[1],R("play.on")))
print('  back on the original tile: same settings as before the visit:',json.loads(SNAP())[0]==json.loads(before)[0])
click('strings');W(500);print('  now',R(INST))
e=dbl('plant','pic');W(600);print('  double-click on the picture of plant (hit %s): browser shut %s | track holds %s | name %s | undo steps %s | level %s'%(e[:22],R("$('#ib').hidden"),R(INST),R("S.tracks[0].name"),R("UNDO.length"),LV(700)))
al.page.screenshot(path=os.path.join(out,'change_inst_kept.png'))
R("undo();1");W(500);print('  one undo: same as before the visit:',SNAP()==before,'| holds',R(INST),'| level',LV(700))
R("redo();1");W(400);print('  redo: holds',R(INST));R("undo();1");W(400)
print('== INSTRUMENT, Escape ==')
open_inst();click('square');W(300);click('emit');W(300);print('  after two clicks: holds',R(INST),LV(500));K.press('Escape');W(600)
print('  Escape: browser shut %s | same as before %s | holds %s | undo steps %s | level %s'%(R("$('#ib').hidden"),SNAP()==before,R(INST),R("UNDO.length"),LV(700)))
open_inst();click('saw');W(300);M.click(*json.loads(R("(()=>{const r=$('#ibCancel').getBoundingClientRect();return JSON.stringify([r.left+r.width/2,r.top+r.height/2])})()")));W(500);print('  Cancel button: same as before',SNAP()==before)
print('== INSTRUMENT, arrow keys and Enter ==')
open_inst();seq=[]
for key in ('ArrowRight','ArrowDown','ArrowLeft','ArrowUp','ArrowRight'):
    K.press(key);W(350);seq.append(key[5:]+'>'+R(INST)+('' if R("ib.sel===S.tracks[0].inst.preset") else '(!)'))
print('  ',' '.join(seq),'| level',LV(600));al.page.screenshot(path=os.path.join(out,'change_inst_arrows.png'))
kept=R(INST);K.press('Enter');W(500);print('  Enter: browser shut %s | holds %s (was %s) | undo steps %s'%(R("$('#ib').hidden"),R(INST),kept,R("UNDO.length")));R("undo();1");W(400);print('  undo: same as before',SNAP()==before)
print('== INSTRUMENT, double-click on the name, stopped ==')
R("stop();pos=0;1");W(400);open_inst();e=dbl('reese','name');W(500);print('  double-click on the name of reese (hit %s): shut %s | holds %s | level %s'%(e[:22],R("$('#ib').hidden"),R(INST),LV(600)));R("undo();1");W(400);print('  undo: same as before',SNAP()==before)
print('== EFFECT, song stopped ==')
print('  chain',R(CH));open_fx(1);print(STATE());print('  the open tile is the track\'s own effect:',R("ib.t.fx[0]===S.tracks[0].fx[1]"),'| feedback',R("ib.t.fx[0].p.feedback"))
al.page.screenshot(path=os.path.join(out,'change_fx_open.png'))
for k in ('phaser','drive','tdelay'):
    click(k);lv=LV(800);print('  click %-7s: chain %s | node there %s | level %s dB'%(k,R(CH),R("!!NODES.get(S.tracks[0].id).fxm.get(S.tracks[0].fx[1].id)&&NODES.get(S.tracks[0].id).fxm.size"),lv[0]));W(300)
al.page.screenshot(path=os.path.join(out,'change_fx_swapped.png'))
print('== EFFECT, song playing ==')
R("pos=0;start();1");W(900)
for k in ('crush','chorus','reverb','delay'):
    click(k);lv=LV(900);print('  click %-7s: chain %s | loudest %s dB, quietest %s dB'%(k,R(CH),lv[0],lv[1]))
print('  back on the original tile: same as before',SNAP()==before)
click('filter');W(300);e=dbl('blur','pic');W(600);print('  double-click on the picture of blur (hit %s): shut %s | chain %s | undo steps %s | level %s'%(e[:22],R("$('#ib').hidden"),R(CH),R("UNDO.length"),LV(600)))
R("undo();1");W(500);print('  one undo: same as before',SNAP()==before,'|',R(CH))
open_fx(1);click('eq');W(300);click('ott');W(300);print('  two clicks:',R(CH));K.press('Escape');W(600);print('  Escape: same as before',SNAP()==before,'|',R(CH),'| undo steps',R("UNDO.length"),'| level',LV(600))
open_fx(1);seq=[]
for key in ('ArrowRight','ArrowDown','ArrowLeft'):
    K.press(key);W(350);seq.append(key[5:]+'>'+R("S.tracks[0].fx[1].type"))
print('  arrows:',' '.join(seq),'|',R(CH));K.press('Enter');W(500);print('  Enter: shut',R("$('#ib').hidden"),'|',R(CH));R("undo();1");W(400);print('  undo: same as before',SNAP()==before)
# an effect that is switched off keeps that; the first and the last place
R("S.tracks[0].fx[2].on=false;changed(true);1");W(400);open_fx(2);click('phaser');W(300);K.press('Enter');W(500);print('  last place, switched off:',R(CH));R("undo();1");W(300);open_fx(0);click('gate');W(300);K.press('Enter');W(500);print('  first place:',R(CH));R("undo();S.tracks[0].fx[2].on=true;changed(true);stop();1");W(400)
print('== the usual browsers still work ==')
R("openBrowser(null);1");W(600);print('  add instrument:',R("$('#ibT').textContent+' | '+$('#ibAdd').textContent+' | change mode '+!!(CHG&&ib.chg)"));click('saw');W(400);K.press('Enter');W(500);print('  tracks',R("S.tracks.map(t=>t.name).join(', ')"));R("undo();1");W(300)
R("openFxBrowser(S.tracks[0]);1");W(600);click('chorus');W(400);dbl('chorus','name');W(500);print('  add effect:',R(CH));R("undo();1");W(300)
print('== speed (ms) ==')
print('  open Change on the instrument: first',R("(()=>{$('#ibList').innerHTML='';$('#ibList').dataset.k2='';const a=performance.now();openBrowser(S.tracks[0]);const b=performance.now()-a;$('#ib').hidden=true;return b.toFixed(0)})()"),end=' ');W(300)
print('| again',R("(()=>{const a=performance.now();openBrowser(S.tracks[0]);return (performance.now()-a).toFixed(0)})()"));W(300)
print('  one swap, stopped (the whole click):',R("(()=>{const o=[];for(const k of ['saw','pad','wtab','pluck']){const a=performance.now();document.querySelector('#ibPlane .ibc[data-k='+k+']').click();o.push((performance.now()-a).toFixed(0))}return o.join(', ')})()"))
print('  of that, the swap on the track:',R("(()=>{const o=[];for(const k of ['saw','pad','wtab','pluck']){ib.sel=k;const a=performance.now();chgSwap(k);o.push((performance.now()-a).toFixed(1))}return o.join(', ')})()"));K.press('Escape');W(400)
print('  same as before',SNAP()==before)
print('errors',al.errors);al.stop()
