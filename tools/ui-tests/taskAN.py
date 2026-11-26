# task AN (v0.215): zoom and scroll keys of the arrangement and their settings (Settings > Interface > Layout > Zoom and scroll).
#   python3 tools/ui-tests/taskAN.py index.html [outdir]
import sys,os,json,math
import numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(f);al.start();pg=al.page;R=al.run;JL=lambda v:json.loads(v) if isinstance(v,str) else v
ok=True
def chk(name,cond,info=''):
    global ok;ok&=bool(cond);print(('PASS ' if cond else 'FAIL ')+name,info)
print('version',al.version,'errors',al.errors)
al.tracks=json.loads(R("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
rms=lambda x:float(np.sqrt(np.mean(x.astype(np.float64)**2)));db=lambda v:20*np.log10(max(v,1e-15))
kx,_=al.render(b0=64,b1=96,only='Kick');bx,_=al.render(b0=64,b1=96,only='Bass');kd,bd=db(rms(kx)),db(rms(bx))
print('Fractals Kick %.5f dB  Bass %.5f dB'%(kd,bd))
chk('Fractals levels unchanged',(abs(kd+9.75669)<2e-5 and abs(bd+25.48699)<2e-5) or (abs(kd+19.05560)<2e-5 and abs(bd+35.48685)<2e-5))  # from v0.220 the song opens with its master at -10 dB (task AI): Kick -19.05560, Bass -35.48685
R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();if(play.on)stop();UI.follow=false})()")
Vw=lambda:JL(R("JSON.stringify({x:V.x,y:V.y,ppb:V.ppb,th:V.th})"))
def setv(x=80,ppb=24,th=96,y=0):
    R("(()=>{SZ.clear();V.x=%f;V.ppb=%f;V.th=%f;V.y=%f;clampV();dirty=true})()"%(x,ppb,th,y));pg.wait_for_timeout(120)
G=JL(R("(()=>{const r=arr.getBoundingClientRect();return JSON.stringify({l:r.left,t:r.top,w:r.width,h:r.height,X0:X0,AY:AY,Z:ZOOM})})()"));print('arr',G)
PX,PY=G['l']+(G['X0']+500)*G['Z'],G['t']+(G['AY']+230)*G['Z']
under=lambda:JL(R("(()=>{const r=arr.getBoundingClientRect(),x=(%f-r.left)/ZOOM,y=(%f-r.top)/ZOOM;return JSON.stringify({b:V.x+(x-X0)/V.ppb,r:(y-AY+V.y)/V.th})})()"%(PX,PY)))
def wheel(mods,dx,dy,n=1,x=None,y=None,wait=450,gap=0):
    pg.mouse.move(PX if x is None else x,PY if y is None else y)
    for m in mods:pg.keyboard.down(m)
    for i in range(n):
        pg.mouse.wheel(dx,dy)
        if gap:pg.wait_for_timeout(gap)
    for m in mods:pg.keyboard.up(m)
    pg.wait_for_timeout(wait)
eq=lambda a,b,t=1e-6:abs(a-b)<=t*max(1,abs(b))
# ---- 1 default mapping, mouse wheel
setv();a=Vw();u0=under();wheel(['Control'],0,-100);b=Vw();u1=under()
chk('Ctrl + wheel: zoom, time and track height together',b['ppb']>a['ppb']*1.2 and b['th']>a['th']*1.05 and eq(b['ppb']/a['ppb'],b['th']/a['th'],1e-3),(round(b['ppb']/a['ppb'],3),round(b['th']/a['th'],3)))
chk('  anchored at the pointer within a pixel (time %.3f px, rows %.3f px)'%((u1['b']-u0['b'])*b['ppb'],(u1['r']-u0['r'])*b['th']),abs((u1['b']-u0['b'])*b['ppb'])<1 and abs((u1['r']-u0['r'])*b['th'])<1)
setv();a=Vw();u0=under();wheel(['Alt'],0,-100);b=Vw();u1=under()
chk('Option/Alt + wheel: track height only',b['th']>a['th']*1.1 and eq(b['ppb'],a['ppb']) and eq(b['x'],a['x']),round(b['th']/a['th'],3))
chk('  the row under the pointer stays (%.3f px)'%((u1['r']-u0['r'])*b['th']),abs((u1['r']-u0['r'])*b['th'])<1)
setv();a=Vw();u0=under();wheel(['Shift'],0,-100);b=Vw();u1=under()
chk('Shift + wheel: clip width only (time zoom, track height unchanged)',b['ppb']>a['ppb']*1.3 and eq(b['th'],a['th']) and eq(b['y'],a['y']),round(b['ppb']/a['ppb'],3))
chk('  anchored at the pointer within a pixel (%.4f px)'%((u1['b']-u0['b'])*b['ppb']),abs((u1['b']-u0['b'])*b['ppb'])<1)
cw=JL(R("(()=>{const t=S.tracks.findIndex(t=>t.clips.length),c=S.tracks[t].clips[0];return clipGeom(t,c).w/c.len})()"));chk('  clips are drawn wider (px per beat of a clip = view)',eq(cw,b['ppb'],1e-6),cw)
setv();a=Vw();wheel(['Shift'],-100,0);b=Vw();chk('Shift + wheel delivered as a sideways delta (browser swap) zooms the same',b['ppb']>a['ppb']*1.3 and eq(b['th'],a['th']))
setv();a=Vw();wheel(['Shift'],0,100);b=Vw();chk('Shift + wheel down: clips thinner',b['ppb']<a['ppb']/1.3 and eq(b['th'],a['th']),round(b['ppb']/a['ppb'],3))
# ---- 2 trackpad-like deltas: many small ones add up, smooth
setv();a=Vw();u0=under()
pg.mouse.move(PX,PY);pg.keyboard.down('Shift');seq=[]
for i in range(30):
    pg.mouse.wheel(0,-3);seq.append(JL(R("V.ppb")))
    pg.wait_for_timeout(8)
pg.keyboard.up('Shift');pg.wait_for_timeout(450);b=Vw();u1=under()
exp=math.exp(30*3*.0085);steps=[seq[i+1]/seq[i] for i in range(len(seq)-1)]
chk('trackpad: 30 small deltas add up exactly (x%.4f, expected x%.4f)'%(b['ppb']/a['ppb'],exp),eq(b['ppb']/a['ppb'],exp,2e-3))
chk('  no jumps: biggest step between two events x%.4f, never backwards'%max(steps),max(steps)<1.12 and min(steps)>=1-1e-9)
chk('  anchored within a pixel (%.4f px)'%((u1['b']-u0['b'])*b['ppb']),abs((u1['b']-u0['b'])*b['ppb'])<1)
setv();a=Vw();u0=under();wheel(['Control'],0,-2.5,n=20,gap=8);b=Vw();u1=under();chk('trackpad Ctrl + scroll: smooth zoom, anchored (%.4f px)'%((u1['b']-u0['b'])*b['ppb']),b['ppb']>a['ppb']*1.3 and abs((u1['b']-u0['b'])*b['ppb'])<1)
setv();a=Vw();wheel(['Alt'],0,-2.5,n=20,gap=8);b=Vw();chk('trackpad Option + scroll: track height',b['th']>a['th']*1.1 and eq(b['ppb'],a['ppb']))
# frames of one wheel step: eased, several frames
setv();pg.mouse.move(PX,PY);pg.keyboard.down('Shift');pg.mouse.wheel(0,-100)
fr=JL(pg.evaluate("()=>new Promise(res=>{const o=[];let n=0;const f=()=>{o.push(window.AudioLab.run('V.ppb'));if(++n<25)requestAnimationFrame(f);else res(JSON.stringify(o))};requestAnimationFrame(f)})"));pg.keyboard.up('Shift')
d=sorted(set(round(v,4) for v in fr));chk('one wheel step is eased over several frames (%d different widths), never backwards'%len(d),len(d)>=3 and all(fr[i+1]>=fr[i]-1e-9 for i in range(len(fr)-1)))
# ---- 3 plain scrolling and sideways
setv();a=Vw();wheel([],60,0);b=Vw();chk('two fingers sideways (no key): scrolls time, no zoom',b['x']>a['x'] and eq(b['ppb'],a['ppb']) and eq(b['th'],a['th']),round(b['x']-a['x'],3))
setv();a=Vw();wheel([],0,60);b=Vw();chk('plain scroll: up and down, no zoom',b['y']>a['y'] and eq(b['ppb'],a['ppb']) and eq(b['x'],a['x']))
setv();a=Vw();wheel(['Control','Shift'],0,100);b=Vw();chk('Ctrl + Shift + wheel: scrolls sideways with a plain mouse wheel',b['x']>a['x']+1 and eq(b['ppb'],a['ppb']) and eq(b['th'],a['th']),round(b['x']-a['x'],3))
# ---- 4 limits
setv();wheel(['Shift'],0,-100,n=40,wait=700);b=Vw();chk('limit zoomed in: 600 px per beat',eq(b['ppb'],600),b['ppb'])
u0=under();wheel(['Shift'],0,-100,n=3);chk('  more scrolling at the limit changes nothing',eq(Vw()['ppb'],600) and abs(under()['b']-u0['b'])<1e-6)
leave=lambda:(R("(()=>{if(OVW.on)ovwToggle()})()"),pg.wait_for_timeout(700))
wheel(['Shift'],0,100,n=60,wait=800);b=Vw();ov=R("OVW.on");vis=G['w']/b['ppb'];L=JL(R("mapLen()"));chk('limit zoomed out: the whole song with room around it (%.3f px per beat, %.0f beats in view, song %.0f)'%(b['ppb'],vis,L),b['ppb']<1 and vis>L and all(math.isfinite(v) for v in b.values()))
chk('  pushing on past the end opens the Overview, as before',ov in (True,'true'));leave()
setv();wheel(['Alt'],0,-100,n=40,wait=700);hi=Vw()['th'];leave();wheel(['Alt'],0,100,n=60,wait=800);lo=Vw()['th'];leave();chk('track height limits: %.0f to %.0f px'%(lo,hi),lo>=12 and hi<=JL(R("laneH"))+1 and hi>lo)
# ---- 5 track names: the track height key works there, plain scroll still scrolls
H=JL(R("(()=>{const r=hdrin.getBoundingClientRect();return JSON.stringify({x:r.left+r.width/2,y:r.top+200})})()"))
setv();a=Vw();wheel(['Alt'],0,-100,x=H['x'],y=H['y']);b=Vw();chk('Option + wheel over the track names: track height',b['th']>a['th']*1.1 and eq(b['ppb'],a['ppb']))
setv();a=Vw();wheel([],0,60,x=H['x'],y=H['y']);b=Vw();chk('plain wheel over the track names: scrolls',b['y']>a['y'] and eq(b['th'],a['th']))
setv();a=Vw();wheel(['Shift'],0,-100,x=H['x'],y=H['y']);b=Vw();chk('Shift + wheel over the track names: no zoom',eq(b['ppb'],a['ppb']) and eq(b['th'],a['th']))
# ---- 6 pinch (wheel with ctrlKey but no Ctrl key held)
pinch="(()=>{const e=new WheelEvent('wheel',{bubbles:true,cancelable:true,clientX:%f,clientY:%f,deltaY:-12,ctrlKey:true});arr.dispatchEvent(e);return e.defaultPrevented})()"%(PX,PY)
setv();a=Vw();dp=R(pinch);pg.wait_for_timeout(400);b=Vw();chk('trackpad pinch zooms (and the page does not)',b['ppb']>a['ppb']*1.05 and dp in (True,'true'))
# ---- 7 AJ's nudge step follows the zoom reached by scrolling
one=JL(R("JSON.stringify((()=>{for(const t of S.tracks)for(const c of t.clips)if(c.notes&&c.start>=64&&c.start<80)return c.id})())"))
stepfor=lambda ppb:next(s for s in (.0625,.125,.25,.5,1,2,4,8) if s*ppb>=12)
for n,dy in ((6,-100),(1,100),(8,100)):
    wheel(['Shift'],0,dy,n=n,wait=600);ppb=Vw()['ppb']
    R("(()=>{selClear();selC='%s';AJ.foc=true;dirty=true})()"%one);s0=JL(R("findClip('%s').c.start"%one));pg.keyboard.press('ArrowRight');pg.wait_for_timeout(250);s1=JL(R("findClip('%s').c.start"%one))
    chk('arrow step follows the scrolled zoom: %.1f px per beat = %s beat (got %s)'%(ppb,stepfor(ppb),round(s1-s0,5)),abs(s1-s0-stepfor(ppb))<1e-4);R("undo()");pg.wait_for_timeout(100)
# ---- 8 settings
pg.mouse.move(5,5);R("openSettings('layout')");pg.wait_for_timeout(700)
B=JL(R("(()=>{const b=document.getElementById('zsBox'),l=b&&b.closest('.stfl'),sc=document.querySelector('.stfsc');return JSON.stringify({ok:!!b,first:!!l&&l.firstElementChild===b,under:!!sc&&sc.nextElementSibling===l,tips:[...b.querySelectorAll('button,select,input')].filter(e=>!(e.title||(e.closest('[title]')||{}).title)).length,n:b.querySelectorAll('button,select,input').length,dash:/\\u2014/.test(b.textContent+[...b.querySelectorAll('[title]')].map(e=>e.title).join(' '))})})()"));print(B,R("JSON.stringify([...document.querySelectorAll('#zsBox button,#zsBox select,#zsBox input')].filter(e=>!(e.title||(e.closest('[title]')||{}).title)).map(e=>e.outerHTML.slice(0,120)))"))
chk('Zoom and scroll group: first thing in the Layout box, directly under the scale',B['ok'] and B['first'] and B['under'])
chk('every control has a tooltip (%d controls), no em dashes'%B['n'],B['tips']==0 and not B['dash'])
pg.locator('#zsBox').scroll_into_view_if_needed();pg.screenshot(path=os.path.join(out,'an_settings_dark.png'))
st=lambda:JL(R("(()=>{const z=ZS();return JSON.stringify({zoom:z.zoom,th:z.th,cw:z.cw,side:z.side,speed:z.speed,anchor:z.anchor,inv:z.inv,pinch:z.pinch,on:[...document.querySelectorAll('#zsPre .on')].map(b=>b.dataset.zp)})})()"))
chk('default: Ctrl zoom, Option track height, Shift clip width; preset AudioLab default lit',st()=={'zoom':'ctrl','th':'alt','cw':'shift','side':'ctrl+shift','speed':100,'anchor':'mouse','inv':False,'pinch':True,'on':['audiolab']},st())
exp={'ableton':('none','alt','ctrl','shift'),'logic':('none','alt','alt+shift','shift'),'fl':('none','alt','ctrl','none'),'audiolab':('ctrl','alt','shift','ctrl+shift')}
for k,v in exp.items():
    pg.click('#zsPre [data-zp=%s]'%k);s=st();chk('preset %s sets %s'%(k,v),(s['zoom'],s['th'],s['cw'],s['side'])==v and k in s['on'],s['on'])
# live: Ableton style, settings still open, events sent to the arrangement canvas
def syn(mods,dy,dx=0,n=1):
    R("(()=>{for(let i=0;i<%d;i++)arr.dispatchEvent(new WheelEvent('wheel',{bubbles:true,cancelable:true,clientX:%f,clientY:%f,deltaY:%f,deltaX:%f,ctrlKey:%s,altKey:%s,shiftKey:%s}))})()"%(n,PX,PY,dy,dx,'true' if 'c' in mods else 'false','true' if 'a' in mods else 'false','true' if 's' in mods else 'false'));pg.wait_for_timeout(450)
def key(c):R("ZSK.c=%s"%('true' if c else 'false'))
pg.click('#zsPre [data-zp=ableton]')
setv();a=Vw();key(1);syn('c',-100);key(0);b=Vw();chk('live, Ableton style: Ctrl + wheel = clip width only',b['ppb']>a['ppb']*1.3 and eq(b['th'],a['th']))
setv();a=Vw();syn('s',100);b=Vw();chk('live, Ableton style: Shift + wheel scrolls sideways',b['x']>a['x']+1 and eq(b['ppb'],a['ppb']))
setv();a=Vw();syn('a',-100);b=Vw();chk('live, Ableton style: Option + wheel = track height',b['th']>a['th']*1.1 and eq(b['ppb'],a['ppb']))
pg.click('#zsPre [data-zp=logic]')
setv();a=Vw();syn('as',-100);b=Vw();chk('live, Logic style: Option + Shift + wheel = clip width',b['ppb']>a['ppb']*1.3 and eq(b['th'],a['th']))
setv();a=Vw();syn('a',-100);b=Vw();chk('live, Logic style: Option + wheel = track height',b['th']>a['th']*1.1 and eq(b['ppb'],a['ppb']))
pg.click('#zsPre [data-zp=fl]')
setv();a=Vw();syn('s',100);b=Vw();chk('live, FL style: Shift has no job and scrolls sideways',b['x']>a['x']+1 and eq(b['ppb'],a['ppb']))
pg.click('#zsPre [data-zp=audiolab]')
# a key that is taken swaps
pg.select_option('#zsBox select[data-zf=cw]','ctrl');s=st();chk('choosing a taken key swaps the two (clip width Ctrl, zoom Shift), no preset lit',s['cw']=='ctrl' and s['zoom']=='shift' and s['on']==[],s)
pg.select_option('#zsBox select[data-zf=th]','none');s=st();chk('None switches a job off',s['th']=='none');setv();a=Vw();syn('a',-100);b=Vw();chk('  Option + wheel then scrolls like a plain wheel',eq(b['th'],a['th']) and eq(b['ppb'],a['ppb']))
pg.click('#zsReset');s=st();chk('Reset puts everything back',s['zoom']=='ctrl' and s['th']=='alt' and s['cw']=='shift' and s['on']==['audiolab'] and JL(R("JSON.stringify(UI.zs===undefined)")))
# speed
setv();a=Vw();syn('s',-40);r1=math.log(Vw()['ppb']/a['ppb'])
R("(()=>{const s=document.getElementById('zsSpeed');s.value=200;s.dispatchEvent(new Event('input',{bubbles:true}))})()");setv();a=Vw();syn('s',-40);r2=math.log(Vw()['ppb']/a['ppb'])
chk('zoom speed 200%% zooms twice as far (x%.3f)'%(r2/r1),eq(r2/r1,2,5e-3) and R("document.getElementById('zsSpeedO').textContent")=='200%')
R("(()=>{const s=document.getElementById('zsSpeed');s.value=50;s.dispatchEvent(new Event('input',{bubbles:true}))})()");setv();a=Vw();syn('s',-40);r3=math.log(Vw()['ppb']/a['ppb']);chk('zoom speed 50%% zooms half as far (x%.3f)'%(r3/r1),eq(r3/r1,.5,5e-3))
# invert
pg.click('#zsInv');setv();a=Vw();syn('s',-100);b=Vw();chk('invert direction: scrolling up now makes clips thinner',b['ppb']<a['ppb'] and st()['inv'])
setv();a=Vw();R(pinch);pg.wait_for_timeout(400);chk('  pinch keeps its direction',Vw()['ppb']>a['ppb'])
pg.click('#zsInv')
# anchor playhead
pg.click('#zsAnchor [data-za=play]');setv();R("(()=>{pos=92;dirty=true})()");a=Vw();px0=(92-a['x'])*a['ppb'];syn('s',-100);b=Vw();px1=(92-b['x'])*b['ppb']
chk('anchor playhead: the playhead stays where it is (%.4f px)'%(px1-px0),abs(px1-px0)<1 and b['ppb']>a['ppb'] and st()['anchor']=='play')
setv();R("(()=>{pos=4;dirty=true})()");u0=under();syn('s',-100);u1=under();chk('  playhead out of view: the pointer is the anchor (%.4f px)'%((u1['b']-u0['b'])*Vw()['ppb']),abs((u1['b']-u0['b'])*Vw()['ppb'])<1)
# pinch off
pg.click('#zsPinch');setv();a=Vw();dp=R(pinch);pg.wait_for_timeout(400);b=Vw();chk('pinch off: a pinch does nothing (and the page still does not zoom)',eq(b['ppb'],a['ppb']) and eq(b['th'],a['th']) and dp in (True,'true') and not st()['pinch'])
setv();a=Vw();key(1);syn('c',-100);key(0);b=Vw();chk('  Ctrl + wheel still zooms with pinch off',b['ppb']>a['ppb']*1.1)
# Light mode screenshot
R("(()=>{UI.lite=true;applyLite()})()");pg.wait_for_timeout(500);pg.locator('#zsBox').scroll_into_view_if_needed();pg.screenshot(path=os.path.join(out,'an_settings_light.png'));R("(()=>{UI.lite=false;applyLite()})()")
# persist: speed 50, anchor play, pinch off, clip width on Ctrl
pg.select_option('#zsBox select[data-zf=cw]','ctrl');pg.wait_for_timeout(500);before=st();saved=JL(pg.evaluate("()=>JSON.stringify(JSON.parse(localStorage.getItem('audiolab-ui')).zs||null)"));print('saved',saved)
chk('saved with the other settings',saved and saved['cw']=='ctrl' and saved['zoom']=='shift' and saved['speed']==50 and saved['anchor']=='play' and saved['pinch']==False)
pg.reload();pg.wait_for_timeout(9000);R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();UI.follow=false})()");R("openSettings('layout')");pg.wait_for_timeout(600);after=st();after['on']=before['on']
chk('after a reload the choices are back and shown',after==before and R("document.querySelector('#zsBox select[data-zf=cw]').value")=='ctrl' and R("document.getElementById('zsSpeedO').textContent")=='50%',after)
setv();a=Vw();key(1);syn('c',-100);key(0);b=Vw();chk('  and they work: Ctrl + wheel = clip width only',b['ppb']>a['ppb']*1.1 and eq(b['th'],a['th']))
pg.click('#zsReset');R("(()=>{document.getElementById('set').hidden=true})()");pg.wait_for_timeout(300)
# ---- 9 other panels keep their own scrolling: the arrangement view must not move
def other(name,sel,open_js=None):
    if open_js:R(open_js);pg.wait_for_timeout(700)
    r=JL(R("(()=>{const e=document.querySelector(%s);if(!e)return'null';const r=e.getBoundingClientRect();return JSON.stringify({x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height})})()"%json.dumps(sel)))
    if not r or r['w']<5:chk('%s found'%name,False,r);return
    hit=R("(()=>{const e=document.elementFromPoint(%f,%f);return !!(e&&e.closest(%s))})()"%(r['x'],r['y'],json.dumps(sel)))
    setv();a=Vw()
    for mods in ([],['Shift'],['Alt'],['Control']):wheel(mods,0,-100,x=r['x'],y=r['y'],wait=250)
    b=Vw();chk('%s: wheel with no key, Shift, Option and Ctrl leaves the arrangement view alone'%name,hit in (True,'true') and all(eq(a[k],b[k]) for k in a),(hit,))
other('devices panel','#fxin')
other('mixer','#mixWin',"openMixer()")
R("(()=>{const w=document.getElementById('mixWin');if(w)w.hidden=true})()")
pr0=None
R("(()=>{for(const t of S.tracks)for(const c of t.clips)if(c.notes&&c.notes.length){openPR(t,c);return}})()");pg.wait_for_timeout(800)
pv=lambda:R("JSON.stringify(typeof PV!=='undefined'?PV:null)")
p0=pv();other('piano roll','#prc');p1=pv();chk('  the piano roll still reacts to its own wheel',p0!=p1 or p0=='null',(str(p0)[:60],str(p1)[:60]))
other('MIDI panel (#pr)','#pr')
errs=[e for e in al.errors];chk('no console errors',not errs,errs[:5])
print('ALL PASS' if ok else 'SOME FAILED');al.stop() if hasattr(al,'stop') else None
sys.exit(0 if ok else 1)
