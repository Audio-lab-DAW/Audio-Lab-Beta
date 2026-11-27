#!/usr/bin/env python3
"""Task FT-F9a (step sequencer clips, part 1): the Fractals song's Kick and Bass clips linked, an edit changes every copy in one undo step, envelopes in
content time and a resize that is not an edit, Make unique, Duplicate as linked copy (menu and command), Alt+Shift-drag linked and
Shift-drag plain copies, audio clip gain, a link left alone is dropped, the file stays small, older projects untouched.
   python3 tools/ui-tests/taskFT_F1.py [index.html] [out dir]"""
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
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
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
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 269), 'version 0.269 or later', v)
    ok(J(R, "['clip.newSteps','clip.editSteps'].every(i=>SCA.some(a=>a.id===i))"), 'commands clip.newSteps and clip.editSteps in the registry')
    ok(J(R, "typeof FT_HOOKS.stepClip==='function'&&typeof FT_HOOKS.stepEditor.open==='function'"), 'hooks FT_HOOKS.stepClip and FT_HOOKS.stepEditor')
    ok(J(R, "S.tracks.every(t=>t.clips.every(c=>!c.steps))"), 'Fractals has no step clips (older songs untouched)')
    F0 = J(R, "S.tracks.flatMap(t=>t.clips.filter(c=>c.notes).slice(0,3).map(c=>c.id))")
    ok(all(J(R, "ccSus(findClip(%s).c,findClip(%s).c.notes)===findClip(%s).c.notes" % ((json.dumps(i),) * 3)) for i in F0[:6]), 'ordinary clips: the chance step leaves the notes untouched (same array)')
    # a fresh song: a drum kit and a saw
    R("AudioLab.build({bpm:120,tracks:[{name:'Kit',preset:'drums'},{name:'Saw',preset:'saw'},{name:'Saw copy',preset:'saw'}]})"); pg.wait_for_timeout(500)
    KIT, SAW, SAW2 = J(R, "S.tracks.map(t=>t.id)")
    # the track menu
    R("(()=>{const t=S.tracks[0];trackMenu(400,300,t,0)})()"); pg.wait_for_timeout(120); L = menu_labels(R)
    ok(any(l.startswith('Add step sequencer clip here') for l in L), 'track menu: Add step sequencer clip here', [l for l in L if 'clip' in l])
    ok(J(R, "[...document.querySelectorAll('#ctxm button')].some(b=>/Add step sequencer/.test(b.textContent)&&b.title.length>20)"), 'the entry has a tooltip')
    u0 = J(R, "UNDO.length"); menu_click(R, 'Add step sequencer clip here'); pg.wait_for_timeout(200)
    ok(J(R, "UNDO.length") - u0 == 1, 'adding it is one undo step')
    C = J(R, "selC"); st = J(R, "findClip(selC).c.steps")
    ok(st['n'] == 16 and st['res'] == .25 and st['mode'] == 'drums' and len(st['rows']) == 16 and st['rows'][0]['p'] == 36, 'a 16-step clip of 1/16 over the 16 drum pads', [st['n'], st['res'], st['mode'], len(st['rows'])])
    ok(J(R, "findClip(selC).c.len") == 4 and J(R, "findClip(selC).c.name") == 'Steps', 'one bar long, named Steps')
    ok(J(R, "!FTSQ.el.hidden&&FTSQ.id===selC"), 'the step editor opens')
    names = J(R, "findClip(selC).c.steps.rows.map(r=>r.nm)"); ok(names[0] == J(R, "ensurePads(S.tracks[0].inst)[0].name"), 'rows named by the pads', names[:4])
    # the real mouse: kick on 1, 5, 9, 13
    for i in (0, 4, 8, 12):
        x, y = cell_xy(R, 0, i); pg.mouse.click(x, y); pg.wait_for_timeout(30)
    n = J(R, NOTES % json.dumps(C)); ok([q[:4] for q in n] == [[36, s, .125, .75] for s in (0, 1, 2, 3)], 'mouse: four kicks on steps 1, 5, 9 and 13 write four notes', n)
    ok(J(R, "UNDO.length") - u0 == 5, 'one undo step per click', J(R, "UNDO.length") - u0)
    # drag paint on row 3
    x0, y0 = cell_xy(R, 2, 0); x1, _ = cell_xy(R, 2, 7); pg.mouse.move(x0, y0); pg.mouse.down(); pg.mouse.move(x1, y0, steps=10); pg.mouse.up(); pg.wait_for_timeout(50)
    ok(J(R, "findClip(selC).c.steps.g[2].slice(0,8).every(Boolean)&&!findClip(selC).c.steps.g[2][8]"), 'drag paints steps 1 to 8 of row 3')
    ok(J(R, "UNDO.length") - u0 == 6, 'the whole drag is one undo step')
    R("undo()"); ok(J(R, "findClip(%s).c.steps.g[2].every(x=>!x)" % json.dumps(C)) and J(R, "FTSQ.el.hidden===false"), 'undo takes the painted row back, the editor stays open and follows')
    # lanes of row 1 (the kick): accent on step 1, ratchet on step 5, chance on step 9, level on step 13
    x, y = cell_xy(R, 0, 0); pg.mouse.click(FTSQ_X := J(R, "FTSQ.cv.getBoundingClientRect().left") + 20, y)  # row label: select row 1
    x, y = cell_xy(R, 0, 0, lane=1); pg.mouse.click(x, y)
    x, y = cell_xy(R, 0, 4, lane=4); pg.mouse.click(x, y)
    x, y = cell_xy(R, 0, 8, lane=3); pg.mouse.move(x, y - 7); pg.mouse.down(); pg.mouse.move(x, y + 1, steps=3); pg.mouse.up()
    x, y = cell_xy(R, 0, 12, lane=0); pg.mouse.move(x, y - 8); pg.mouse.down(); pg.mouse.up()
    g0 = J(R, "findClip(%s).c.steps.g[0].slice(0,13)" % json.dumps(C))
    ok(g0[0].get('ac') == 1 and g0[4].get('rt') == 2 and 0 < g0[8].get('ch', 1) < 1 and g0[12].get('lv', .75) > .75, 'mouse in the lanes: accent on 1, ratchet 2 on 5, chance on 9, level up on 13', [g0[0], g0[4], g0[8], g0[12]])
    n = J(R, NOTES % json.dumps(C))
    ok(n[0][3] == 1 and n[0][5] == 1, 'accent: the step plays at full level', n[0])
    rat = [q for q in n if 1 <= q[1] < 1.25]; ok(len(rat) == 2 and abs(rat[1][1] - 1.125) < 1e-9 and abs(rat[0][2] - .1) < 1e-9, 'ratchet 2: two hits in the step', rat)
    ch = [q for q in n if q[1] == 2]; ok(ch and ch[0][4] < 1, 'chance stored on the note', ch)
    pg.screenshot(path=os.path.join(OUT, 'f9a_drums.png'))
    # chance while playing: rolled each time, the hits of a ratchet share the roll
    R("(()=>{const c=findClip(%s).c;const st=c.steps;st.g[0][4].ch=.5;ftSqGen(c);changed(false)})()" % json.dumps(C))
    res = J(R, "(()=>{const c=findClip(%s).c;let k=0,kr=0,split=0;for(let i=0;i<2000;i++){FTSQ.memo.clear();const r=ccSus(c,c.notes);const a=r.filter(n=>n.s===2).length,b=r.filter(n=>n.s>=1&&n.s<1.25).length;k+=a;kr+=b?1:0;if(b===1)split++}return[k/2000,kr/2000,split,ccSus(c,c.notes).filter(n=>n.ch==null).length]})()" % json.dumps(C))
    ok(abs(res[0] - J(R, "findClip(%s).c.steps.g[0][8].ch" % json.dumps(C))) < .06 and abs(res[1] - .5) < .06 and res[2] == 0 and res[3] == 2, 'chance: each roll plays the step about as often as set; both ratchet hits always together; steps without chance always play', res)
    # the render of a step clip equals the render of a plain clip with the same notes (Saw, notes in key)
    R("selT=%s;" % json.dumps(SAW)); R("SCA.find(a=>a.id==='clip.newSteps').run()"); pg.wait_for_timeout(150); C2 = J(R, "selC")
    st = J(R, "findClip(selC).c.steps"); ok(st['mode'] == 'key' and [r['p'] for r in st['rows']] == [57, 55, 53, 52, 50, 48, 47, 45], 'on a synth: 8 notes of A minor from A3 (the command clip.newSteps)', [r['nm'] for r in st['rows']])
    for row, i in ((7, 0), (4, 3), (3, 6), (0, 8), (2, 12)):
        x, y = cell_xy(R, row, i); pg.mouse.click(x, y)
    x, y = cell_xy(R, 4, 3); R("FTSQ.row=4;ftSqPaint()"); x, y = cell_xy(R, 4, 3, lane=2); pg.mouse.click(x, y)
    pg.screenshot(path=os.path.join(OUT, 'f9a_key.png'))
    n2 = J(R, NOTES % json.dumps(C2)); ok(len(n2) == 5 and n2[0][:2] == [45, 0] and any(q[6] == 1 and abs(q[2] - .2625) < 1e-9 for q in n2), 'five notes; slide holds into the next step', n2)
    R("(()=>{const c=findClip(%s).c,t=S.tracks[2];t.clips.push(mkClip({start:c.start,len:c.len,name:'plain',notes:c.notes.map(n=>({p:n.p,s:n.s,l:n.l,v:n.v}))}));changed(false)})()" % json.dumps(C2))
    hA = rhash(pg, 0, 5, SAW); hB = rhash(pg, 0, 5, SAW2); ok(hA == hB, 'the step clip renders bit-identical to a plain clip with the same notes', (hA, hB))
    # pattern length and step size
    R("FTSQ.el.querySelector('[data-a=n]').value='32';FTSQ.el.querySelector('[data-a=n]').dispatchEvent(new Event('change',{bubbles:true}))")
    ok(J(R, "findClip(selC).c.len") == 8 and len(J(R, NOTES % json.dumps(C2))) == 10, '32 steps: the clip grows to 2 bars and the pattern repeats into the new steps')
    R("FTSQ.el.querySelector('[data-a=res]').value='0.5';FTSQ.el.querySelector('[data-a=res]').dispatchEvent(new Event('change',{bubbles:true}))")
    ok(J(R, "findClip(selC).c.len") == 16 and J(R, NOTES % json.dumps(C2))[1][1] == 1.5, 'step size 1/8: steps half a beat apart, the clip 4 bars')
    R("undo();undo()")
    R("(()=>{const c=findClip(%s).c;pushUndo();c.len=12;changed(false)})()" % json.dumps(C2))
    ok(max(q[1] for q in J(R, NOTES % json.dumps(C2))) >= 8, 'a step clip made longer keeps repeating its pattern')
    R("undo()")
    # octave and rows
    R("FTSQ.el.querySelector('[data-a=ou]').click()"); ok(J(R, "findClip(selC).c.steps.rows[7].p") == 57 and J(R, NOTES % json.dumps(C2))[0][0] == 57, 'Oct +: the rows and their notes an octave higher')
    R("undo()")
    # piano roll edits: the editor says so; Use the steps writes them again
    R("(()=>{const c=findClip(%s).c;pushUndo();c.notes[0].p+=1;changed(false)})()" % json.dumps(C2))
    ok(J(R, "!FTSQ.el.querySelector('.ftsqw').hidden"), 'notes changed elsewhere: the editor says editing a step replaces them')
    R("FTSQ.el.querySelector('[data-a=re]').click()"); ok(J(R, "FTSQ.el.querySelector('.ftsqw').hidden") and J(R, NOTES % json.dumps(C2))[0][0] == 45, 'Use the steps: the notes come from the steps again')
    # double-click and the clip menu
    R("ftSqClose()"); R("(()=>{const f=findClip(%s);openPR(f.t,f.c)})()" % json.dumps(C2))
    ok(J(R, "!FTSQ.el.hidden&&FTSQ.id===%s&&!PR.open" % json.dumps(C2)), 'opening a step clip (double-click) opens the step editor, not the piano roll')
    R("(()=>{const f=findClip(%s);clipMenu(500,300,f.t,f.c)})()" % json.dumps(C2)); pg.wait_for_timeout(120); L = menu_labels(R)
    ok(any(l.startswith('Edit steps') for l in L) and any(l.startswith('Open in piano roll') for l in L), 'clip menu: Edit steps…, Open in piano roll', [l for l in L if 'steps' in l or 'piano' in l])
    ok(not any('—' in l for l in L), 'no em dash in the menu')
    menu_click(R, 'Open in piano roll'); pg.wait_for_timeout(150); ok(J(R, "PR.open&&PR.cid===%s" % json.dumps(C2)), 'Open in piano roll still opens the piano roll')
    R("closePR()")
    # linked copies share the pattern
    R("(()=>{const f=findClip(%s);lkDup(f.t,f.c)})()" % json.dumps(C2)); C3 = J(R, "selC")
    R("ftSqOpen(%s)" % json.dumps(C2)); x, y = cell_xy(R, 1, 15); pg.mouse.click(x, y); R("lkSweep()"); pg.wait_for_timeout(400)
    ok(J(R, "JSON.stringify(findClip(%s).c.steps.g)===JSON.stringify(findClip(%s).c.steps.g)" % (json.dumps(C2), json.dumps(C3))), 'a linked copy follows the pattern too')
    # the file
    j = J(R, "(()=>{const s=JSON.stringify(S),P=JSON.parse(s);return P.tracks[1].clips.filter(c=>c.steps).length})()"); ok(j >= 2, 'the steps are saved with the song', j)
    # idle: nothing per frame
    ok(J(R, "FTSQ.raf===0"), 'not playing: no animation frame')
    R("start()"); pg.wait_for_timeout(700); ok(J(R, "FTSQ.raf!==0"), 'playing: the playing step is drawn'); pg.screenshot(path=os.path.join(OUT, 'f9a_playing.png'))
    R("stop()"); pg.wait_for_timeout(400); ok(J(R, "FTSQ.raf===0"), 'stopped: no animation frame again')
    txt = J(R, "FTSQ.el.innerText+[...FTSQ.el.querySelectorAll('[title]')].map(e=>e.title).join(' ')"); ok('—' not in txt, 'no em dash in the editor')
    ok(J(R, "[...FTSQ.el.querySelectorAll('button,select')].every(e=>(e.title||e.closest('label')&&e.closest('label').title))"), 'every control of the editor has a tooltip')
    R("pmSetOn(true)"); pg.wait_for_timeout(800); pg.screenshot(path=os.path.join(OUT, 'f9a_light.png')); R("pmSetOn(false)")
    R("ftSqClose()"); ok(J(R, "FTSQ.iv===0&&FTSQ.raf===0"), 'closed: no timer left')
    ok(not logs, 'no console errors', logs[:3])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL))); sys.exit(1 if FAIL else 0)
