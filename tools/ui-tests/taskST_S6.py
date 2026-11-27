"""Task ST-S6 (settings rebuild, step S6): search with synonyms and help text, the whole path in each result, in-place options with "Show me".
Synonyms and help lines from the table find their settings ("latency" finds Buffer size, "sound card" finds Output device); each result shows
group › page › block; the in-place options (metronome, count-in, capture, loudness, CPU, Follow chip, mixer switches, piano roll snap and scale)
are found, marked "Show me", and choosing one closes Settings and lights the control where it lives (or says where it is); the moved settings
and old page names are still found; keyboard choice works; dark and Light level; no console errors.
  python3 tools/ui-tests/taskST_S6.py [repo dir] [out dir]"""
import sys,os,mimetypes,json
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(OUT,exist_ok=True)
N=[0,0];FAIL=[]
def ck(name,ok,info=''):
    N[0]+=1
    if ok:N[1]+=1
    else:FAIL.append(name);print('  FAIL',name,str(info)[:600])
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html';f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type='text/html' if f.endswith('.html') else (mimetypes.guess_type(f)[0] or 'application/octet-stream'))
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
J=lambda pg,c:json.loads(R(pg,"JSON.stringify("+c+")"))
def ctx(b,lite):
    c=b.new_context(viewport={'width':1600,'height':1000});pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and errs.append('console '+m.text[:200]))
    pg.route('https://app.test/**',serve)
    u=dict(order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite)
    pg.add_init_script("if(!sessionStorage.getItem('t6')){sessionStorage.setItem('t6','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(3000)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
    return c,pg,errs
def search(pg,q):
    pg.evaluate("q=>{const e=document.getElementById('setQ');e.focus();e.value=q;e.dispatchEvent(new Event('input'))}",q);pg.wait_for_timeout(200)
    return pg.evaluate("()=>[...document.querySelectorAll('#setQR button')].map(b=>({t:b.querySelector('b').textContent,p:b.querySelector('small').textContent,ip:b.classList.contains('st6ip'),tip:b.title,mark:!!b.querySelector('mark')}))")
def pick(pg,q,label):
    h=search(pg,q);i=next((n for n,x in enumerate(h) if x['t']==label and x['ip']),-1)
    if i<0:return False
    pg.click('#setQR button >> nth=%d'%i);pg.wait_for_timeout(500);return True
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c,pg,errs=ctx(b,lite)
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.251)
        R(pg,"openSettings('general')");pg.wait_for_timeout(500)
        # synonyms and help lines from the table, with the whole path
        for q,label,path in [('latency','Buffer size','Sound › Audio'),('sound card','Output device','Sound › Audio'),('crackle','Buffer size','Sound › Audio'),
                             ('hotkeys','Keyboard shortcuts','Program › Keyboard shortcuts'),('chase','Pick up notes','Working › Editing'),('speakers','Output device','Sound › Audio'),
                             ('khz','Sample rate','Sound › Audio')]:
            h=search(pg,q);hit=[x for x in h if x['t'].lower().startswith(label.lower()) and x['p'].startswith(path)]
            ck(f'{L}: "{q}" finds {label} under {path}',bool(hit),h[:5])
        h=search(pg,'buffer')
        ck(f'{L}: results show group › page › block, mark the words and carry the help line',any(x['p'].count('›')>=2 and x['mark'] for x in h) and any(len(x['tip'])>20 for x in h),h[:3])
        # old page names and moved settings
        for q,w in [('colours & clips','Appearance'),('zoom and playhead','Navigation'),('safety limiter','DAC and audio interface'),('level meters','Mixer and meters')]:
            h=search(pg,q);ck(f'{L}: "{q}" still finds {w}',any(w in x['p'] or x['t']==w for x in h),h[:4])
        # in-place options
        for q,label in [('metronome','Metronome on or off'),('count-in','Count-in on or off'),('capture','Capture'),('lufs','Loudness read-out and target'),('follow','Follow the playhead on or off'),
                        ('compact','Compact channels'),('cables','Cables'),('dim','Mono, Dim and swap'),('snap','Snap in the piano roll'),('scale','Scale and root'),('cpu','CPU read-out and the performance panel')]:
            h=search(pg,q);hit=[x for x in h if x['t']==label and x['ip']]
            ck(f'{L}: "{q}" finds the in-place {label} with Show me',bool(hit) and hit[0]['ip'] and 'Show me' in hit[0]['p'] and hit[0]['p'].startswith('In place:'),h[:5])
        if not lite:
            search(pg,'metronome');pg.locator('#set .sheet').screenshot(path=f'{OUT}/s6_search_metronome_{L}.png')
        # Show me: transport button
        ok=pick(pg,'metronome','Metronome on or off')
        st=pg.evaluate("()=>{const s=document.getElementById('st6Spot'),b=document.getElementById('bClick').getBoundingClientRect(),r=s&&s.getBoundingClientRect();return{set:document.getElementById('set').hidden,on:!!s&&s.classList.contains('on'),near:!!r&&Math.abs(r.left+4-b.left)<2&&Math.abs(r.top+4-b.top)<2}}")
        ck(f'{L}: Show me closes Settings and lights the metronome button',ok and st['set'] and st['on'] and st['near'],st)
        pg.wait_for_timeout(150);pg.screenshot(path=f'{OUT}/s6_show_metronome_{L}.png',clip={'x':0,'y':780,'width':1100,'height':220})
        ck(f'{L}: the metronome itself was not switched',R(pg,"!!(document.getElementById('bClick').getAttribute('aria-pressed')==='true')")==False)
        # Show me: in the mixer (opens it)
        R(pg,"openSettings('general')");pg.wait_for_timeout(300)
        ok=pick(pg,'compact','Compact channels');pg.wait_for_timeout(500)
        st=pg.evaluate("()=>{const s=document.getElementById('st6Spot'),m=document.getElementById('mixWin'),b=document.getElementById('mxCmp');return{mix:!!m&&!m.hidden,on:!!s&&s.classList.contains('on'),b:!!b}}")
        ck(f'{L}: Show me opens the mixer and lights Compact channels',ok and st['mix'] and st['b'] and st['on'],st)
        if not lite: pg.screenshot(path=f'{OUT}/s6_show_compact_{L}.png')
        R(pg,"(()=>{const w=document.getElementById('mixWin');if(w)w.hidden=true;return 1})()")
        # Show me where the place is not open: the piano roll says where
        R(pg,"openSettings('general')");pg.wait_for_timeout(300)
        ok=pick(pg,'snap','Snap in the piano roll');pg.wait_for_timeout(300)
        t=pg.evaluate("()=>{const t=document.getElementById('toast');return t?t.textContent:''}")
        ck(f'{L}: Snap with the piano roll closed says where it is',ok and 'piano roll' in t.lower(),t)
        # the Follow chip (drawn on the ruler)
        R(pg,"openSettings('general')");pg.wait_for_timeout(300)
        ok=pick(pg,'follow','Follow the playhead on or off');pg.wait_for_timeout(300)
        st=pg.evaluate("()=>{const s=document.getElementById('st6Spot'),t=document.getElementById('toast');return{on:!!s&&s.classList.contains('on'),t:t?t.textContent:''}}")
        ck(f'{L}: Follow chip is lit, or Settings says where it is',ok and (st['on'] or 'ruler' in st['t']),st)
        if not lite: pg.screenshot(path=f'{OUT}/s6_show_follow_{L}.png',clip={'x':0,'y':0,'width':900,'height':120})
        # a normal result still opens its page and flashes the row; keyboard choice
        R(pg,"openSettings('general')");pg.wait_for_timeout(300)
        search(pg,'sound card');pg.keyboard.press('Enter');pg.wait_for_timeout(400)
        ck(f'{L}: Enter on "sound card" opens Audio and flashes the row',pg.evaluate("()=>!document.getElementById('set').hidden&&document.querySelector('#setNav [data-tab].on').dataset.tab==='audio'&&!!document.querySelector('#setBody .sflash')"))
        search(pg,'metronome');pg.keyboard.press('ArrowDown');pg.keyboard.press('ArrowUp')
        ck(f'{L}: arrow keys move through the results',pg.evaluate("()=>document.querySelectorAll('#setQR button.on').length")==1)
        pg.keyboard.press('Escape')
        ck(f'{L}: no console errors',not errs,errs[:4])
        c.close()
    b.close()
print('%d/%d checks pass'%(N[1],N[0]));sys.exit(1 if FAIL else 0)
