# task AI (v0.220): AudioLab starts with the Fractals song as the only open song (shipped inside the app, master -10 dB).
#   python3 tools/ui-tests/taskAI.py index.html [old index.html (v0.219) to compare the song against]
import sys,os,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..')
f=sys.argv[1] if len(sys.argv)>1 else os.path.join(ROOT,'index.html');oldf=sys.argv[2] if len(sys.argv)>2 else None
ok=True
def chk(name,cond,info=''):
    global ok;ok&=bool(cond);print(('PASS ' if cond else 'FAIL ')+name,info)
pw=sync_playwright().start();br=pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
def page(path,vox):
    cx=br.new_context(viewport={"width":1600,"height":1000});pg=cx.new_page();pg.set_default_timeout(45000);pg.errs=[];pg.cons=[]
    pg.on("pageerror",lambda e:pg.errs.append(str(e)[:300]));pg.on("console",lambda m:pg.cons.append(m.text[:300]) if m.type=='error' else None)
    src=open(path,encoding='utf-8').read()
    def h(route):
        u=route.request.url
        if u.endswith('/') or u.endswith('index.html'):route.fulfill(body=src,content_type='text/html')
        elif vox and '/vox/' in u:route.fulfill(body=open(os.path.join(ROOT,'vox',u.rsplit('/',1)[1]),'rb').read(),content_type='audio/wav')
        else:route.fulfill(status=404,body='')
    pg.route("https://app.test/**",alsong(h));return pg
def boot(pg,reload=False):
    (pg.reload() if reload else pg.goto("https://app.test/"))
    pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=60000)
    pg.bring_to_front()
    for i in range(100):
        if pg.evaluate("()=>AudioLab.run(\"typeof FRX==='undefined'?S.tracks.some(t=>t.name==='Vocals (original)'):!PJ.list.some(p=>p.frxHold)\")"):break
        pg.wait_for_timeout(200)
    else:pass
    pg.wait_for_timeout(2500)
R=lambda pg,c:pg.evaluate("c=>AudioLab.run(c)",c)
J=lambda pg,c:json.loads(R(pg,"JSON.stringify("+c+")"))
STATE="{tabs:PJ.list.map(p=>p.name),win:(PJ.win||[]).length,master:S.master,n:S.tracks.length,vox:(S.tracks.find(t=>t.name==='Vocals (original)')||{clips:[]}).clips.length,bufs:(S.tracks.find(t=>t.name==='Vocals (original)')||{clips:[]}).clips.every(c=>BUFS.has(c.buf)),playing:!!play.on,pos:pos,dirty:!!curP().dirty,file:curP().file,ctx:ctx?ctx.state:null,splash:!!document.getElementById('splash'),booting:document.body.classList.contains('booting')}"
# ---- 1 fresh install, no vox files next to the app (as in the desktop app)
pg=page(f,False);boot(pg);st=J(pg,STATE);print('version',R(pg,'VERSION'),st)
chk('fresh start: one open song, the Fractals song',st['tabs']==['Fractals_remake'] and st['win']==0,st['tabs'])
chk('  no empty untitled song next to it',len(st['tabs'])==1 and pg.locator('#ptl .ptab').count()==1,pg.locator('#ptl .ptab').all_inner_texts())
chk('  master at -10 dB',st['master']==-10,st['master']);chk('  31 tracks with the vocal audio track (10 clips, audio loaded, no vox files served)',st['n']==31 and st['vox']==10 and st['bufs'])
chk('  not playing, at the start, no unsaved mark',not st['playing'] and st['pos']==0 and not st['dirty'],(st['playing'],st['pos'],st['dirty']))
chk('  start screen gone',not st['splash'] and not st['booting']);chk('  no page errors',not pg.errs,pg.errs);print('  console errors:',[c for c in pg.cons if 'vox' not in c][:5])
chk('  master read-out says -10',  '-10' in pg.locator('#mBtnV').inner_text(),pg.locator('#mBtnV').inner_text())
song=J(pg,"S")
# ---- 2 the song is the v0.219 song with only the master changed
if oldf:
    # v0.219 adds the vocal track a moment after the song opens (and not always: it is dropped when another tab takes the front in that moment)
    po=page(oldf,True);boot(po);R(po,"(()=>{const p=PJ.list.find(p=>p.name==='Fractals_remake');if(p&&p.id!==PJ.cur)switchProject(p.id)})();0");po.wait_for_timeout(800);old=J(po,"S")
    hasv=any(t['name']=='Vocals (original)' for t in old['tracks'])
    if not hasv:print('  (v0.219 opened the song without its vocal track this time: the other 30 tracks are compared, the vocal track is checked on its own below)');song2=json.loads(json.dumps(song));song2['tracks']=[t for t in song2['tracks'] if t['name']!='Vocals (original)']
    else:song2=song
    def norm(S):
        S=json.loads(json.dumps(S));S.pop('master');S.pop('work',None)
        for t in S['tracks']:
            if t['name']=='Vocals (original)':
                t.pop('id')
                for c in t['clips']:c.pop('id');c.pop('buf')
        return S
    a,b=norm(old),norm(song2);same=a==b
    if not same:
        for k in set(a)|set(b):
            if a.get(k)!=b.get(k):print('   differs:',k)
        for x,y in zip(a['tracks'],b['tracks']):
            if x!=y:print('   track differs:',x['name'],[k for k in set(x)|set(y) if x.get(k)!=y.get(k)])
            if x.get('inst')!=y.get('inst'):print('    inst:',{k:(x['inst'].get(k),y['inst'].get(k)) for k in set(x['inst'])|set(y['inst']) if x['inst'].get(k)!=y['inst'].get(k)})
    chk('song equals the v0.219 Fractals song: tracks, notes, devices, levels, sends, sections, tempo (master %g -> %g)'%(old['master'],song['master']),same and old['master']==0 and song['master']==-10)
    v=[t for t in song['tracks'] if t['name']=='Vocals (original)'][0];rv=[t for t in song['tracks'] if t['kind']=='return'][0]
    chk('vocal track as before: audio track, fader 0.8, send 0.15 to the plate reverb, clips at beats 0, 96, 276, 572, 588, 756, 828, 1012, 1076, 1140',v['kind']=='audio' and v['vol']==.8 and v.get('sends')=={rv['id']:.15} and [c['start'] for c in v['clips']]==[0,96,276,572,588,756,828,1012,1076,1140] and all(c['gain']==0 and c['fo']==.25 for c in v['clips']))
    # the embedded FLAC samples decode to the same audio as the WAV files
    d=po.evaluate("async()=>{const o=[];for(let k=1;k<=10;k++){const r=await fetch('vox/fractals_vox_'+String(k).padStart(2,'0')+'.wav');const b=await AudioLab.run('ctx').decodeAudioData(await r.arrayBuffer());o.push(Array.from(b.getChannelData(0)))}return o.map(a=>[a.length,a.reduce((s,v,i)=>s+v*((i%977)+1),0)])}")
    e=pg.evaluate("()=>{const o=[];for(let k=1;k<=10;k++){const b=AudioLab.run('BUFS').get('frxvox'+String(k).padStart(2,'0')).buf;o.push(Array.from(b.getChannelData(0)))}return o.map(a=>[a.length,a.reduce((s,v,i)=>s+v*((i%977)+1),0)])}")
    chk('vocal samples inside the app are the same audio as vox/*.wav (10 files, length and weighted sum)',d==e,[x[0] for x in e]);po.context.close()
# ---- 3 play and stop
pg.keyboard.press('Space');pg.wait_for_timeout(1500);p1=J(pg,"{on:!!play.on,pos:pos,ctx:ctx.state}");pg.keyboard.press('Space');pg.wait_for_timeout(500);p2=J(pg,"{on:!!play.on}")
chk('Space plays and stops it',p1['on'] and not p2['on'],(p1,p2));chk('  no page errors',not pg.errs,pg.errs)
# ---- 4 next start after only playing it: nothing is kept, nothing is said
d=J(pg,"({dirty:!!curP().dirty})");boot(pg,True);st=J(pg,STATE);sv=J(pg,"savedList().map(q=>q.name)");toasts=' '.join(pg.locator('#toast,.toast').all_inner_texts())
chk('playing marks the song unsaved (work timer), yet the next start keeps nothing: one song, Saved projects empty',d['dirty'] and st['tabs']==['Fractals_remake'] and sv==[] and st['master']==-10 and not st['dirty'],(d,st['tabs'],sv))
# ---- 5 other songs open and the Fractals song closes
R(pg,"openDemo('psy');0");pg.wait_for_timeout(800);t=J(pg,"PJ.list.map(p=>p.name)");chk('another song opens next to it',t==['Fractals_remake','Psytrance demo'],t)
R(pg,"closeTab(PJ.list[0].id);0");pg.wait_for_timeout(600);t=J(pg,"PJ.list.map(p=>p.name)");chk('the Fractals song closes',t==['Psytrance demo'],t)
R(pg,"openDemoFractals();0");pg.wait_for_timeout(2500);t=J(pg,"({t:PJ.list.map(p=>p.name),cur:curP().name,m:S.master,n:S.tracks.length})");chk('the menu opens it again (master -10, 31 tracks)',t['t']==['Psytrance demo','Fractals_remake'] and t['cur']=='Fractals_remake' and t['m']==-10 and t['n']==31,t)
R(pg,"openDemoFractals();0");pg.wait_for_timeout(1200);t=J(pg,"PJ.list.map(p=>p.name)");chk('  a second time it only switches to the open one',t==['Psytrance demo','Fractals_remake'],t)
chk('  no page errors',not pg.errs,pg.errs)
# ---- 6 coming from v0.219: its three demo tabs, the Fractals one played (master 0 dB, other audio ids)
R(pg,"""(()=>{const mk=()=>{const keep=S;demo();const ps=S;S=keep;return ps};const F=JSON.parse(JSON.stringify(S));F.master=0;F.work={o:99,a:77};const v=F.tracks.find(t=>t.name==='Vocals (original)');v.id='zz';v.clips.forEach((c,i)=>{c.id='q'+i;c.buf='old'+i});
  localStorage.setItem('audiolab-projects',JSON.stringify({cur:'f',list:[{id:'p1',name:'Psytrance demo',S:mk()},{id:'s',name:'Psy demo · Shrine Legion',S:mk()},{id:'f',name:'Fractals_remake',S:F,file:'Fractals_remake.audiolab',dirty:true}],win:[]}));saveProjects=()=>{};0})()""")
boot(pg,True);st=J(pg,STATE);sv=J(pg,"savedList().map(q=>q.name)")
chk('update from v0.219 (3 demo tabs, Fractals played): only the Fractals song, master -10, nothing kept',st['tabs']==['Fractals_remake'] and st['master']==-10 and sv==[] and st['vox']==10 and st['bufs'],(st['tabs'],sv))
# ---- 7 next start with real unsaved work: tabs are closed, the work is kept
R(pg,"""(()=>{const mk=v=>{const keep=S;demo();const ps=S;S=keep;ps.bpm=v;return ps};
  PJ.list.push({id:'u1',name:'Untitled',S:mk(111),dirty:true},{id:'u2',name:'Untitled',S:mk(112),dirty:true},{id:'c1',name:'On disk',S:mk(113),file:'On disk.audiolab',dirty:false});
  S.tracks.find(t=>t.name==='Kick').vol=.5;curP().dirty=true;PJ.win=[{id:'w1',name:'Torn off',S:mk(114),dirty:false}];saveProjects();0})()""")
before=J(pg,"JSON.parse(localStorage.getItem('audiolab-projects')).list.map(p=>p.name)");print('  stored before the restart:',before)
boot(pg,True);st=J(pg,STATE);sv=J(pg,"savedList().map(q=>[q.name,q.S.bpm,q.S.tracks.find(t=>t.name==='Kick').vol])");toasts=' '.join(pg.locator('#toast,.toast').all_inner_texts())
chk('restart with 4 stored tabs and a torn-off one: only the Fractals song is open',st['tabs']==['Fractals_remake'] and st['win']==0 and pg.locator('#ptl .ptab').count()==1,st['tabs'])
chk('  it is the shipped one again (master -10, clean, 31 tracks, vocals, Kick fader back)',st['master']==-10 and not st['dirty'] and st['n']==31 and st['vox']==10 and st['bufs'] and J(pg,"S.tracks.find(t=>t.name==='Kick').vol")==.8,st)
chk('  the 3 tabs with unsaved changes are under Saved projects, the edited Fractals song under its own name',sorted(x[0] for x in sv)==['Fractals_remake (edited)','Untitled','Untitled (2)'] and sorted(x[1] for x in sv)==[111,112,145] and [x[2] for x in sv if x[0].startswith('Fractals')]==[.5],sv)
chk('  a notice says so','3 projects with unsaved changes kept under New project, Saved projects.' in toasts,toasts[:200])
chk('  not playing, no page errors',not st['playing'] and not pg.errs,pg.errs)
IDB="async()=>{const db=await new Promise(r=>{const q=indexedDB.open('audiolab-files');q.onsuccess=()=>r(q.result)});return await new Promise(r=>{const q=db.transaction('audio').objectStore('audio').getAllKeys();q.onsuccess=()=>r(q.result)})}"
n1=pg.evaluate(IDB)
R(pg,"npOpen();0");pg.wait_for_timeout(500);pg.locator('#npSaved [data-sv]').filter(has_text='Untitled (2)').click();pg.wait_for_timeout(700);t=J(pg,"({t:PJ.list.map(p=>p.name),bpm:S.bpm})");chk('  a kept project opens again from New project > Saved projects',t['t']==['Fractals_remake','Untitled (2)'] and t['bpm'] in (111,112),t)
# ---- 8 another start: still one song, nothing piles up
boot(pg,True);st=J(pg,STATE);sv2=J(pg,"savedList().map(q=>q.name)");n2=pg.evaluate(IDB)
chk('next start: one song again',st['tabs']==['Fractals_remake'] and st['master']==-10,st['tabs']);chk('  Saved projects unchanged (the reopened copy had no changes)',sorted(sv2)==sorted(x[0] for x in sv),sv2)
chk('  stored vocal audio does not pile up (%d files, then %d)'%(len(n1),len(n2)),sorted(n1)==sorted(n2) and len([k for k in n2 if k.startswith('frxvox')])==10,n2[:12])
sz=J(pg,"({p:(localStorage.getItem('audiolab-projects')||'').length,s:(localStorage.getItem('audiolab-saved')||'').length})");print('  browser storage: open songs %d kB, saved projects %d kB'%(sz['p']//1024,sz['s']//1024))
# ---- 9 browser storage full: unsaved work stays open instead of being lost
R(pg,"""(()=>{const keep=S;demo();const ps=S;S=keep;PJ.list.push({id:'u9',name:'Big one',S:ps,dirty:true});saveProjects();
  const _s=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='audiolab-saved')throw new Error('full');return _s.apply(this,arguments)};0})()""")
pg.add_init_script("{const _s=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='audiolab-saved')throw new Error('QuotaExceededError');return _s.apply(this,arguments)}}")
boot(pg,True);st=J(pg,STATE);chk('storage full: the unsaved project stays open next to the Fractals song (shown first)',st['tabs']==['Fractals_remake','Big one'] and st['master']==-10 and J(pg,"JSON.parse(localStorage.getItem('audiolab-projects')).list.map(p=>p.name)")==['Fractals_remake','Big one'],st['tabs'])
chk('no page errors at the end',not pg.errs,pg.errs)
print('ALL PASS' if ok else 'SOME FAILED');br.close();pw.stop();sys.exit(0 if ok else 1)
