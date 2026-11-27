#!/usr/bin/env python3
"""Task LT-2 (lane J): the played track skips delay compensation (L4); recorded notes placed by the compensated clock.
The start project (Fractals): arming the Lead takes its compensation delay to 0 (6 ms, and 52 ms with a resonance suppressor on the Bass) with a
ramp, the other tracks and the song's compensation (CPU.pdc) unchanged, the exporter's map (pdcMap without the live flag) unchanged; disarming
puts it back; the computer keyboard's selected track likewise; delay compensation off: nothing; LT_HOOKS.pdcOut lists what is skipped.
Recording: presses timed by the output clock land within a millisecond or two of what was heard, with and without the suppressor.
No console errors.   python3 tools/ui-tests/taskLT_2.py [index.html] [out dir]"""
import sys, os, json, statistics as st
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)[:300]) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)
INIT = "if(!sessionStorage.getItem('c1i')){sessionStorage.setItem('c1i','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
REC = """(async(reson)=>{const w=ms=>new Promise(r=>setTimeout(r,ms));for(const t of S.tracks)t.arm=false;const lead=S.tracks.find(t=>t.name==='Lead');lead.arm=true;
 const b=S.tracks.find(t=>t.name==='Bass');b.fx=b.fx.filter(f=>!f._lt2);if(reson){const f=mkFx('reson');f._lt2=1;b.fx.push(f)}changed(true);syncGraph();await w(400);
 S.loop=false;UI.recOff=0;UI.countIn=0;UI.metro=false;const n0=lead.clips.length;pos=(81-1)*4;recStart();await w(2500);const P=[];
 for(let i=0;i<10;i++){await w(160+Math.random()*140);const pn=performance.now(),o=ctx.getOutputTimestamp(),spk=o.contextTime+(pn-o.performanceTime)/1000,tgt=CPU.pdc||0;
  const h0=beatOf(secOf(play.b0)+(spk-tgt-play.t0));noteOn(60+i%5,.8,'lt2k'+i);const pn2=performance.now(),o2=ctx.getOutputTimestamp(),h1=beatOf(secOf(play.b0)+(o2.contextTime+(pn2-o2.performanceTime)/1000-(pn2-pn)/1000-tgt-play.t0));
  P.push({h0,h1});await w(90);noteOff('lt2k'+i)}
 await w(300);stop();await w(400);const c=lead.clips.slice(n0).find(c=>/take/.test(c.name));if(!c)return{err:'no take'};
 const got=c.notes.map(n=>c.start+n.s).sort((a,b)=>a-b),spb=60/S.bpm;const e=got.map((g,i)=>(g-(P[i].h0+P[i].h1)/2)*spb*1000),jump=P.map(q=>Math.abs(q.h1-q.h0)*spb*1000);const target=(CPU.pdc||0)*1000;
 lead.clips.splice(n0);b.fx=b.fx.filter(f=>!f._lt2);changed(true);return{n:e.length,e,jump,target}})"""

with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    cx = b.new_context(viewport={'width': 1600, 'height': 1000}); pg = cx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall' not in m.text and 'willReadFrequently' not in m.text): logs.append(m.type + ': ' + m.text[:300])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    print('version', R("VERSION"))
    # the headless output has no device and underruns at random: a fixed buffer, the playing buffer off, so nothing restarts mid-test
    R("UI.buf=256;UI.ltPlayBuf=0;urNow=()=>-1;Object.defineProperty(CPU,'dropT',{configurable:true,get(){return -9},set(v){}});restartAudio(true);0")
    pg.wait_for_timeout(800)
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));ensureCtx();await ctx.resume();for(const t of S.tracks)t.arm=false;UI.kbPiano=false;CAPS=false;changed(true);syncGraph();await w(400);
      const sr=ctx.sampleRate,ms=t=>+(NODES.get(t.id).pdc.delayTime.value*1000).toFixed(2),lead=S.tracks.find(t=>t.name==='Lead'),kick=S.tracks.find(t=>t.name==='Kick');
      const o={has:!!lead&&!!kick,t0:+(CPU.pdc*1000).toFixed(2),lead0:ms(lead),kick0:ms(kick)};lead.arm=true;changed(true);syncGraph();await w(8);o.mid=ms(lead);await w(300);
      o.lead1=ms(lead);o.kick1=ms(kick);o.t1=+(CPU.pdc*1000).toFixed(2);o.exp=+((pdcMap(sr).get(lead.id)||0)/sr*1000).toFixed(2);o.out=LT_HOOKS.pdcOut().map(x=>x.name+' '+x.ms.toFixed(1));
      const bs=S.tracks.find(t=>t.name==='Bass');const f=mkFx('reson');bs.fx.push(f);changed(true);syncGraph();await w(400);await w(400);o.rt=+(CPU.pdc*1000).toFixed(2);o.rlead=ms(lead);o.rkick=+(NODES.get(kick.id).pdcV*1000).toFixed(2);/* what syncGraph sets (its setValueAtTime sometimes does not take on this machine, old builds too: tools/engine-lab/lt/pdc_set_probe.py) */o.rkickExp=+((pdcMap(sr).get(kick.id)||0)/sr*1000).toFixed(2);
      lead.arm=false;changed(true);syncGraph();await w(20);o.rmid=ms(lead);await w(400);o.rback=ms(lead);bs.fx.pop();changed(true);syncGraph();await w(400);o.back=ms(lead);return o})()""")
    ok(r['has'], 'the start project has the Lead and the Kick', r)
    ok(r['lead0'] > 5.9 and r['lead1'] == 0, 'arming the Lead takes its compensation delay from %.2f ms to 0' % r['lead0'], r)
    ok(r['kick1'] == r['kick0'] and r['t1'] == r['t0'], 'the other tracks and the song compensation stay', r)
    ok(abs(r['exp'] - r['lead0']) < .01, "the exporter's map (no live flag) is unchanged while the Lead is armed", r['exp'])
    ok(any(x.startswith('Lead ') for x in r['out']), 'LT_HOOKS.pdcOut lists the Lead', r['out'])
    ok(r['rt'] > 50 and r['rlead'] == 0 and abs(r['rkick'] - r['rkickExp']) < .05 and r['rkickExp'] > 40, 'with a resonance suppressor on the Bass (%.1f ms) the armed Lead still skips it' % r['rt'], r)
    ok(0 < r['rmid'] < r['rt'] and abs(r['rback'] - r['rt']) < .05, 'disarmed: back to the full compensation, ramped over 0.2 s (no jump, no click)', r)
    ok(abs(r['back'] - r['lead0']) < .01, 'suppressor removed: back to %.2f ms' % r['lead0'], r['back'])
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const lead=S.tracks.find(t=>t.name==='Lead'),ms=t=>+(NODES.get(t.id).pdc.delayTime.value*1000).toFixed(2);selT=lead.id;UI.kbPiano=true;ltPdcEval();await w(500);
      const o={kb:ms(lead)};UI.kbPiano=false;ltPdcEval();await w(500);o.off=ms(lead);UI.pdc=false;lead.arm=true;changed(true);syncGraph();await w(300);o.pdcOff=ms(lead);o.rec=ltRecSec(lead);UI.pdc=true;lead.arm=false;changed(true);syncGraph();await w(300);return o})()""")
    ok(r['kb'] == 0 and r['off'] > 5.9, 'the computer keyboard playing the selected Lead: it skips compensation; keyboard off: back', r)
    ok(r['pdcOff'] == 0 and r['rec'] == 0, 'delay compensation off: nothing to skip, no shift of the take', r)
    for reson in (False, True):
        r = pg.evaluate("([c,x])=>AudioLab.run('('+c+')('+x+')')", [REC, 'true' if reson else 'false'])
        e = r.get('e') or []; j = r.get('jump') or []
        good = [x for x, q in zip(e, j) if q < 1]
        md = st.median(good) if good else 99; wa = max(abs(x) for x in good) if good else 99
        ok(len(e) == 10 and len(good) >= 7 and abs(md) < 1 and wa < 1.5, 'recording %s (compensation %.1f ms): notes land %.2f ms from what was heard (median), worst %.2f ms; %d of 10 presses judged (the others: the browser\'s output clock jumped by more than 1 ms during the press)' % ('with the suppressor' if reson else 'Fractals as built', r.get('target', 0), md, wa, len(good)), [(round(x, 2), round(q, 2)) for x, q in zip(e, j)])
    ok(not logs, 'no console errors', logs[:5])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
