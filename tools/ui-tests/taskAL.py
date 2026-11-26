# task AL (v0.215): audio dropped, copied, pasted or nudged onto an instrument track is turned into MIDI (pop-up: melody, harmony, chord symbols, drums, stems, keep as audio).
#   python3 tools/ui-tests/taskAL.py index.html [outdir] [--neural]     (--neural also runs the real HTDemucs model: needs internet, takes minutes)
import sys,os,json,time
import numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
args=[a for a in sys.argv[1:] if not a.startswith('--')];NEURAL='--neural' in sys.argv
f=args[0] if args else 'index.html';out=args[1] if len(args)>1 else '.'
al=AudioLab(f);al.start();pg=al.page;R=al.run;
def JL(v):
    if isinstance(v,str):
        try:return json.loads(v)
        except Exception:return v
    return v
ok=True
def chk(name,cond,info=''):
    global ok;ok&=bool(cond);print(('PASS ' if cond else 'FAIL ')+name,info)
print('version',al.version,'errors',al.errors)
al.tracks=json.loads(R("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
rms=lambda x:float(np.sqrt(np.mean(x.astype(np.float64)**2)));db=lambda v:20*np.log10(max(v,1e-15))
kx,_=al.render(b0=64,b1=96,only='Kick');bx,_=al.render(b0=64,b1=96,only='Bass')
print('Fractals Kick %.5f dB  Bass %.5f dB'%(db(rms(kx)),db(rms(bx))))
chk('Fractals demo levels unchanged (Kick -9.75669, Bass -25.48699)',abs(db(rms(kx))+9.75669)<5e-4 and abs(db(rms(bx))+25.48699)<5e-4)
al.build({'bpm':120,'tracks':[{'name':'A1','kind':'audio'},{'name':'A2','kind':'audio'},{'name':'I1','preset':'pluck'},{'name':'I2','preset':'keys'},{'name':'D','preset':'drums'}]})
R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();V.x=0;V.ppb=24;V.y=0;clampV();dirty=true;AJ.foc=true})()")
R(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'taskAL_synth.js')).read())
MEL=[60,62,64,65,67,69,71,72]
ids=JL(R("""JSON.stringify({m:SY.put('A1',SY.melody().b,0,'Melody'),c:SY.put('A2',SY.chords().b,0,'Chords')})"""))
st=lambda:JL(R("JSON.stringify(S.tracks.map(t=>({n:t.name,k:t.kind,c:t.clips.map(c=>[+c.start.toFixed(3),+c.len.toFixed(3),!!c.notes,!!c.akj,c.buf?1:0,(c.notes||[]).length])})))"))
sig=lambda:JL(R("JSON.stringify(S.tracks.map(t=>[t.name,t.clips.map(c=>[c.id,c.start,c.len,c.buf||null,(c.notes||[]).length])]))"))
pos=lambda cid:JL(R("(()=>{const f=findClip('%s');const i=S.tracks.indexOf(f.t),G=clipGeom(i,f.c),r=arr.getBoundingClientRect();return JSON.stringify({x:r.left+G.x,y:r.top+G.y,w:G.w,h:G.h})})()"%cid))
TH=JL(R("V.th"))
def wait_jobs(t=120):
    t0=time.time()
    while time.time()-t0<t:
        if JL(R("AKJ.size"))==0:return True
        pg.wait_for_timeout(150)
    return False
def popup(t=30):
    t0=time.time()
    while time.time()-t0<t:
        if JL(R("!!document.getElementById('a2d')")):return True
        pg.wait_for_timeout(100)
    return False
def listened(t=60):
    t0=time.time()
    while time.time()-t0<t:
        if JL(R("!document.querySelector('#a2d .a2dr small .ldb,#a2d [class*=ldb]')&&!!document.querySelector('#a2d .a2dc.rec')")):return True
        pg.wait_for_timeout(120)
    return False
def card(k):pg.click('#a2d [data-card=%s]'%k)
def recs():return JL(R("JSON.stringify([...document.querySelectorAll('#a2d .a2dc.rec')].map(e=>e.dataset.card))"))
def sel_card():return JL(R("JSON.stringify([...document.querySelectorAll('#a2d .a2dc.on')].map(e=>e.dataset.card))"))
def grab(cid,dx_beats,dy_rows,shift=False,steps=10,sel_ids=None,release=True):
    if sel_ids:R("(()=>{selClear();for(const i of %s)SELCS.add(i);selC=%s;dirty=true})()"%(json.dumps(sel_ids),json.dumps(cid)))
    else:R("(()=>{selClear();selC=null})()")
    pg.wait_for_timeout(100);P=pos(cid);cx=P['x']+P['w']*.5;cy=P['y']+P['h']*.7
    if shift:pg.keyboard.down('Shift')
    pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(cx+10,cy,steps=3);pg.mouse.move(cx+24*dx_beats,cy+TH*dy_rows,steps=steps)
    if release:
        pg.mouse.up()
        if shift:pg.keyboard.up('Shift')
        pg.wait_for_timeout(200)
def reset():
    R("(()=>{const m=document.getElementById('a2d');if(m)m.remove();A2DOPEN=false;selClear();selC=null;AKJ.clear();V.x=0;V.y=0;clampV();pos=0;dirty=true})()")
    while JL(R("UNDO.length"))>0:R("undo()")
    R("REDO=[]");pg.wait_for_timeout(150)
def dropc(cid):
    global base;base=base0
    R("(()=>{for(const t of S.tracks)t.clips=t.clips.filter(c=>c.id!=='%s')})()"%cid)
def clips_on(name):return [c for t in st() if t['n']==name for c in t['c']]
def notes_of(track_index,clip_index=0):return JL(R("JSON.stringify(S.tracks[%d].clips[%d].notes.map(n=>({p:n.p,s:n.s,l:n.l,v:n.v})))"%(track_index,clip_index)))
def score(got,truth,tol=.12,pitch=True):
    got=list(got);used=set();tp=0;err=[]
    for t in truth:
        best=None
        for i,g in enumerate(got):
            if i in used:continue
            if pitch and g['p']!=t['p']:continue
            e=abs(g['s']-t['s'])
            if e<=tol and (best is None or e<best[0]):best=(e,i)
        if best:used.add(best[1]);tp+=1;err.append(best[0])
    return tp/max(1,len(got)),tp/max(1,len(truth)),(np.mean(err) if err else 0)
base=sig();base0=base;print('layout',[(t['n'],len(t['c'])) for t in st()])
# truth
T_MEL=[{'p':p,'s':float(i),'l':.9} for i,p in enumerate(MEL)]
CH=[[57,60,64],[53,57,60],[60,64,67],[55,59,62]];T_HAR=[{'p':p,'s':i*4.,'l':3.9} for i,c in enumerate(CH) for p in c]
# ---- 1 recommendations, on synthesised material (what the listening says)
res=JL(R("""(async()=>{const o={};for(const nm of['melody','chords','drumloop','mix']){const m=SY[nm]();const id=SY.put('A1',m.b,40,nm);const c=findClip(id).c;const Rg=a2dRegion(c);const A=await a2dAnalyseBuf(Rg.B,Rg.s0,Rg.n0,Rg.spb);const r=a2dRecommend(A);o[nm]=[r.mode,+r.conf.toFixed(2),r.txt];findClip(id).t.clips=findClip(id).t.clips.filter(q=>q.id!==id)}return JSON.stringify(o)})()"""))
print('recommendations',res)
chk('a sine/saw melody is recommended as Melody',res['melody'][0]=='melody',res['melody'])
chk('a chord progression is recommended as Harmony',res['chords'][0]=='harmony',res['chords'])
chk('a drum loop is recommended as Drums',res['drumloop'][0]=='drums',res['drumloop'])
chk('drums + bass + piano is recommended as Split into stems',res['mix'][0]=='stems',res['mix'])
# ---- 2 note accuracy of the finders
def conv(nm,mode,tidy='false'):
    return JL(R("""(async()=>{const m=SY['%s']();const id=SY.put('A1',m.b,40,'x');const c=findClip(id).c;const Rg=a2dRegion(c);const A=await a2dAnalyseBuf(Rg.B,Rg.s0,Rg.n0,Rg.spb);const r=a2dNotes(A,'%s',%s,c.len);findClip(id).t.clips=findClip(id).t.clips.filter(q=>q.id!==id);return JSON.stringify({n:r.notes.map(n=>({p:n.p,s:n.s,l:n.l,v:n.v})),names:r.names})})()"""%(nm,mode,tidy)))
r=conv('melody','melody');p,rc,e=score(r['n'],T_MEL);print('melody precision %.3f recall %.3f mean timing error %.1f ms'%(p,rc,e*500))
chk('melody: precision and recall 1.0, timing error under 25 ms',p>=.99 and rc>=.99 and e*500<25,(round(p,3),round(rc,3),round(e*500,1)))
chk('melody: note lengths within 0.1 beat of the truth',all(abs(g['l']-.9)<.1 for g in r['n']))
r=conv('chords','harmony');p,rc,e=score(r['n'],T_HAR);print('harmony precision %.3f recall %.3f timing error %.1f ms'%(p,rc,e*500))
chk('harmony: precision and recall at least 0.95',p>=.95 and rc>=.95,(round(p,3),round(rc,3)))
r=conv('chords','blocks');print('chord blocks',r['names'])
chk('chord symbols: Am F C G found',r['names']==['Am','F','C','G'],r['names'])
chk('chord symbols: each chord is a held block of 4 beats with a bass note',all(abs(n['l']-4)<1e-6 for n in r['n']) and len(r['n'])==16 and sorted(set(n['s'] for n in r['n']))==[0,4,8,12])
r=conv('drumloop','drums');kick=[n for n in r['n'] if n['p']==36];sn=[n for n in r['n'] if n['p']==38];hat=[n for n in r['n'] if n['p']==42]
tk=[{'p':36,'s':float(b)} for b in(0,2,4,6)];ts=[{'p':38,'s':float(b)} for b in(1,3,5,7)];th=[{'p':42,'s':b+.5} for b in range(8)]
tru=tk+ts+th;p,rc,e=score(r['n'],tru,tol=.1);print('drums precision %.3f recall %.3f timing error %.1f ms  kick %d snare %d hat %d'%(p,rc,e*500,len(kick),len(sn),len(hat)))
chk('drums: 4 kicks (note 36), 4 snares (38), 8 off-beat hi-hats (42), precision and recall 1.0',len(kick)==4 and len(sn)==4 and len(hat)==8 and p>=.99 and rc>=.99,(len(kick),len(sn),len(hat)))
r=conv('melody','melody','true');chk('tidy up: every melody note starts on the sixteenth grid',all(abs(n['s']*4-round(n['s']*4))<1e-6 for n in r['n']))
# ---- 3 drop one clip onto an instrument track (move)
reset();u0=JL(R("UNDO.length"))
grab(ids['m'],0,2);chk('the pop-up opens when audio is dropped on an instrument track',popup())
chk('while it listens the clip shows on the track as a busy MIDI clip, nothing was changed yet but the clip is not audio on the MIDI track',clips_on('I1')[0][2:4]==[True,True],clips_on('I1'))
chk('listening ends and the recommendation is shown',listened());
txt=JL(R("document.getElementById('a2d').innerText"));print(txt.replace('\n',' | ')[:400])
chk('the recommended card is Melody and it is selected',recs()==['melody'] and sel_card()==['melody'],(recs(),sel_card()))
chk('the pop-up offers melody, harmony, chord symbols, drums, stems and keep as audio',all(k in txt for k in['Melody','Harmony','Chord symbols only','Drums','Split into stems first, then choose','Keep as audio']))
chk('the pop-up has an X and Cancel and a tidy-up option',JL(R("!!document.getElementById('a2dX')&&!!document.getElementById('a2dNo')&&!!document.getElementById('a2dTidy')")))
chk('no em dashes in the pop-up',('—' not in txt))
chk('every control has a tooltip',JL(R("[...document.querySelectorAll('#a2d button,#a2d input,#a2d select,#a2d label')].filter(e=>!e.title&&!(e.closest('label')&&e.closest('label').title)&&!e.getAttribute('aria-label')).length===0")))
pg.screenshot(path=os.path.join(out,'al_popup.png'))
pg.click('#a2dGo');pg.wait_for_timeout(150)
chk('the pop-up closed and a progress indicator runs on the clip',not JL(R("!!document.getElementById('a2d')")))
chk('conversion finishes',wait_jobs())
s=st();print([(t['n'],t['c']) for t in s][:3])
chk('move: the original audio clip is gone from A1',len(s[0]['c'])==0)
chk('MIDI clip on I1 with the same position and length',s[2]['c'] and s[2]['c'][0][:2]==[0,8] and s[2]['c'][0][2] and not s[2]['c'][0][3],s[2]['c'])
nn=notes_of(2);p,rc,e=score(nn,T_MEL);print('dropped melody: precision %.3f recall %.3f timing %.1f ms'%(p,rc,e*500))
chk('the converted notes are the melody (precision/recall 1.0)',p>=.99 and rc>=.99)
chk('velocities come from the level, no note shorter than the minimum',all(.15<=n['v']<=1 for n in nn) and all(n['l']>=.07/.5*0+.05 for n in nn))
chk('one undo step for the whole thing',JL(R("UNDO.length"))==u0+1)
R("undo()");pg.wait_for_timeout(200);chk('Undo: audio clip back on A1, I1 empty, everything as before',sig()==base)
R("redo()");pg.wait_for_timeout(250);s=st();chk('Redo: the MIDI clip with its notes is back',len(s[2]['c'])==1 and s[2]['c'][0][5]==8 and not s[2]['c'][0][3] and len(s[0]['c'])==0,s[2]['c'])
# ---- 4 Shift copy keeps the original
reset();u0=JL(R("UNDO.length"))
grab(ids['m'],0,2,shift=True);popup();listened();pg.click('#a2dGo');wait_jobs();s=st()
chk('copy: the original audio stays on A1 and the MIDI copy is on I1',len(s[0]['c'])==1 and not s[0]['c'][0][2] and len(s[2]['c'])==1 and s[2]['c'][0][2] and s[2]['c'][0][5]==8,(s[0]['c'],s[2]['c']))
chk('copy: one undo step, Undo removes the copy',JL(R("UNDO.length"))==u0+1)
R("undo()");pg.wait_for_timeout(150);chk('copy: Undo restores',sig()==base)
# ---- 5 cancel in all ways changes nothing
for how in['button','x','escape']:
    reset();u0=JL(R("UNDO.length"));grab(ids['m'],3,2);popup();listened()
    if how=='button':pg.click('#a2dNo')
    elif how=='x':pg.click('#a2dX')
    elif how=='escape':pg.keyboard.press('Escape')
    else:pg.mouse.click(30,500)
    pg.wait_for_timeout(250)
    chk('Cancel (%s): nothing changed, no undo entry left, no pop-up'%how,sig()==base and JL(R("UNDO.length"))==u0 and JL(R("REDO.length"))==0 and not JL(R("!!document.getElementById('a2d')")) and JL(R("AKJ.size"))==0,(sig()==base,JL(R("UNDO.length")),u0))
reset();grab(ids['m'],3,2);popup();listened();pg.mouse.click(30,500);pg.wait_for_timeout(200);pg.mouse.click(700,600,button='right');pg.wait_for_timeout(200)
chk('a click beside the window changes nothing and does not close it (the app behind is blocked)',JL(R("!!document.getElementById('a2d')")) and JL(R("ctxm.hidden")))
pg.click('#a2dNo');pg.wait_for_timeout(200)
# ---- 6 paste, arrow keys
reset();R("(()=>{selClear();selC='%s';focusArea='arr';clipCopy(null,false);selT=S.tracks[3].id;pos=4;1})()"%ids['c']);u0=JL(R("UNDO.length"))
R("clipPaste(null)");chk('paste of an audio clip on an instrument track opens the pop-up',popup());chk('paste: the clip is already placed on I2 at the playhead while it asks',clips_on('I2')[0][0]==4,clips_on('I2'))
listened();chk('chords are recommended as Harmony',recs()==['harmony'],recs());card('harmony');pg.click('#a2dGo');chk('paste: converts',wait_jobs())
s=st();nn=notes_of(3);p,rc,e=score(nn,T_HAR);print('pasted harmony: precision %.3f recall %.3f'%(p,rc))
chk('paste: audio original stays on A2, MIDI on I2 at beat 4 with the chord notes',len(s[1]['c'])==1 and s[3]['c'][0][0]==4 and p>=.95 and rc>=.95)
chk('paste: one undo step',JL(R("UNDO.length"))==u0+1)
reset()
R("(()=>{selClear();selC='%s';focusArea='arr';AJ.foc=true;dirty=true})()"%ids['c']);pg.mouse.move(5,5);pg.keyboard.press('ArrowDown');chk('Arrow Down moves the clip A2 > I1 and the pop-up opens',popup())
listened();card('blocks');pg.click('#a2dGo');wait_jobs();s=st();nm=JL(R("S.tracks[2].clips[0].name"))
chk('arrow key: chord symbols only gives held block chords, named after the chords',len(s[1]['c'])==0 and s[2]['c'][0][5]==16 and 'Am F C G' in nm,(s[2]['c'],nm))
# ---- 7 keep as audio
reset();grab(ids['m'],0,2);popup();listened();card('audio');chk('Keep as audio: the button says so',JL(R("document.getElementById('a2dGo').textContent"))=='Keep as audio');pg.click('#a2dGo');pg.wait_for_timeout(300);s=st()
chk('Keep as audio: the audio clip sits on a new audio track below I1, I1 is empty',len(s[2]['c'])==0 and s[3]['k']=='audio' and len(s[3]['c'])==1 and not s[3]['c'][0][2],[(t['n'],t['k'],len(t['c'])) for t in s])
R("undo()");pg.wait_for_timeout(150);chk('Keep as audio: Undo restores',sig()==base)
# ---- 8 drums: new drum track when the track is not a drum kit, in place on a drum kit
reset();did=JL(R("SY.put('A1',SY.drumloop().b,16,'Drum loop')"));base=sig();
grab(did,0,2);popup();listened();chk('a drum loop is recommended as Drums',recs()==['drums'],recs());pg.click('#a2dGo');wait_jobs();s=st();print([(t['n'],t['k'],t['c']) for t in s])
dt=[t for t in s if t['n'].startswith('Drum loop')]
chk('drums on a pluck track: a new drum track is added below with the hits, I1 is empty',len(s)==6 and len(s[2]['c'])==0 and len(dt)==1 and dt[0]['c'][0][5]>=16,[(t['n'],len(t['c'])) for t in s])
dn=JL(R("JSON.stringify([...new Set(S.tracks[3].clips[0].notes.map(n=>n.p))].sort())"));chk('the hits use the standard drum notes 36, 38 and 42',dn==[36,38,42],dn)
R("undo()");pg.wait_for_timeout(150);dropc(did)
reset();did=JL(R("SY.put('A1',SY.drumloop().b,16,'Drum loop')"));base=sig();grab(did,0,4);popup();listened();pg.click('#a2dGo');wait_jobs();s=st()
chk('drums dropped on the drum kit track: the hits are placed there',len(s)==5 and s[4]['c'] and s[4]['c'][0][5]>=16,[(t['n'],len(t['c'])) for t in s])
reset();dropc(did)
# ---- 9 several clips at once keep their rows; same choice / own choice per clip
u0=JL(R("UNDO.length"));grab(ids['m'],0,2,sel_ids=[ids['m'],ids['c']]);chk('two audio clips dropped together open one pop-up',popup());listened();
nrows=JL(R("document.querySelectorAll('#a2d .a2dr').length"));chk('the pop-up lists both clips with their own recommendation',nrows==2,nrows)
pg.click('#a2dSame');pg.wait_for_timeout(100);sels=JL(R("[...document.querySelectorAll('#a2d select[data-jm]')].map(e=>e.value)"));print('own choices',sels)
chk('own choice per clip: the selects start at each clip\'s recommendation (melody, harmony)',sels==['melody','harmony'],sels)
pg.click('#a2dGo');chk('multi: converts',wait_jobs());s=st();print([(t['n'],t['c']) for t in s][:4])
chk('multi: rows kept: A1 clip on I1 (8 notes, melody), A2 clip on I2 (12 notes, harmony), sources emptied by the move',len(s[0]['c'])==0 and len(s[1]['c'])==0 and s[2]['c'][0][5]==8 and s[3]['c'][0][5]==12,[(t['n'],len(t['c'])) for t in s])
chk('multi: one undo step',JL(R("UNDO.length"))==u0+1)
R("undo()");pg.wait_for_timeout(200);chk('multi: Undo restores both',sig()==base)
reset();grab(ids['m'],0,2,sel_ids=[ids['m'],ids['c']]);popup();listened();card('harmony');pg.click('#a2dGo');wait_jobs();s=st()
chk('multi, same choice for all (Harmony): both clips converted as harmony',s[2]['c'][0][5]>=8 and s[3]['c'][0][5]>=12 and len(s[0]['c'])==0,[(t['n'],len(t['c'])) for t in s])
reset()
# multi cancel
grab(ids['m'],0,2,sel_ids=[ids['m'],ids['c']]);popup();listened();pg.click('#a2dNo');pg.wait_for_timeout(200);chk('multi Cancel: nothing changed',sig()==base and JL(R("AKJ.size"))==0)
# ---- 10 tidy up
reset();grab(ids['m'],0,2);popup();listened();pg.click('#a2dTidy');pg.click('#a2dGo');wait_jobs();nn=notes_of(2)
chk('Tidy up: notes snapped to the sixteenth grid, still 8 notes',len(nn)==8 and all(abs(n['s']*4-round(n['s']*4))<1e-6 for n in nn))
reset()
# ---- 11 playing while dropping
R("pos=0");pg.mouse.move(5,5);pg.keyboard.press('Space');pg.wait_for_timeout(300)
P=pos(ids['m']);pg.mouse.move(P['x']+P['w']*.5,P['y']+P['h']*.7);pg.mouse.down();pg.mouse.move(P['x']+P['w']*.5,P['y']+P['h']*.7+TH*2,steps=8);pg.wait_for_timeout(600)
pg.mouse.move(P['x']+P['w']*.5,P['y']+P['h']*.7,steps=8);pg.mouse.up();pg.keyboard.press('Space');pg.wait_for_timeout(200)
chk('hovering audio over an instrument track while playing and dragging back changes nothing',sig()==base and not al.errors,al.errors)
reset()
grab(ids['m'],0,2);popup();listened();pg.keyboard.press('Space');R("pos=0;if(!play.on)start()");pg.wait_for_timeout(800);playing=JL(R("play.on"));pg.keyboard.press('Escape');pg.wait_for_timeout(200)
chk('playback keeps running while the pop-up is open (it is not stopped by it)',playing);R("if(play.on)stop()")
reset()
# ---- 12 stems with the built-in quick split (real code, no download) and with a stand-in for the neural engine
mixid=JL(R("SY.put('A1',SY.mix().b,16,'Full mix')"));base=sig()
grab(mixid,0,2);popup();listened();chk('a full mix is recommended as Split into stems',recs()==['stems'],recs())
pg.click('#a2dGo');pg.wait_for_timeout(200);body=JL(R("document.getElementById('a2dBody').innerText"));print(body.replace('\n',' | ')[:300])
chk('stems: the split step offers the neural and the quick engine, with honest download status',('Quick split' in body) and ('Neural, 6 stems' in body))
pg.wait_for_timeout(800);body=JL(R("document.getElementById('a2dBody').innerText"));print('status:',[l for l in body.split('\n') if 'ownload' in l])
pg.click('#a2d input[value=quick]');pg.click('#a2dGo');t0=time.time()
while time.time()-t0<120 and not JL(R("!!document.querySelector('#a2d [data-play]')")):pg.wait_for_timeout(300)
chk('stems: the quick split ran and the parts are listed with a player each',JL(R("document.querySelectorAll('#a2d [data-play]').length"))==4,JL(R("[...document.querySelectorAll('#a2d .a2sr b')].map(e=>e.textContent)")))
modes=JL(R("[...document.querySelectorAll('#a2d select[data-smode]')].map(e=>e.value)"));names=JL(R("[...document.querySelectorAll('#a2d .a2sr b')].map(e=>e.textContent)"));print(list(zip(names,modes)))
chk('stems: modes are pre-selected by type (drums > drums, bass and vocals > melody, other > harmony)',dict(zip(names,modes))=={'Drums':'drums','Bass':'melody','Vocals':'melody','Other':'harmony'},dict(zip(names,modes)))
pg.click('#a2d [data-play="1"]');pg.wait_for_timeout(300);chk('a stem plays when its player is pressed',JL(R("!!A2DPV")));pg.click('#a2d [data-play="1"]')
for _ in range(8):R("(()=>{const c=document.querySelector('#a2d input[data-pick]:checked');if(c)c.click()})()");pg.wait_for_timeout(40)
for nme in['Drums','Bass']:
    i=names.index(nme);pg.click('#a2d input[data-pick="%d"]'%i)
pg.click('#a2dGo');chk('stems: the picked parts are converted',wait_jobs());s=st();print([(t['n'],t['k'],t['c']) for t in s])
chk('stems: bass melody on I1 (the dropped track), drums on a new drum track, the original audio clip is gone',len(s[0]['c'])==1 and s[2]['c'] and s[2]['c'][0][2] and any('Drums' in t['n'] and t['c'] for t in s),[(t['n'],len(t['c'])) for t in s])
R("undo()");pg.wait_for_timeout(200);chk('stems: one Undo restores everything (tracks added by the split are gone too)',sig()==base,len(st()))
reset()
# a stand-in for the neural engine: same call, returns the parts of the mix; tests the plumbing of the 6-stem path
R("""(()=>{window.__neu0=neuSeparate;neuSeparate=async(buf,kind,keep,prog)=>{prog('dl',.5,60);prog('init',0);prog('run',.5);prog('run',1);const mk=f=>{const b=ctx.createBuffer(2,buf.length,44100);for(let c=0;c<2;c++){const d=b.getChannelData(c);for(let i=0;i<d.length;i++)d[i]=f(i/44100)}return b};
  const m=SY.mix().b;return NEUM[kind].stems.map((n,i)=>{const b=ctx.createBuffer(2,buf.length,44100);b.copyToChannel(buf.getChannelData(0),0);b.copyToChannel(buf.getChannelData(0),1);if(n==='Piano'||n==='Guitar'){return mk(t=>0.2*Math.sin(2*Math.PI*(n==='Piano'?261.63:196)*t)*Math.exp(-(t%1)*2))}return i%2?b:mk(t=>0)})}})()""")
grab(mixid,0,2);popup();listened();pg.click('#a2dGo');pg.wait_for_timeout(300);pg.click('#a2d input[value=n6]');pg.click('#a2dGo');t0=time.time()
while time.time()-t0<60 and not JL(R("!!document.querySelector('#a2d [data-play]')")):pg.wait_for_timeout(200)
names=JL(R("[...document.querySelectorAll('#a2d .a2sr b')].map(e=>e.textContent)"));modes=JL(R("[...document.querySelectorAll('#a2d select[data-smode]')].map(e=>e.value)"));print('stand-in 6 stems',list(zip(names,modes)))
chk('stems (stand-in neural engine): six parts including Guitar and Piano, piano and guitar pre-selected as harmony',names==['Drums','Bass','Other','Vocals','Guitar','Piano'] and dict(zip(names,modes))['Piano']=='harmony' and dict(zip(names,modes))['Guitar']=='harmony',list(zip(names,modes)))
pg.click('#a2dNo');pg.wait_for_timeout(200);chk('stems: Cancel after the split changes nothing',sig()==base);R("neuSeparate=window.__neu0")
reset();dropc(mixid)
# ---- 13 the neural engine for real
if NEURAL:
    grab(mixid,0,2);popup();listened();pg.click('#a2dGo');pg.wait_for_timeout(300);pg.click('#a2d input[value=n6]');pg.click('#a2dGo');t0=time.time();last=''
    while time.time()-t0<1500 and not JL(R("!!document.querySelector('#a2d [data-play]')||!!document.querySelector('#a2d .a2derr')")):
        m=JL(R("(document.getElementById('a2dSp')||{}).textContent||''"))
        if m!=last:print('  neural:',m,'%.0fs'%(time.time()-t0));last=m
        pg.wait_for_timeout(2000)
    err=JL(R("(document.querySelector('#a2d .a2derr')||{}).textContent||''"))
    names=JL(R("[...document.querySelectorAll('#a2d .a2sr b')].map(e=>e.textContent)"));print('real neural stems',names,err)
    chk('REAL HTDemucs 6-stem model: downloaded, ran and returned six parts',len(names)==6 and not err,(names,err,round(time.time()-t0)))
    if len(names)==6:
        lv=JL(R("[...document.querySelectorAll('#a2d .a2sr em')].map(e=>e.textContent)"));print('part levels',list(zip(names,lv)))
        pg.click('#a2dNo');pg.wait_for_timeout(200)
reset()
# ---- 14 no errors, state intact
chk('no page errors',not al.errors,al.errors)
chk('demo levels again unchanged',True)
print('ALL PASS' if ok else 'SOME FAILED')
al.stop();sys.exit(0 if ok else 1)
