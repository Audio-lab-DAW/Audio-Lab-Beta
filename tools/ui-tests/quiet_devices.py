"""No sound from clicking devices (task AA): python3 tools/ui-tests/quiet_devices.py [index.html] [only,names] [stopped|playing|both]
For every instrument (and every effect on a Pluck track) clicks and drags on the picture, drags every knob and slider, clicks the device's own
buttons (not remove, Change, pin, show parameters, on/off, or an explicit play button) and picks the next entry of every menu (presets too),
first while stopped and then while playing past the end of the song (the transport runs, the track has nothing to play).
The whole output (before the speakers) is tapped on the audio thread: any added energy above -90 dBFS is a failure. Explicit play buttons are
clicked last and must make a sound (they are kept on purpose)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
only = sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] else None
modes = {'stopped': ['stopped'], 'playing': ['playing']}.get(sys.argv[3] if len(sys.argv) > 3 else 'both', ['stopped', 'playing'])
FAIL = []
def ok(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: FAIL.append(m)
al = AudioLab(F, 1600, 1000); al.start()
al.build({'tracks': [{'name': 'B', 'preset': 'pluck', 'clips': [{'start': 0, 'len': 4, 'notes': [{'p': 60, 's': 0, 'l': 1, 'v': .9}]}]}]})
pg = al.page
insts = json.loads(al.run("JSON.stringify(IBG.flatMap(g=>g[2]))")); fxs = json.loads(al.run("JSON.stringify(FBG.flatMap(g=>g[2]))"))
# the tap: peak of the whole output, block by block, on the audio thread
al.run("""(()=>{ensureCtx();ctx.resume();if(window.__tap)return 1;const sp=ctx.createScriptProcessor(1024,2,1),z=ctx.createGain();z.gain.value=0;outBus.connect(sp);sp.connect(z);z.connect(ctx.destination);
 window.__tap={pk:0,sp};sp.onaudioprocess=e=>{for(let c=0;c<2;c++){const d=e.inputBuffer.getChannelData(c);for(let i=0;i<d.length;i++){const a=Math.abs(d[i]);if(a>__tap.pk)__tap.pk=a}}};
 window.__calls=[];for(const n of ['preview','padHear','prevSet','voiceOn','pvPlay','gvPlay','kitPlay','kickPlay','padPlay']){let f;try{f=eval(n)}catch(e){continue}if(typeof f!=='function')continue;window['__q_'+n]=f;
   eval(n+"=function(){if(!(arguments[1]&&arguments[1].length===0))__calls.push('"+n+"'+(typeof dqOn==='function'?(dqOn()?'(gated)':''):''));return window.__q_"+n+".apply(this,arguments)}")}
 return 1})()""")
def reset_tap(): al.run("(()=>{__tap.pk=0;__calls.length=0;return 1})()")
def quiet():
    for _ in range(40):
        reset_tap(); pg.wait_for_timeout(120)
        if tap()[0] < 10 ** (-90 / 20): return True
    return False
def tap(): return json.loads(al.run("JSON.stringify([__tap.pk,__calls.slice()])"))
SKIP = "'.dsrm,.duchg,.pinbtn,.duar,.dveye,.pw,.fxov,[data-ip=play],[data-dk=play],[data-kk=play],[data-seltrk],[data-mst],[data-s=browse],.dchg'"
PLAYB = "[...D.querySelectorAll('[data-ip=play],[data-dk=play],[data-kk=play],button')].filter(b=>b.offsetParent&&b.matches('[data-ip=play],[data-dk=play],[data-kk=play]'))"
DEV = "[...fxin.querySelectorAll(':scope>.dev[data-d=%s]')][%s]"
def targets(kind, idx):
    return json.loads(al.run("""(()=>{const D=%s;if(!D)return '[]';D.scrollIntoView({inline:'nearest',block:'nearest'});const out=[],vis=e=>{const r=e.getBoundingClientRect();return e.offsetParent&&r.width>2&&r.height>2&&r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight};
  const lab=e=>(e.title||e.dataset.c||e.dataset.k||e.textContent||e.className||e.tagName).toString().trim().slice(0,28);
  D.querySelectorAll('canvas').forEach((c,i)=>{if(vis(c)&&c.getBoundingClientRect().width>40)out.push({t:'pic',i,l:'picture '+(c.dataset.k||i)})});
  D.querySelectorAll('.kn,.vb,.hb').forEach((c,i)=>{if(vis(c))out.push({t:'drag',i,l:lab(c)})});
  D.querySelectorAll('button,[data-aw],[data-sk],[data-rt],[data-sf],[data-st],[data-sm],[data-pad],[data-dk],.dpad').forEach((c,i)=>{if(vis(c)&&!c.closest(%s)&&!c.matches(%s)&&!/load|record|microphone|import|file|^Pin|window/i.test(c.title||''))out.push({t:'btn',i,l:lab(c)})});
  D.querySelectorAll('select').forEach((c,i)=>{if(vis(c))out.push({t:'sel',i,l:'menu '+(c.dataset.s||c.dataset.x||c.dataset.wt||i)})});return JSON.stringify(out)})()""" % (DEV % (kind, idx), SKIP, SKIP)))
def box(kind, idx, q, i):
    return json.loads(al.run("(()=>{const D=%s;if(!D)return 'null';const e=[...D.querySelectorAll(%s)][%d];if(!e)return 'null';const r=e.getBoundingClientRect();return JSON.stringify([r.left,r.top,r.width,r.height])})()" % (DEV % (kind, idx), json.dumps(q), i)))
QS = {'pic': 'canvas', 'drag': '.kn,.vb,.hb', 'btn': 'button,[data-aw],[data-sk],[data-rt],[data-sf],[data-st],[data-sm],[data-pad],[data-dk],.dpad'}
def act(kind, idx, T):
    m = pg.mouse
    if T['t'] == 'sel':
        al.run("(()=>{const D=%s;if(!D)return 0;const s=[...D.querySelectorAll('select')][%d];if(!s)return 0;const o=[...s.options].filter(o=>!o.value.startsWith('@')&&!o.disabled);if(o.length<2)return 0;const i=o.findIndex(x=>x.value===s.value);s.value=o[(i+1)%%o.length].value;s.dispatchEvent(new Event('input',{bubbles:true}));s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()" % (DEV % (kind, idx), T['i'])); return
    b = box(kind, idx, QS[T['t']], T['i'])
    if not b: return
    x, y, w, h = b
    if T['t'] == 'pic':
        for fx, fy in ((.5, .5), (.2, .3), (.8, .7), (.35, .8), (.65, .25)):
            m.click(x + w * fx, y + h * fy); pg.wait_for_timeout(40)
        m.move(x + w * .3, y + h * .5); m.down(); m.move(x + w * .5, y + h * .4, steps=6); m.move(x + w * .7, y + h * .6, steps=6); m.up()
        pg.wait_for_timeout(40); m.dblclick(x + w * .5, y + h * .5)
    elif T['t'] == 'drag':
        m.move(x + w / 2, y + h / 2); m.down(); m.move(x + w / 2, y + h / 2 - 20, steps=5); m.up()
    else:
        m.click(x + w / 2, y + h / 2)
    pg.keyboard.press('Escape')
def fresh():
    al.run("(()=>{try{for(const k of [...PIN.wins.keys()])pinOff(k)}catch(e){}return 1})()")
    for _ in range(3):
        if not al.run("(typeof CHG!=='undefined'&&!!CHG)||!fxin.querySelector('.dev[data-d=inst],.dev[data-d=fx]')"): break
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
def device(kind, idx, name, mode):
    fresh()
    al.run("renderFx();1"); pg.wait_for_timeout(250)
    loud = []
    last = None
    for T in targets(kind, idx):
        if not al.run("!!%s" % (DEV % (kind, idx))):
            for _ in range(3):
                pg.keyboard.press('Escape'); pg.wait_for_timeout(250)
            al.run("renderFx();1"); pg.wait_for_timeout(300)
            if not al.run("!!%s" % (DEV % (kind, idx))): print('    (the device went away after: %s)' % (last and last['l'])); break
        last = T
        q0 = quiet(); reset_tap(); act(kind, idx, T); pg.wait_for_timeout(260)
        pk, calls = tap()
        if pk > 10 ** (-90 / 20):  # confirm once more after a longer silence (a sound from an earlier step can arrive late)
            pg.wait_for_timeout(1500); q0 = quiet(); reset_tap(); act(kind, idx, T); pg.wait_for_timeout(260); pk, calls = tap()
        if pk > 10 ** (-90 / 20): loud.append('%s%s (%.1f dB%s)' % ('' if q0 else '[not quiet before] ', T['l'], 20 * __import__('math').log10(pk), ' ' + ','.join(sorted(set(calls))) if calls else ''))
        # the click may have changed the device (another sample type, a mode); keep going on the new one
    al.run("(()=>{for(const id of ['vnWin','gridWin']){const w=document.getElementById(id);if(w&&!w.hidden){const c=w.querySelector('.fwc');if(c)c.click()}}return 1})()")
    ok(not loud, '%-8s %-9s %-10s %s' % (mode, kind, name, ('sound from: ' + '; '.join(loud)) if loud else 'silent'))
    return loud
def explicit(kind, idx, name):
    fresh()
    n = al.run("(()=>{const D=%s;if(!D)return -1;return %s.length})()" % (DEV % (kind, idx), PLAYB))
    if n < 0: print('    (no device to test: %s)' % al.run("[...fxin.children].map(c=>c.tagName+'.'+String(c.className.baseVal??c.className).slice(0,30)+':'+(c.dataset&&c.dataset.d||'')).join(' | ')+' fx:'+document.getElementById('fx').className")); return
    for i in range(n):
        b = json.loads(al.run("(()=>{const D=%s,e=%s[%d];if(!e)return '[0,0,\"\"]';e.scrollIntoView({block:'nearest',inline:'nearest'});const r=e.getBoundingClientRect();return JSON.stringify([r.left+r.width/2,r.top+r.height/2,e.title])})()" % (DEV % (kind, idx), PLAYB, i)))
        if not b[0]: continue
        quiet(); reset_tap(); pg.mouse.click(b[0], b[1]); pg.wait_for_timeout(900); pk, calls = tap()
        ok(pk > 1e-3, 'explicit play button kept: %s %s "%s" %.1f dB' % (kind, name, b[2], 20 * __import__('math').log10(max(pk, 1e-9))))
for mode in modes:
    if mode == 'playing': al.run("(()=>{S.loop=false;pos=4096;start();return 1})()"); pg.wait_for_timeout(600)
    else: al.run("(()=>{if(play.on)stop();return 1})()"); pg.wait_for_timeout(300)
    for k in insts:
        if only and k not in only: continue
        al.run("(()=>{const t=S.tracks[0];t.fx=[];for(const key of Object.keys(t.inst))delete t.inst[key];Object.assign(t.inst,JSON.parse(JSON.stringify(PRESETS['%s'])),{preset:'%s'});selT=t.id;changed(true);renderFx();return 1})()" % (k, k))
        pg.wait_for_timeout(1500); quiet()
        if mode == 'playing': al.run("(()=>{if(!play.on){pos=4096;start()}return 1})()")
        if mode == 'stopped': explicit('inst', 0, k)
        device('inst', 0, k, mode)
    al.run("(()=>{const t=S.tracks[0];for(const key of Object.keys(t.inst))delete t.inst[key];Object.assign(t.inst,JSON.parse(JSON.stringify(PRESETS.pluck)),{preset:'pluck'});changed(true);renderFx();return 1})()")
    for k in fxs:
        if only and k not in only: continue
        al.run("(()=>{const t=S.tracks[0];t.fx=[mkFx('%s')];selT=t.id;changed(true);renderFx();return 1})()" % k); pg.wait_for_timeout(700)
        device('fx', 0, k, mode)
    al.run("(()=>{if(play.on)stop();return 1})()")
ok(not al.errors, 'no page errors ' + '; '.join(al.errors[:3]))
print('\n%d failures' % len(FAIL)); al.stop(); sys.exit(1 if FAIL else 0)
