#!/usr/bin/env python3
"""Task FT-F9b (step sequencer clips, part 2): ready-made patterns (Roll for Psy Bass with the first hit lower, Psy drums), accent and slide
as Acid hears them (a glide into the note after a slide), a step clip to a normal MIDI clip and back (exact, and read from notes:
step size, ratchets, slides, accents, chance, gate; off-grid notes counted), Push 1's drum step lane on a step clip, linked copies.
   python3 tools/ui-tests/taskFT_F9b.py [index.html] [out dir]"""
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
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
 F.plug=(name,man,outName)=>{/* from v0.261 (task HF1) a control surface works only once the user turned it on in Controllers: these tests turn every fake device on */try{AudioLab.run('UI.ctlOn=Object.assign({},UI.ctlOn||{},{'+JSON.stringify(name)+':1})')}catch(e){}const id='in-'+name,oid='out-'+name;const i={id,name,manufacturer:man||'Fake',type:'input',state:'connected',onmidimessage:null};
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
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script(INIT + (';window.__refuseSysex=1;' if refuse else ';') + FAKE)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    return b, pg, logs, R
J = lambda R, c: json.loads(R("JSON.stringify(" + c + ")"))

import base64, hashlib
TR = []
def rhash(pg, b0, b1, tid):
    h = pg.evaluate("o=>AudioLab.render(o)", {'b0': b0, 'b1': b1, 'sr': 44100, 'only': tid}); m = hashlib.md5()
    for ch in range(h['ch']):
        for off in range(0, h['len'], 1 << 18):
            n = min(1 << 18, h['len'] - off); m.update(base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])", [h['id'], ch, off, n])))
    pg.evaluate("i=>AudioLab.free(i)", h['id']); return m.hexdigest()[:12]
NOTES = "findClip(%s).c.notes.map(n=>[n.p,n.s,n.l,n.v,n.ch||1,n.ac||0,n.sl||0])"
def cell_xy(R, row, i, lane=None):
    return J(R, "(()=>{const f=ftSqClip(),st=f.c.steps,G=ftSqGeo(st),r=FTSQ.cv.getBoundingClientRect(),z=ZOOM||1;const y=%s;return[r.left+(FTSQ.LW+%d*G.cw+G.cw/2)*z,r.top+y*z]})()" % (("%d*FTSQ.RH+FTSQ.RH/2" % row) if lane is None else ("G.ly+%d*FTSQ.LH+(FTSQ.LH-5)/2" % lane), i))
def menu_labels(R): return J(R, "[...document.querySelectorAll('#ctxm button')].map(b=>b.textContent.trim())")
def menu_click(R, label):
    return R("(()=>{const b=[...document.querySelectorAll('#ctxm button')].find(b=>b.textContent.trim().startsWith(%s));if(!b)return 'none';b.click();return 'ok'})()" % json.dumps(label))

PUSH = 'Ableton Push'
def msg(R, *ms): R(";".join("FAKEMIDI.msg('Ableton Push',%s)" % json.dumps(list(m)) for m in ms))
def sel_pat(R, v): R("(()=>{const s=FTSQ.el.querySelector('[data-a=pat]');s.value=%s;s.dispatchEvent(new Event('change',{bubbles:true}))})()" % json.dumps(v))
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 278), 'version 0.278 or later', v)
    ok(J(R, "['clip.toSteps','clip.toNotes'].every(i=>SCA.some(a=>a.id===i))"), 'commands clip.toSteps and clip.toNotes in the registry')
    ok(J(R, "typeof FT_HOOKS.stepConvert.toSteps==='function'&&FT_HOOKS.stepConvert.presets('key').length===4"), 'hook FT_HOOKS.stepConvert')
    F0 = J(R, "S.tracks.flatMap(t=>t.clips.filter(c=>c.notes).slice(0,2).map(c=>c.id))")
    ok(all(J(R, "ccSus(findClip(%s).c,findClip(%s).c.notes)===findClip(%s).c.notes" % ((json.dumps(i),) * 3)) for i in F0[:6]) and J(R, "S.tracks.every(t=>t.clips.every(c=>!c.nch&&!c.steps))"), 'Fractals: no step or converted clips, notes untouched')
    R("initMidi()"); pg.wait_for_timeout(150)
    R("AudioLab.build({bpm:145,tracks:[{name:'Kit',preset:'drums'},{name:'Psy',preset:'psyb'},{name:'Acid',preset:'acid'},{name:'Saw',preset:'saw'},{name:'Saw copy',preset:'saw'}]})"); pg.wait_for_timeout(500)
    KIT, PSY, ACID, SAW, SAW2 = J(R, "S.tracks.map(t=>t.id)")
    # Roll on Psy Bass
    R("selT=%s;PR.root=9;PR.scale='minor';" % json.dumps(PSY)); R("SCA.find(a=>a.id==='clip.newSteps').run()"); pg.wait_for_timeout(150); C = J(R, "selC")
    opts = J(R, "[...FTSQ.el.querySelectorAll('[data-a=pat] option')].map(o=>[o.value,o.textContent,o.title])")
    ok([o[0] for o in opts] == ['', 'roll', 'gallop', 'off', 'clear'] and all(len(o[2]) > 15 for o in opts[1:]), 'Pattern menu on a bass: Roll, Gallop, Off-beat, Clear all, each with a tooltip', [o[1] for o in opts])
    u0 = J(R, "UNDO.length"); sel_pat(R, 'roll'); pg.wait_for_timeout(80)
    st = J(R, "findClip(%s).c.steps" % json.dumps(C)); r = len(st['rows']) - 1
    on = [i for i, q in enumerate(st['g'][r]) if q is not None]
    ok(on == [i for i in range(16) if i % 4], 'Roll: the bass on the three 16ths after each kick (K B B B), on the root', on)
    ok(st['rows'][r]['p'] % 12 == 9 and all(not any(st['g'][k]) for k in range(r)), 'only the root row (A)', st['rows'][r])
    n = J(R, NOTES % json.dumps(C))
    ok(len(n) == 12 and n[0][1] == .25 and n[0][3] < n[1][3] and n[3][3] < n[4][3] and n[1][3] == n[2][3], 'the first hit of each roll is lower', [q[3] for q in n[:4]])
    ok(J(R, "UNDO.length") - u0 == 1 and J(R, "FTSQ.el.querySelector('[data-a=pat]').value") == '', 'one undo step; the menu goes back to Choose…')
    pg.screenshot(path=os.path.join(OUT, 'f9b_roll.png'))
    # Psy drums on the kit
    R("ftSqClose();selT=%s" % json.dumps(KIT)); R("SCA.find(a=>a.id==='clip.newSteps').run()"); pg.wait_for_timeout(150); CK = J(R, "selC")
    opts = J(R, "[...FTSQ.el.querySelectorAll('[data-a=pat] option')].map(o=>o.value)"); ok(opts == ['', 'four', 'psy', 'clear'], 'on a drum kit: Four on the floor, Psy drums, Clear all', opts)
    sel_pat(R, 'psy'); g = J(R, "(()=>{const c=findClip(%s).c,P=ensurePads(S.tracks[0].inst),r=ty=>c.steps.rows.findIndex(x=>x.p===36+P.findIndex(p=>p.type===ty));return[r('kick'),r('clap'),r('chat'),c.steps.g]})()" % json.dumps(CK))
    row = lambda k: [i for i, q in enumerate(g[3][k]) if q is not None]
    ok(row(g[0]) == [0, 4, 8, 12] and row(g[1]) == [4, 12] and row(g[2]) == [2, 6, 10, 14], 'Psy drums: kick on every beat, clap on 2 and 4, closed hat on the off-beats', (row(g[0]), row(g[1]), row(g[2])))
    # Acid: accent over its line, plain steps under it, slide glides
    R("ftSqClose();selT=%s" % json.dumps(ACID)); R("SCA.find(a=>a.id==='clip.newSteps').run()"); pg.wait_for_timeout(150); CA = J(R, "selC")
    R("(()=>{const c=findClip(%s).c,st=c.steps,r=st.rows.length-1;pushUndo();st.g[r][0]={ac:1,lv:.6};st.g[r][1]={sl:1};st.g[r][2]={lv:1};st.g[r][3]={};st.g[r][5]={};ftSqGen(c);changed(false)})()" % json.dumps(CA))
    n = J(R, NOTES % json.dumps(CA))
    ok(n[0][3] >= .9 and n[0][5] == 1, 'Acid: an accented step reaches its accent (velocity over 0.88) even at a low level', n[0])
    ok(n[2][3] == .88 and n[3][3] <= .88, 'Acid: a plain step at full level stays under the accent line', [n[2][3], n[3][3]])
    ok(n[1][1] + n[1][2] > n[2][1] and n[1][6] == 1, 'the slide step holds into the next one', n[1])
    R("window.GL=[];window.GR=[];window._pvS=pvPlay;pvPlay=function(c,I,ch){const r=_pvS.apply(this,arguments);try{const st=pvState(c,ch.triv?ch.dest:ch.in),q=st.nb&&st.nb[st.nb.length-1];if(q)GL.push([q[0],q[2],q[6]])}catch(e){}return r};window._erp=AudioParam.prototype.exponentialRampToValueAtTime;AudioParam.prototype.exponentialRampToValueAtTime=function(v,t){if(Math.abs(v-110)<.01)GR.push(t);return _erp.apply(this,arguments)};0")
    rhash(pg, 0, 2, ACID); gl = J(R, "GL.sort((a,b)=>a[0]-b[0])"); gr = J(R, "GR.sort((a,b)=>a-b)")
    spb = 60 / 145
    if gl: ok(len(gl) >= 5 and gl[2][2] > 0 and all(q[2] == 0 for q in gl[:2] + gl[3:5]), 'rendered (voice engine): Acid glides into the note after the slide and only there', gl[:5])
    else: ok(len(gr) == 1 and abs(gr[0] - (0.5 * spb + J(R, "S.tracks[2].inst.slide"))) < .002, 'rendered: Acid glides into the note after the slide and only there', gr)
    R("pvPlay=_pvS;AudioParam.prototype.exponentialRampToValueAtTime=_erp;0")
    # to a normal MIDI clip and back, exactly
    R("(()=>{const c=findClip(%s).c;pushUndo();c.steps.g[c.steps.rows.length-1][5].ch=.5;ftSqGen(c);changed(false)})()" % json.dumps(CA))
    before = J(R, "JSON.stringify(findClip(%s).c.notes)" % json.dumps(CA)); stb = J(R, "JSON.stringify(findClip(%s).c.steps.g)" % json.dumps(CA))
    R("(()=>{const f=findClip(%s);clipMenu(500,300,f.t,f.c)})()" % json.dumps(CA)); pg.wait_for_timeout(120); L = menu_labels(R)
    ok(any(l.startswith('Make normal MIDI clip') for l in L) and J(R, "[...document.querySelectorAll('#ctxm button')].some(b=>/Make normal MIDI clip/.test(b.textContent)&&b.title.length>20)"), 'clip menu of a step clip: Make normal MIDI clip, with a tooltip')
    u0 = J(R, "UNDO.length"); menu_click(R, 'Make normal MIDI clip'); pg.wait_for_timeout(120)
    c = J(R, "(()=>{const c=findClip(%s).c;return{steps:!!c.steps,nch:c.nch,same:JSON.stringify(c.notes)===%s,ed:FTSQ.id}})()" % (json.dumps(CA), json.dumps(before)))
    ok(not c['steps'] and c['same'] and c['nch'] == 1 and c['ed'] is None and J(R, "UNDO.length") - u0 == 1, 'normal MIDI clip: the steps go, the notes stay the same, chance is kept, the editor closes, one undo step', c)
    k = J(R, "(()=>{const c=findClip(%s).c;let n=0;for(let i=0;i<400;i++){FTSQ.memo.clear();n+=ccSus(c,c.notes).length}return n/400})()" % json.dumps(CA))
    ok(4.3 < k < 4.7, 'a converted clip still rolls its notes’ chance', k)
    R("(()=>{const f=findClip(%s);clipMenu(500,300,f.t,f.c)})()" % json.dumps(CA)); pg.wait_for_timeout(120); L = menu_labels(R)
    ok(any(l.startswith('Make step sequencer clip') for l in L) and not any(l.startswith('Edit steps') for l in L), 'clip menu of a MIDI clip: Make step sequencer clip')
    menu_click(R, 'Make step sequencer clip'); pg.wait_for_timeout(150)
    ok(J(R, "JSON.stringify(findClip(%s).c.steps.g)" % json.dumps(CA)) == stb and J(R, "JSON.stringify(findClip(%s).c.notes)" % json.dumps(CA)) == before and J(R, "FTSQ.id") == CA and J(R, "!findClip(%s).c.nch" % json.dumps(CA)), 'and back: the same steps and notes, the editor opens')
    R("undo()"); ok(J(R, "!findClip(%s).c.steps" % json.dumps(CA)), 'undo: a normal clip again')
    R("ftSqClose()")
    # reading notes: a plain clip with ratchets, slides, accents, levels and chance on 1/16 comes back identical
    R("selT=%s" % json.dumps(SAW)); R("SCA.find(a=>a.id==='clip.newSteps').run()"); pg.wait_for_timeout(120); CS = J(R, "selC")
    R("(()=>{const c=findClip(%s).c,st=c.steps;pushUndo();st.g[7][0]={ac:1};st.g[4][2]={rt:3};st.g[3][4]={sl:1};st.g[2][5]={lv:.4};st.g[0][9]={ch:.5};st.g[7][12]={rt:2,lv:.9};st.g[5][14]={};ftSqGen(c);changed(false)})()" % json.dumps(CS))
    ref = J(R, "JSON.stringify(findClip(%s).c.notes)" % json.dumps(CS)); gref = J(R, "JSON.stringify(findClip(%s).c.steps.g)" % json.dumps(CS))
    R("(()=>{const c=findClip(%s).c;pushUndo();delete c.steps;delete c.stepsOld;c.notes=c.notes.map(n=>Object.assign({},n));changed(false);ftSqClose()})()" % json.dumps(CS))
    R("selC=%s" % json.dumps(CS)); u0 = J(R, "UNDO.length"); R("SCA.find(a=>a.id==='clip.toSteps').run()"); pg.wait_for_timeout(120)
    lr = J(R, "FTSQ.lastRead")
    ok(lr['moved'] == 0 and lr['len'] == 0 and J(R, "JSON.stringify(findClip(%s).c.notes)" % json.dumps(CS)) == ref, 'read from notes: ratchets, slide, accent, level and chance come back as the same notes', lr)
    gnew = J(R, "JSON.stringify(findClip(%s).c.steps.g)" % json.dumps(CS)); ok(json.loads(gnew) == json.loads(gref) and J(R, "findClip(%s).c.steps.res" % json.dumps(CS)) == .25 and J(R, "UNDO.length") - u0 == 1, 'and as the same steps (1/16, one undo step)', (gnew == gref, [(a,b) for a,b in zip(json.loads(gnew),json.loads(gref)) if a!=b], J(R, "UNDO.length") - u0))
    # off the grid, 1/8 and 1/32
    R("(()=>{const t=S.tracks[4];t.clips.push(mkClip({start:8,len:4,name:'p8',notes:[{p:45,s:0,l:.4,v:.8},{p:48,s:.5,l:.4,v:.8},{p:45,s:1.5,l:.4,v:.8}]}),mkClip({start:16,len:2,name:'p32',notes:[{p:45,s:0,l:.1,v:.8},{p:45,s:.125,l:.1,v:.8},{p:45,s:.375,l:.1,v:.8}]}),mkClip({start:24,len:4,name:'off',notes:[{p:45,s:0,l:.2,v:.8},{p:45,s:1.1,l:.2,v:.8}]}),mkClip({start:32,len:4,name:'chrom',notes:[{p:60,s:0,l:.2,v:.8},{p:61,s:.25,l:.2,v:.8},{p:62,s:.5,l:.2,v:.8}]}),mkClip({start:40,len:4,name:'many',notes:Array.from({length:20},(_,i)=>({p:40+i,s:i*.125,l:.1,v:.8}))}));changed(false)})()")
    ids = J(R, "S.tracks[4].clips.map(c=>c.id)")
    for cid in ids: R("FT_HOOKS.stepConvert.toSteps(%s)" % json.dumps(cid)); pg.wait_for_timeout(30)
    s8, s32, off, chrom = [J(R, "(()=>{const c=findClip(%s).c;return c.steps?{res:c.steps.res,n:c.steps.n,cust:c.steps.cust||0,rows:c.steps.rows.map(r=>r.p),notes:c.notes.map(n=>[n.p,n.s])}:null})()" % json.dumps(i)) for i in ids[:4]]
    ok(s8['res'] == .25 and s8['n'] == 16 and s8['notes'] == [[45, 0], [48, .5], [45, 1.5]], 'notes on 8ths: the 16th grid (it fits), the same notes', s8)
    ok(s32['res'] == .125 and s32['notes'] == [[45, 0], [45, .125], [45, .375]], 'notes on 32nds: 1/32 steps', s32)
    ok(off['notes'] == [[45, 0], [45, 1]], 'a note off the grid moves to the nearest step', off['notes'])
    ok(chrom['cust'] == 1 and chrom['rows'] == [62, 61, 60], 'notes outside the key: the rows are the clip’s own notes', chrom['rows'])
    ok(J(R, "!findClip(%s).c.steps" % json.dumps(ids[4])), 'more than 16 different notes: refused, the clip stays as it was')
    R("ftSqOpen(%s)" % json.dumps(ids[3])); R("FTSQ.el.querySelector('[data-a=ou]').click()"); ok(J(R, "findClip(%s).c.steps.rows.map(r=>r.p)" % json.dumps(ids[3])) == [74, 73, 72] and J(R, "FTSQ.el.querySelector('.ftsqk').textContent") == 'Notes of the clip', 'Oct + moves the clip’s own rows; the editor says "Notes of the clip"')
    pg.screenshot(path=os.path.join(OUT, 'f9b_custom.png'))
    R("ftSqClose()")
    # Push 1's drum lane on a step clip
    R("FAKEMIDI.plug('Ableton Push','Ableton')"); pg.wait_for_timeout(300)
    R("(()=>{const t=S.tracks[0];t.inst.psel=S.tracks[0].clips.length?ensurePads(t.inst).findIndex(p=>p.type==='kick'):0;selectTrack(t.id);pos=findClip(%s).c.start})()" % json.dumps(CK)); pg.wait_for_timeout(200)
    L0 = J(R, "p1bLane(curT()).on"); ok([i for i, x in enumerate(L0) if x] == [0, 4, 8, 12], 'Push 1 drum lane: shows the step clip’s kick steps', L0)
    u0 = J(R, "UNDO.length"); msg(R, [0x90, 92 + 2, 100], [0x80, 92 + 2, 0]); pg.wait_for_timeout(60)
    kr = J(R, "(()=>{const c=findClip(%s).c,t=S.tracks[0];return c.steps.rows.findIndex(r=>r.p===36+(t.inst.psel|0))})()" % json.dumps(CK))
    ok(J(R, "!!findClip(%s).c.steps.g[%d][2]" % (json.dumps(CK), kr)) and J(R, "findClip(%s).c.notes.some(n=>n.s===.5&&n.p===36+(S.tracks[0].inst.psel|0))" % json.dumps(CK)) and J(R, "UNDO.length") - u0 == 1, 'pressing lane step 3 turns that step of the pattern on (and its note), one undo step')
    ok(J(R, "S.tracks[0].clips.length") == 1, 'no new clip made over the step clip')
    led = J(R, "[...CTL.devs.values()][0].p1.led.get(94)"); ok(led == J(R, "p1Col(curT().color)"), 'its pad lights in the track colour', led)
    msg(R, [0xB0, 118, 127], [0x90, 36 + J(R, "curT().inst.psel|0") % 4 + 8 * (J(R, "curT().inst.psel|0") // 4), 100], [0x80, 36, 0], [0xB0, 118, 0]); pg.wait_for_timeout(60)
    ok(not any(J(R, "p1bLane(curT()).on")), 'Delete held + pad: clears that row of the pattern')
    R("undo()"); ok(sum(J(R, "p1bLane(curT()).on")) == 5, 'undo brings it back')
    # linked copies follow the conversion
    R("(()=>{const f=findClip(%s);lkDup(f.t,f.c)})()" % json.dumps(CS)); CL = J(R, "selC")
    R("FT_HOOKS.stepConvert.toNotes(%s);lkSweep()" % json.dumps(CS)); pg.wait_for_timeout(300)
    ok(J(R, "!findClip(%s).c.steps&&!findClip(%s).c.steps" % (json.dumps(CS), json.dumps(CL))), 'a linked copy becomes a normal clip too')
    # saved and loaded
    j = J(R, "(()=>{const P=JSON.parse(JSON.stringify(S));return P.tracks.flatMap(t=>t.clips).filter(c=>c.stepsOld).length})()"); ok(j >= 2, 'the kept steps are saved with the song', j)
    ok(not any('—' in x for x in J(R, "Object.values(FTSQ_TIP).concat(FTSQP.key.flat(),FTSQP.drums.flat())")), 'no em dash in the new text')
    ok(J(R, "FTSQ.raf===0&&FTSQ.iv===0"), 'idle: no timer, no animation frame')
    ok(not logs, 'no console errors', logs[:3])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL))); sys.exit(1 if FAIL else 0)
