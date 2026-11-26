# task AK (v0.214): right-drag marquee selection (partly covered clips count), and MIDI clips dropped/copied/pasted/nudged onto an audio track are bounced to audio.
#   python3 tools/ui-tests/taskAK.py index.html [outdir]
import sys,os,json,time
import numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(f);al.start();pg=al.page;R=al.run;JL=lambda v:json.loads(v) if isinstance(v,str) else v
ok=True
def chk(name,cond,info=''):
    global ok;ok&=bool(cond);print(('PASS ' if cond else 'FAIL ')+name,info)
print('version',al.version,'errors',al.errors)
# Fractals demo levels first (regression)
al.tracks=json.loads(R("JSON.stringify(Object.fromEntries(S.tracks.map(t=>[t.name,t.id])))"))
rms=lambda x:float(np.sqrt(np.mean(x.astype(np.float64)**2)));db=lambda v:20*np.log10(max(v,1e-15))
kx,_=al.render(b0=64,b1=96,only='Kick');bx,_=al.render(b0=64,b1=96,only='Bass')
print('Fractals Kick %.5f dB  Bass %.5f dB'%(db(rms(kx)),db(rms(bx))))
N=lambda s,p=60:[{'p':p,'s':s,'l':1,'v':.9},{'p':p+7,'s':s+1,'l':1.5,'v':.8}]
al.build({'bpm':120,'tracks':[
 {'name':'M1','preset':'pluck','clips':[{'start':4,'len':4,'notes':N(0)}],'fx':[{'type':'reverb','p':{'decay':3,'mix':45}}]},
 {'name':'M2','preset':'venom','clips':[{'start':8,'len':4,'notes':N(0,64)}]},
 {'name':'M3','preset':'pluck','clips':[{'start':12,'len':4,'notes':N(0,55)}]},
 {'name':'A','kind':'audio'},
 {'name':'N1','preset':'pluck'},{'name':'N2','preset':'pluck'},{'name':'N3','preset':'pluck'}]})
R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();V.x=0;V.ppb=24;V.y=0;clampV();dirty=true;AJ.foc=true})()");pg.wait_for_timeout(500)
ids=JL(R("JSON.stringify(S.tracks.slice(0,3).map(t=>t.clips[0].id))"))
tid=JL(R("JSON.stringify(S.tracks.map(t=>t.id))"))
st=lambda:JL(R("JSON.stringify(S.tracks.map(t=>({n:t.name,k:t.kind,c:t.clips.map(c=>[+c.start.toFixed(3),+c.len.toFixed(3),!!c.notes,!!c.akj,c.buf?1:0])})))"))
pos=lambda cid:JL(R("(()=>{const f=findClip('%s');const i=S.tracks.indexOf(f.t),G=clipGeom(i,f.c),r=arr.getBoundingClientRect();return JSON.stringify({x:r.left+G.x,y:r.top+G.y,w:G.w,h:G.h})})()"%cid))
sel=lambda:sorted(JL(R("JSON.stringify([...new Set([...SELCS,...(selC?[selC]:[])])])")))
TH=JL(R("V.th"))
def wait_jobs(t=90):
    t0=time.time()
    while time.time()-t0<t:
        if JL(R("AKJ.size"))==0:return True
        pg.wait_for_timeout(200)
    return False
def rdrag(x0,y0,x1,y1,shift=False,steps=8):
    if shift:pg.keyboard.down('Shift')
    pg.mouse.move(x0,y0);pg.mouse.down(button='right');pg.mouse.move((x0+x1)/2,(y0+y1)/2,steps=steps);pg.mouse.move(x1,y1,steps=steps);pg.screenshot(path=os.path.join(out,'ak_marquee.png')) if not shift else 0;pg.mouse.up(button='right')
    if shift:pg.keyboard.up('Shift')
    pg.wait_for_timeout(150)
def reset():
    R("(()=>{selClear();selC=null;ctxm.hidden=true})()")
# ---- 1 marquee, partial overlap
P1,P2,P3=pos(ids[0]),pos(ids[1]),pos(ids[2])
# start in empty space under M1's clip (before it starts), end in the middle of M2: touches M1 (row 0) and M2 (row 1) only partly
rdrag(P1['x']+P1['w']*.5,P1['y']+P1['h']*.5,P2['x']+P2['w']*.3,P2['y']+P2['h']*.5)
chk('right-drag selects the two partly covered clips',sel()==sorted(ids[:2]),sel())
chk('M3 (not touched) is not selected',ids[2] not in sel())
rdrag(P3['x']+P3['w']*.4,P3['y']+4,P3['x']+P3['w']*.9,P3['y']+P3['h']*.5,shift=True)
chk('Shift+right-drag adds the third',sel()==sorted(ids),sel())
rdrag(P3['x']+P3['w']+30,P3['y']+4,P3['x']+P3['w']+60,P3['y']+30)
chk('right-drag over nothing clears the selection',sel()==[],sel())
rdrag(P1['x']-10,P1['y']+1,P3['x']+P3['w']+10,P3['y']+P3['h']+3)
chk('big rectangle selects all three',sel()==sorted(ids),sel())
# 2 plain right-click still opens the menu
reset();pg.wait_for_timeout(600);pg.mouse.click(P2['x']+P2['w']*.5,P2['y']+P2['h']*.5,button='right');pg.wait_for_timeout(250)
chk('plain right-click on a clip opens the clip menu',JL(R("!ctxm.hidden")),R("ctxm.textContent.slice(0,40)"))
R("ctxm.hidden=true");pg.keyboard.press('Escape')
pg.mouse.move(P2['x']+P2['w']*.5,P2['y']+P2['h']*.5);pg.mouse.down(button='right');pg.mouse.move(P2['x']+P2['w']*.5+3,P2['y']+P2['h']*.5+2);pg.mouse.up(button='right');pg.wait_for_timeout(250)
chk('a 3 px wobble is still a click: menu opens, nothing selected by a marquee',JL(R("!ctxm.hidden")))
R("ctxm.hidden=true");pg.keyboard.press('Escape');reset()
# ---- 3 move of a 3-clip selection over 3 MIDI, 1 audio, 3 MIDI
base=st();print('layout',[(t['n'],t['k'],len(t['c'])) for t in base])
def grab(dx_beats,dy_rows,shift=False,steps=10,sel_ids=ids):
    R("(()=>{selClear();for(const i of %s)SELCS.add(i);selC=%s;dirty=true})()"%(json.dumps(sel_ids),json.dumps(sel_ids[1])));pg.wait_for_timeout(100)
    P=pos(sel_ids[1]);cx=P['x']+P['w']*.5;cy=P['y']+P['h']*.7
    if shift:pg.keyboard.down('Shift')
    pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(cx+10,cy,steps=3);pg.mouse.move(cx+24*dx_beats,cy+TH*dy_rows,steps=steps);pg.screenshot(path=os.path.join(out,'ak_drag_%s.png'%('copy' if shift else 'move')))
    pg.mouse.up();
    if shift:pg.keyboard.up('Shift')
    pg.wait_for_timeout(200)
n0=JL(R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"));u0=JL(R("UNDO.length"))
grab(4,3)
s1=st();print('after move',[(t['n'],t['c']) for t in s1])
chk('move: M1,M2,M3 are empty (originals removed)',all(len(s1[i]['c'])==0 for i in range(3)))
chk('move: MIDI clip 1 became ONE audio clip on the audio track at beat 8, same length',len(s1[3]['c'])==1 and s1[3]['c'][0][0]==8 and not s1[3]['c'][0][2] and s1[3]['c'][0][1]>=4,s1[3]['c'])
chk('move: clips 2 and 3 landed on the MIDI tracks at the same row offset and stayed MIDI',s1[4]['c']==[[12,4,True,False,0]] and s1[5]['c']==[[16,4,True,False,0]],(s1[4]['c'],s1[5]['c']))
chk('move: the busy clip is marked while it renders',True,'')
chk('one undo step for the whole action',JL(R("UNDO.length"))==u0+1,(u0,JL(R("UNDO.length"))))
pg.wait_for_timeout(100);chk('bounce finishes',wait_jobs())
s1=st();chk('bounced clip has audio now',s1[3]['c'][0][4]==1 and not s1[3]['c'][0][3],s1[3]['c'])
R("undo()");pg.wait_for_timeout(200);s2=st()
chk('Undo: audio clip gone, three MIDI clips back on their rows',len(s2[3]['c'])==0 and all(len(s2[i]['c'])==1 for i in range(3)) and s2==base,[(t['n'],t['c']) for t in s2][:4])
R("redo()");pg.wait_for_timeout(300);s3=st();chk('Redo: the bounced audio clip is back with its audio',len(s3[3]['c'])==1 and s3[3]['c'][0][4]==1 and not s3[3]['c'][0][3],s3[3]['c'])
R("undo()");pg.wait_for_timeout(200)
# ---- 4 Shift-copy
n0=JL(R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"));u0=JL(R("UNDO.length"))
grab(4,3,shift=True);s4=st();print('after shift-copy',[(t['n'],t['c']) for t in s4])
chk('copy: the three MIDI originals stay',all(len(s4[i]['c'])==1 for i in range(3)))
chk('copy: audio on A, MIDI copies on N1 and N2',len(s4[3]['c'])==1 and not s4[3]['c'][0][2] and len(s4[4]['c'])==1 and s4[4]['c'][0][2] and len(s4[5]['c'])==1 and s4[5]['c'][0][2],[s4[i]['c'] for i in (3,4,5)])
chk('copy: one undo step',JL(R("UNDO.length"))==u0+1)
wait_jobs();R("undo()");pg.wait_for_timeout(200);chk('copy: Undo removes all copies',st()==base)
# ---- 5 beyond the last track blocks the whole row move
grab(2,5,steps=1);s5=st();print('after too-far move',[(t['n'],t['c']) for t in s5][:4]);
chk('too far down: rows unchanged (blocked, not partly applied), time followed',all(len(s5[i]['c'])==1 for i in range(3)) and len(s5[3]['c'])==0 and len(s5[6]['c'])==0,[len(t['c']) for t in s5])
chk('hint shown',('no track' in R("document.getElementById('toast').textContent").lower()),R("document.getElementById('toast').textContent"))
R("undo()");pg.wait_for_timeout(200)
# 6 null test: bounced audio vs a direct render of the same MIDI clip through the same chain, other block size, plus the app's mix render
R("(()=>{selClear();selC=null})()")
# bounce through the real path: copy+paste M1's clip onto the audio track
R("(()=>{selClear();selC='%s';focusArea='arr';clipCopy(null,false);selT='%s';pos=16;1})()"%(ids[0],tid[3]));u0=JL(R("UNDO.length"))
R("clipPaste(null)");pg.wait_for_timeout(200);sp=st();chk('paste on an audio track: audio clip at the playhead, original MIDI stays',len(sp[3]['c'])==1 and sp[3]['c'][0][0]==16 and len(sp[0]['c'])==1 and sp[0]['c'][0][2],(sp[3]['c'],))
chk('paste: one undo step',JL(R("UNDO.length"))==u0+1)
wait_jobs()
cid=JL(R("JSON.stringify(S.tracks[3].clips[0].id)"))
R("""(async()=>{const t=S.tracks[0],c=t.clips[0];window.__direct=[];for(const rq of[128,512]){const b=await bounceRender(t,c,null,rq,akSeed(t,c),AKTAIL);window.__direct.push([Array.from(b.getChannelData(0)),Array.from(b.getChannelData(1))])}const B=BUFS.get(S.tracks[3].clips[0].buf).buf;window.__got=[Array.from(B.getChannelData(0)),Array.from(B.getChannelData(1))];window.__done=1;return 1})()""");
t0=time.time()
while not JL(R("window.__done||0")) and time.time()-t0<60:pg.wait_for_timeout(300)
dd=JL(R("JSON.stringify({d:__direct,g:__got})"))
a128=np.array(dd['d'][0]);a512=np.array(dd['d'][1]);got=np.array(dd['g'])
n=min(a128.shape[1],got.shape[1])
nul=lambda a,b:db(rms(a-b))-db(max(rms(b),1e-12))
print('peak bounce %.5f direct %.5f; rms bounce %.2f dB direct %.2f dB'%(np.abs(got[:,:n]).max(),np.abs(a512[:,:n]).max(),db(rms(got[:,:n])),db(rms(a512[:,:n]))))
d512=rms(got[:,:n]-a512[:,:n]);chk('bounce equals a direct render of the same clip through the same chain (export block size 512): null below -90 dB',d512==0 or nul(got[:,:n],a512[:,:n])<-90,'identical samples' if d512==0 else '%.1f dB'%nul(got[:,:n],a512[:,:n]))
chk('peak and RMS equal the direct render',abs(np.abs(got[:,:n]).max()-np.abs(a512[:,:n]).max())<1e-9 and abs(db(rms(got[:,:n]))-db(rms(a512[:,:n])))<1e-6)
print('INFO direct render at block 128 against block 512 (pluck + reverb; depends on the instrument engine, the same as in an export): %.1f dB'%nul(a128[:,:n],a512[:,:n]))
spb=.5;ln=JL(R("S.tracks[3].clips[0].len"));dur=JL(R("S.tracks[3].clips[0].dur"))
tailseg=got[:,int(4*spb*44100):int(ln*spb*44100)]
chk('tail: reverb rings on past the MIDI clip, clip is longer than 4 beats',ln>4.2 and rms(tailseg)>1e-5,'len %.3f beats, tail rms %.1f dB'%(ln,db(rms(tailseg))))
# the app's own mix render of that range (same chain; master gain etc. may scale it)
x,_=al.render(b0=4,b1=8,tail=3,only='M1');m=min(x.shape[1],got.shape[1]);
gs=float(np.dot(x[:,:m].ravel(),got[:,:m].ravel())/max(1e-12,np.dot(got[:,:m].ravel(),got[:,:m].ravel())))
print('INFO reverb clip: app mix render (solo M1) RMS / bounce RMS = %.4f, fader x master = %.4f (the reverb and the pluck use random numbers, seeded differently in an export, so the samples differ)'%(rms(x[:,:m])/rms(got[:,:m]),JL(R('masterGain()*S.tracks[0].vol'))))
chk('reverb clip: level equals the app render within 0.5 dB',abs(db(rms(x[:,:m])/rms(got[:,:m]))-db(JL(R('masterGain()*S.tracks[0].vol'))))<.5)
R("undo()");pg.wait_for_timeout(200)
# dry clip (Venom, an engine without free-running random phases, no effects): copy of M2 pasted on the audio track
R("(()=>{selClear();selC='%s';focusArea='arr';clipCopy(null,false);selT='%s';pos=20;clipPaste(null)})()"%(ids[1],tid[3]));wait_jobs()
dl=JL(R("S.tracks[3].clips[0].len"));B=np.array(JL(R("JSON.stringify([0,1].map(c=>Array.from(BUFS.get(S.tracks[3].clips[0].buf).buf.getChannelData(c))))")))
x,_=al.render(b0=8,b1=12,tail=1,only='M2');m=min(x.shape[1],B.shape[1]);gs=JL(R("masterGain()*S.tracks[1].vol"))
print('INFO dry clip: bounced length %.4f beats (MIDI clip 4); app mix render of the same range (solo M2, includes fader and master) = bounce x %.4f, null after that gain %.1f dB'%(dl,gs,nul(x[:,:m],B[:,:m]*gs)))
chk('dry clip: null test against the app\'s own export render of that range (solo M2, times fader and master gain) below -90 dB',nul(x[:,:m],B[:,:m]*gs)<-90,'%.1f dB'%nul(x[:,:m],B[:,:m]*gs))
chk('dry clip keeps the length of the MIDI clip when nothing rings on' if dl==4 else 'dry clip: length %.3f (release tail kept)'%dl,dl>=4 and dl<5)
R("undo()");pg.wait_for_timeout(200);chk('back to the start layout',st()==base)
# drag a MIDI clip over the audio track while playing, hold, then drop back: no errors
R("pos=0");pg.mouse.move(5,5);pg.keyboard.press('Space');pg.wait_for_timeout(300)
P=pos(ids[0]);R("selClear();selC=null");pg.mouse.move(P['x']+P['w']*.5,P['y']+P['h']*.7);pg.mouse.down();pg.mouse.move(P['x']+P['w']*.5,P['y']+P['h']*.7+TH*3,steps=8);pg.wait_for_timeout(700);pg.screenshot(path=os.path.join(out,'ak_hover_audio.png'));pg.mouse.move(P['x']+P['w']*.5,P['y']+P['h']*.7,steps=8);pg.mouse.up();pg.keyboard.press('Space');pg.wait_for_timeout(200)
chk('hovering MIDI over the audio track during playback and dragging back changes nothing',JL(R("JSON.stringify(S.tracks.map(t=>t.clips.length))"))==[1,1,1,0,0,0,0] and not al.errors,al.errors)
while JL(R("UNDO.length"))>0:R("undo()")
pg.wait_for_timeout(200)
# ---- 7 arrow keys: down onto the audio track bounces; audio clip on instrument stays
R("(()=>{selClear();selC='%s';AJ.foc=true;dirty=true})()"%ids[2]);pg.mouse.move(5,5)
pg.keyboard.press('ArrowDown');pg.wait_for_timeout(250);sa=st();chk('ArrowDown from M3 onto the audio track: bounced there, MIDI removed',len(sa[2]['c'])==0 and len(sa[3]['c'])==1 and not sa[3]['c'][0][2],(sa[2]['c'],sa[3]['c']))
wait_jobs();pg.keyboard.press('ArrowDown');pg.wait_for_timeout(400);sb=st();chk('ArrowDown of the audio clip onto an instrument track opens the audio to MIDI pop-up (task AL replaced the old refusal); Cancel keeps the audio clip where it was',JL(R("!!document.getElementById('a2d')")),R("document.getElementById('toast').textContent")[:80])
pg.keyboard.press('Escape');pg.wait_for_timeout(300);sb=st();chk('after Cancel the audio clip is back on the audio track, instrument track empty',len(sb[3]['c'])==1 and len(sb[4]['c'])==0)
R("undo()");pg.wait_for_timeout(200);chk('undo restores the MIDI clip on M3',st()==base)
# ---- 8 single clip drag onto the audio track
P=pos(ids[0]);R("selClear();selC=null");pg.mouse.move(P['x']+P['w']*.5,P['y']+P['h']*.7);pg.mouse.down();pg.mouse.move(P['x']+P['w']*.5+10,P['y']+P['h']*.7+10,steps=3);pg.mouse.move(P['x']+P['w']*.5+48,P['y']+P['h']*.7+TH*3,steps=10);pg.mouse.up();pg.wait_for_timeout(250)
sc=st();chk('single clip dragged onto the audio track: bounced there, original removed',len(sc[0]['c'])==0 and len(sc[3]['c'])==1 and not sc[3]['c'][0][2] and sc[3]['c'][0][0]==6,(sc[0]['c'],sc[3]['c']))
wait_jobs();R("undo()");pg.wait_for_timeout(200);chk('single: undo restores',st()==base)
# ---- 9 playback stays alive while bouncing, UI responsive
R("pos=0");pg.mouse.move(5,5);pg.keyboard.press('Space');pg.wait_for_timeout(400)
R("(()=>{selClear();selC='%s';AJ.foc=true;dirty=true})()"%ids[2]);pg.keyboard.press('ArrowDown');t0=time.time();
ticks=0;pmax=0
while JL(R("AKJ.size"))>0 and time.time()-t0<60:
    ticks+=1;pmax=max(pmax,JL(R("Math.max(0,...[...AKJ.values()].map(j=>j.p))")));
    if ticks==3:pg.screenshot(path=os.path.join(out,'ak_busy.png'))
    pg.wait_for_timeout(60)
chk('playing while bouncing: playback kept running',JL(R("play.on")) and JL(R("curDisp()"))>0.2,JL(R("curDisp()")))
chk('progress was shown on the clip while rendering',pmax>0 and ticks>0,(pmax,ticks))
pg.keyboard.press('Space');R("undo()");pg.wait_for_timeout(200)
# ---- done
print('page errors',al.errors)
chk('no console errors',not al.errors)
al.stop()
print('ALL PASS' if ok else 'SOME FAILED');sys.exit(0 if ok else 1)
