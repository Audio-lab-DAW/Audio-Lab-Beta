#!/usr/bin/env python3
"""Task FT-C3c (Launchpad and APC, fake grids): Launchpad Mini MK3 in programmer mode, its DAW port left alone, the grid of 8 tracks by
the song's sections, launching from pads and scene buttons, arrows, Keys and Drums; APC40 MK2 in Ableton mode with faders (pick up),
knobs and LED rings, track buttons, transport and tempo; APC mini mk2 and APC mini; Works as; the Controllers page; goodbye.
   python3 tools/ui-tests/taskFT_C3c.py [index.html] [out dir]"""
import sys, os, json
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
# the fake MIDI system: FAKEMIDI.plug(name), .unplug(name), .msg(name,[bytes]); every byte AudioLab sends lands in FAKEMIDI.sent
FAKE = r"""(()=>{const F=window.FAKEMIDI={sent:[],asked:[],refuse:!!window.__refuseSysex,acc:null};
 const acc={inputs:new Map(),outputs:new Map(),onstatechange:null,sysexEnabled:false};F.acc=acc;
 const fire=p=>{if(acc.onstatechange)acc.onstatechange({port:p})};
 F.plug=(name,man,outName)=>{const id='in-'+name,oid='out-'+name;const i={id,name,manufacturer:man||'Fake',type:'input',state:'connected',onmidimessage:null};
   const o={id:oid,name:outName||name,manufacturer:man||'Fake',type:'output',state:'connected',send(d){F.sent.push({port:o.name,data:Array.from(d),t:performance.now()})}};
   acc.inputs.set(id,i);acc.outputs.set(oid,o);fire(i)};
 F.unplug=name=>{const i=acc.inputs.get('in-'+name),o=acc.outputs.get('out-'+name);if(i){i.state='disconnected';acc.inputs.delete(i.id)}if(o){o.state='disconnected';acc.outputs.delete(o.id)}fire(i)};
 F.msg=(name,b)=>{const i=acc.inputs.get('in-'+name);if(i&&i.onmidimessage)i.onmidimessage({data:new Uint8Array(b)})};
 Object.defineProperty(navigator,'requestMIDIAccess',{configurable:true,value:o=>{F.asked.push(!!(o&&o.sysex));if(o&&o.sysex&&F.refuse)return Promise.reject(new DOMException('SysEx refused','NotAllowedError'));acc.sysexEnabled=!!(o&&o.sysex);return Promise.resolve(acc)}})})()"""
INIT = "if(!sessionStorage.getItem('c1i')){sessionStorage.setItem('c1i','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"

def boot(p, refuse=False, dsf=1):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=dsf); pg = ctx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall' not in m.text and 'willReadFrequently' not in m.text): logs.append(m.type + ': ' + m.text[:200])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT + (';window.__refuseSysex=1;' if refuse else ';') + FAKE)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    return b, pg, logs, R
J = lambda R, c: json.loads(R("JSON.stringify(" + c + ")"))

LP = 'Launchpad Mini MK3 LPMiniMK3 MIDI'; LPD = 'Launchpad Mini MK3 LPMiniMK3 DAW'; A40 = 'APC40 mkII'; AM2 = 'APC mini mk2 Control'; AM2N = 'APC mini mk2 Notes'; AM1 = 'APC MINI'
def msg(R, dev, *ms): R(";".join("FAKEMIDI.msg(%s,%s)" % (json.dumps(dev), json.dumps(list(m))) for m in ms))
def sent(R, dev): return J(R, "FAKEMIDI.sent.filter(x=>x.port===%s).map(x=>x.data)" % json.dumps(dev))
val = lambda R, id: J(R, "(C=>C?C.spec.n(C.get()):null)(CT.get(%s))" % json.dumps(id))
prof = lambda R, dev: J(R, "([...CTL.devs.values()].find(d=>d.name===%s)||{prof:{}}).prof.id" % json.dumps(dev))
def state(R, dev):  # what the device shows now: key -> bytes
    return {k: list(map(int, v.split(','))) for k, v in J(R, "[...[...CTL.devs.values()].find(d=>d.name===%s).g.out]" % json.dumps(dev))}
def pads(R, dev):
    return {k: v for k, v in state(R, dev).items() if k[0] == 'n'}
def has(tr, sec, tracks):
    a, e = sec['start'], sec['start'] + sec['len']
    for c in tr['clips']:
        if c.get('mute'): continue
        c0, c1 = c['start'], c['start'] + c['len']
        if c1 <= a or c0 >= e: continue
        if c.get('notes') is None: return True
        for n in c['notes']:
            b = c0 + n['s'] - (c.get('off') or 0)
            if a <= b < e and c0 <= b < c1: return True
    if tr['kind'] == 'group':
        return any(has(m, sec, tracks) for m in tracks if m.get('grp') == tr['id'])
    return False
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 251), 'version 0.251 or later', v)
    R("initMidi()"); pg.wait_for_timeout(200)
    R("pos=0;selectTrack(S.tracks[0].id)")
    secs = J(R, "p1cSecs()"); tracks = J(R, "S.tracks"); ok(len(secs) >= 3, 'the demo song has sections', len(secs))
    # ---- Launchpad Mini MK3 ----
    R("FAKEMIDI.plug(%s,'Focusrite');FAKEMIDI.plug(%s,'Focusrite')" % (json.dumps(LPD), json.dumps(LP))); pg.wait_for_timeout(300)
    ok(prof(R, LP) == 'grid' and prof(R, LPD) == 'generic', 'Launchpad: the MIDI port is a grid, the DAW port is left alone', (prof(R, LP), prof(R, LPD)))
    ok([0xF0, 0, 0x20, 0x29, 2, 0x0D, 0x0E, 1, 0xF7] in sent(R, LP), 'programmer mode asked by SysEx (header 00 20 29 02 0D, 0E 01)')
    ok(not sent(R, LPD), 'nothing sent to the DAW port')
    P = pads(R, LP); exp = {}; errs = []
    for r in range(8):
        s = secs[r] if r < len(secs) else None
        for x in range(8):
            t = tracks[x] if x < len(tracks) else None
            n = 11 + (7 - r) * 10 + x
            c = J(R, "p1Col(%s)" % json.dumps(t['color'])) if s and t and has(t, s, tracks) else 0
            if P.get('n%d' % n) != [0x90, n, c]: errs.append((n, P.get('n%d' % n), c))
    ok(not errs, 'pads: 8 tracks across, sections down, lit in the track colour where the track plays', errs[:4])
    st = state(R, LP); ok(st.get('c89', [0, 0, 0])[2] == 1 and st.get('c95', [0, 0, 0])[2] == 21, 'scene button 1 dim (a section), Session lit green', (st.get('c89'), st.get('c95')))
    # pad top left: select track 1, play from section 1 (stopped)
    R("selectTrack(S.tracks[1].id)"); msg(R, LP, [0x90, 81 + 2, 127], [0x90, 83, 0]); pg.wait_for_timeout(300)
    ok(J(R, "play.on") and J(R, "selT") == tracks[2]['id'], 'pad 3 of the top row: track 3 selected, the song plays from section 1')
    R("stop()"); pg.wait_for_timeout(200)
    msg(R, LP, [0xB0, 79, 127], [0xB0, 79, 0]); pg.wait_for_timeout(300)
    ok(J(R, "play.on") and abs(J(R, "curBeat()") - secs[1]['start']) < 2, 'scene button 2 (CC 79), stopped: plays from section 2', (J(R, "curBeat()"), secs[1]['start']))
    msg(R, LP, [0xB0, 69, 127], [0xB0, 69, 0]); pg.wait_for_timeout(150)
    q = J(R, "P1C.q"); ok(q and q['id'] == secs[2]['id'], 'while playing, scene button 3 queues section 3', q)
    st = state(R, LP); row = [st.get('n%d' % (61 + x)) for x in range(8)]
    ok(any(r and r[0] == 0x92 and r[2] == 3 for r in row) and st.get('c69') == [0xB2, 69, 3], 'the queued row pulses white (channel 3), and its scene button', (row, st.get('c69')))
    ok(J(R, "LPG.iv") != 0, 'the 4 Hz follow runs while playing')
    msg(R, LP, [0xB0, 69, 127], [0xB0, 69, 0]); pg.wait_for_timeout(150); ok(not J(R, "P1C.q"), 'pressed again: the queue is cancelled')
    R("stop()"); pg.wait_for_timeout(500); ok(J(R, "LPG.iv") == 0, 'the follow stops with the song')
    # arrows
    if len(secs) > 8:
        msg(R, LP, [0xB0, 92, 127]); ok(J(R, "[...CTL.devs.values()].find(d=>d.name===%s).g.so" % json.dumps(LP)) == 1, 'Down: the grid shows the next section')
        msg(R, LP, [0xB0, 91, 127])
    if len(tracks) > 8:
        msg(R, LP, [0xB0, 94, 127]); ok(J(R, "LPG.tb") == 1, 'Right: the grid shows the next track'); msg(R, LP, [0xB0, 93, 127]); ok(J(R, "LPG.tb") == 0, 'Left: back')
    else:
        msg(R, LP, [0xB0, 94, 127]); ok(J(R, "LPG.tb") == 0, 'Right with 8 tracks or fewer: nothing to move')
    # keys: pads play the selected instrument in key
    inst = J(R, "(S.tracks.find(t=>t.kind==='inst')||{}).id"); R("selectTrack(%s)" % json.dumps(inst))
    msg(R, LP, [0xB0, 97, 127], [0xB0, 97, 0]); pg.wait_for_timeout(100)
    m = J(R, "p1Pad(0,0,p1S()).m"); msg(R, LP, [0x90, 11, 100]); pg.wait_for_timeout(50)
    ok(J(R, "LIVE.has('p1:'+%d)" % m) and pads(R, LP).get('n11', [0, 0, 0])[2] == 21, 'Keys: the bottom left pad plays the root note, lit green while held', m)
    msg(R, LP, [0x90, 11, 0]); pg.wait_for_timeout(50); ok(not J(R, "LIVE.has('p1:'+%d)" % m), 'released: the note stops')
    msg(R, LP, [0xB0, 96, 127]); pg.wait_for_timeout(50); msg(R, LP, [0x90, 12, 90]); ok(J(R, "LIVE.has('p1:61')"), 'Drums: 4x4 from the bottom left, pad 2 plays kit pad 2'); msg(R, LP, [0x90, 12, 0])
    P = pads(R, LP); ok(P.get('n15', [0, 0, 9])[2] == 0, 'Drums: the right half is dark')
    msg(R, LP, [0xB0, 95, 127]); ok(J(R, "[...CTL.devs.values()].find(d=>d.name===%s).g.mode" % json.dumps(LP)) == 'ses', 'Session: back to the section grid')
    # ---- APC40 MK2 ----
    R("FAKEMIDI.sent.length=0;UI.ctlTake='pickup';selectTrack(S.tracks[0].id)"); R("FAKEMIDI.plug(%s,'Akai')" % json.dumps(A40)); pg.wait_for_timeout(300)
    ok(prof(R, A40) == 'grid' and [0xF0, 0x47, 0x7F, 0x29, 0x60, 0, 4, 0x41, 0, 0, 0, 0xF7] in sent(R, A40), 'APC40 MK2: a grid, Ableton Live mode asked (47 7F 29 60, mode 41)')
    st = state(R, A40); n0 = 32 + 0
    ok(st.get('n32') and st['n32'][0] == 0x90 and ('n40' not in st), 'APC40: 5 rows (notes 0 to 39), top left is note 32, solid on channel 1', st.get('n32'))
    t0 = tracks[0]['id']; v0 = val(R, 'hd:' + t0); far = 0 if v0 > .5 else 127
    msg(R, A40, [0xB0, 7, far]); ok(abs(val(R, 'hd:' + t0) - v0) < .002, 'fader 1 far from the level: pick up waits', (v0, far))
    msg(R, A40, [0xB0, 7, round(v0 * 127)], [0xB0, 7, 64]); ok(abs(val(R, 'hd:' + t0) - 64 / 127) < .002, 'fader 1 caught at the level, then moves track 1 level', val(R, 'hd:' + t0))
    ms0 = val(R, 'ms'); msg(R, A40, [0xB0, 14, round(ms0 * 127)], [0xB0, 14, 90]); ok(abs(val(R, 'ms') - 90 / 127) < .002, 'master fader (CC 14) on the master')
    R("UI.ctlTake='jump'")
    mu = J(R, "S.tracks[2].mute"); msg(R, A40, [0x92, 0x32, 127], [0x82, 0x32, 0]); pg.wait_for_timeout(100)
    ok(J(R, "S.tracks[2].mute") != mu and state(R, A40).get('b2:50', [0, 0, 9])[2] == (1 if mu else 0), 'activator 3 (note 0x32, channel 3): track 3 muted, its LED follows', state(R, A40).get('b2:50'))
    msg(R, A40, [0x92, 0x32, 127]); pg.wait_for_timeout(50)
    msg(R, A40, [0x93, 0x33, 127]); pg.wait_for_timeout(100); ok(J(R, "selT") == tracks[3]['id'], 'track select 4 selects track 4')
    ids = J(R, "ctlTDev().ids"); st = state(R, A40)
    ok(ids and st.get('rt0') == [0xB0, 0x18, 1], 'device knob 1 ring set to single (CC 0x18) for the selected device', (ids[:2], st.get('rt0')))
    if ids:
        msg(R, A40, [0xB0, 0x10, 100]); ok(abs(val(R, ids[0]) - 100 / 127) < .01, 'device knob 1 (CC 16) moves the selected device knob 1', val(R, ids[0]))
        pg.wait_for_timeout(100); ok(state(R, A40).get('rv0') == [0xB0, 0x10, round(val(R, ids[0]) * 127)], 'its LED ring value follows')
    msg(R, A40, [0xB0, 0x30, 20]); ok(abs(val(R, 'hp:' + t0) - 20 / 127) < .01, 'track knob 1 (CC 48) pans track 1', val(R, 'hp:' + t0))
    ok(state(R, A40).get('pt0') == [0xB0, 0x38, 3], 'track knob ring type pan')
    ck = J(R, "!!S.click"); msg(R, A40, [0x90, 90, 127]); pg.wait_for_timeout(100); ok(J(R, "!!S.click") != ck, 'Metronome toggles the click'); msg(R, A40, [0x90, 90, 127])
    bpm = J(R, "S.bpm"); u0 = J(R, "UNDO.length"); msg(R, A40, [0xB0, 13, 1], [0xB0, 13, 1]); pg.wait_for_timeout(50)
    ok(abs(J(R, "S.bpm") - bpm - 2) < 1e-6 and J(R, "UNDO.length") - u0 == 1, 'tempo knob: 2 steps up = 2 BPM, one undo step', (bpm, J(R, "S.bpm")))
    R("setBpm(%s)" % bpm)
    msg(R, A40, [0x90, 91, 127]); pg.wait_for_timeout(300); pl = J(R, "play.on"); pg.wait_for_timeout(100)
    ok(pl and state(R, A40).get('b0:91', [0, 0, 0])[2] == 1, 'Play plays, its LED lit')
    msg(R, A40, [0x90, 32 + 1, 127]); pg.wait_for_timeout(100); ok(J(R, "P1C.q") is not None or len(secs) < 1, 'a pad while playing queues its section')
    msg(R, A40, [0x90, 92, 127]); pg.wait_for_timeout(300); ok(not J(R, "play.on") and not J(R, "P1C.q"), 'Stop stops and clears the queue')
    # a learned mapping wins
    R("ctlG().maps.push({id:'mx',dev:%s,type:'cc',ch:0,num:14,target:'hd:'+S.tracks[1].id,min:0,max:1,take:'jump',enc:'abs',fb:false});ctlDirty()" % json.dumps(A40))
    ms0 = val(R, 'ms'); msg(R, A40, [0xB0, 14, 10]); ok(abs(val(R, 'ms') - ms0) < .002 and abs(val(R, 'hd:' + tracks[1]['id']) - 10 / 127) < .01, 'a mapping learned on the master fader wins')
    R("ctlG().maps=ctlG().maps.filter(m=>m.id!=='mx');ctlDirty()")
    # ---- APC mini mk2 ----
    R("FAKEMIDI.plug(%s,'Akai');FAKEMIDI.plug(%s,'Akai')" % (json.dumps(AM2), json.dumps(AM2N))); pg.wait_for_timeout(300)
    ok(prof(R, AM2) == 'grid' and prof(R, AM2N) == 'generic', 'APC mini mk2: the Control port is a grid, the Notes port is left alone')
    P = pads(R, AM2); lit = [v for v in P.values() if v[2]]; ok(lit and all(v[0] == 0x96 for v in lit), 'mk2 pads lit at full brightness (channel 7)', lit[:2])
    msg(R, AM2, [0xB0, 48, 30]); ok(abs(val(R, 'hd:' + t0) - 30 / 127) < .01, 'mk2 fader 1 (CC 48) moves track 1 level (jump)')
    msg(R, AM2, [0x90, 122, 127], [0x90, 105, 127], [0x80, 122, 0]); msg(R, AM2, [0xB0, 48, 127]); ok(abs(val(R, 'hp:' + t0) - 1) < .01, 'Shift + track button 6: faders on pan', val(R, 'hp:' + t0))
    msg(R, AM2, [0x90, 122, 127], [0x90, 104, 127], [0x80, 122, 0])
    msg(R, AM2, [0x90, 101, 127]); pg.wait_for_timeout(100); ok(J(R, "selT") == tracks[1]['id'] and state(R, AM2).get('b0:101', [0, 0, 0])[2] == 1, 'track button 2 selects track 2, its LED lit')
    # ---- APC mini ----
    R("FAKEMIDI.plug(%s,'Akai')" % json.dumps(AM1)); pg.wait_for_timeout(300)
    P = pads(R, AM1); ok(prof(R, AM1) == 'grid' and P and {v[2] for v in P.values()} <= {0, 1, 2, 3, 5, 6}, 'APC mini: green, red and yellow only', sorted({v[2] for v in P.values()}))
    # ---- Works as ----
    R("FAKEMIDI.plug('Fake Grid','Fake')"); pg.wait_for_timeout(100); ok(prof(R, 'Fake Grid') == 'generic', 'an unknown device stays generic')
    R("FAKEMIDI.sent.length=0;FT_HOOKS.surfaceAs('Fake Grid','lpx')"); pg.wait_for_timeout(100)
    ok(prof(R, 'Fake Grid') == 'grid' and [0xF0, 0, 0x20, 0x29, 2, 0x0C, 0x0E, 1, 0xF7] in sent(R, 'Fake Grid'), 'Works as Launchpad X: programmer mode with device id 0C')
    R("FT_HOOKS.surfaceAs('Fake Grid','')"); pg.wait_for_timeout(100); ok(prof(R, 'Fake Grid') == 'generic' and [0xF0, 0, 0x20, 0x29, 2, 0x0C, 0x0E, 0, 0xF7] in sent(R, 'Fake Grid'), 'back to Automatic: generic again, the Launchpad back in Live mode')
    # ---- page ----
    R("ctlPage()"); pg.wait_for_timeout(300)
    ok(J(R, "[...document.querySelectorAll('#ctlWin .mcset select option[data-lp]')].length") >= 6 * 6, 'Works as lists the six models for every device')
    ok(J(R, "!!document.querySelector('#ctlWin .lpinfo')&&!!document.querySelector('#ctlWin .lpinfo').title"), 'a line on what the grid does, with a tooltip')
    ok('—' not in R("[...document.querySelectorAll('#ctlWin .mcset *')].map(e=>e.textContent+(e.title||'')).join(' ')"), 'no em dash')
    pg.screenshot(path=os.path.join(OUT, 'c3c_page.png'))
    R("document.documentElement.classList.add('light')"); pg.wait_for_timeout(200); pg.screenshot(path=os.path.join(OUT, 'c3c_page_light.png')); R("document.documentElement.classList.remove('light')")
    # goodbye
    R("FAKEMIDI.sent.length=0;dispatchEvent(new Event('pagehide'))")
    lo = [d for d in sent(R, LP) if d[0] & 0xF0 in (0x90, 0xB0) and d[2]]
    ok(not lo and [0xF0, 0, 0x20, 0x29, 2, 0x0D, 0x0E, 0, 0xF7] in sent(R, LP), 'page hidden: Launchpad dark and back in Live mode')
    ok(not [d for d in sent(R, A40) if d[0] & 0xF0 in (0x90, 0xB0) and d[2]], 'page hidden: APC40 dark, rings off')
    R("FAKEMIDI.unplug(%s)" % json.dumps(AM1)); pg.wait_for_timeout(200); ok(J(R, "[...CTL.devs.values()].filter(d=>d.name===%s).length" % json.dumps(AM1)) == 0, 'unplugged APC mini is gone')
    R("window.__to=[];{const o=setTimeout,i=setInterval;window.setTimeout=function(){const s=(new Error().stack||'');if(/lp[A-Z]/.test(s))__to.push(s.slice(0,200));return o.apply(this,arguments)};window.setInterval=function(){const s=(new Error().stack||'');if(/lp[A-Z]/.test(s))__to.push(s.slice(0,200));return i.apply(this,arguments)}}"); pg.wait_for_timeout(1500)
    ok(J(R, "__to") == [] and J(R, "LPG.iv") == 0, 'nothing of the grids runs while stopped and still', J(R, "__to"))
    ok(not logs, 'no console errors', logs)
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
