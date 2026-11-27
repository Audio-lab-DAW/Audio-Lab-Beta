#!/usr/bin/env python3
"""Task FT-F2 (arranger moves): the Fractals song's Kick and Bass clips linked, an edit changes every copy in one undo step, envelopes in
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
def notes(R, cid): return J(R, "findClip(%s).c.notes.map(n=>[n.s,n.p,n.l,n.v])" % json.dumps(cid))
def menu_click(R, pg, label):
    return R("(()=>{const b=[...document.querySelectorAll('#ctxm button')].find(b=>b.textContent.trim().startsWith(%s));if(!b)return 'none';b.click();return 'ok'})()" % json.dumps(label))
TR = []
def rhash(pg, b0, b1):
    m = hashlib.md5()
    for tid in TR:  # each track alone (as tools/engine-tests/export_same.py does): several tracks together differ from render to render
        h = pg.evaluate("o=>AudioLab.render(o)", {'b0': b0, 'b1': b1, 'sr': 44100, 'only': tid})
        for ch in range(h['ch']):
            for off in range(0, h['len'], 1 << 18):
                n = min(1 << 18, h['len'] - off)
                m.update(base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])", [h['id'], ch, off, n])))
        pg.evaluate("i=>AudioLab.free(i)", h['id'])
    return m.hexdigest()[:12]
PLACES = "S.tracks.map(t=>t.clips.map(c=>[+c.start.toFixed(4),+c.len.toFixed(4),+(c.off||0).toFixed(4)]).sort((a,b)=>a[0]-b[0]||a[1]-b[1]))"
SEC = "(S.sections||[]).slice().sort((a,b)=>a.start-b.start).map(s=>[s.name,s.start,s.len])"
CANON = "JSON.stringify({p:%s,s:%s,t:S.tempo||null,bpm:S.bpm,g:S.sigs||null,a:S.pauto||null,l:S.loopRange||null,n:S.tracks.map(t=>t.clips.map(c=>(c.notes||[]).length+':'+c.id))})" % (PLACES, SEC)
HAND_CUT = "pushUndo();for(const t of S.tracks){for(const b of %s)cutAt(t,b)}"
names = lambda R: [x[0] for x in J(R, SEC)]
GRID = "(n=>({t:Array.from({length:n},(_,i)=>bpmAt(i+.5)),a:Array.from({length:n},(_,i)=>envAt(S.pauto['test:a'],i+.5,.5)),s:Array.from({length:n},(_,i)=>{const g=sigAt(i+.5);return g.n+'/'+g.d})}))(%d)"
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 262), 'version 0.262 or later', v)
    sec0 = J(R, SEC); N0 = names(R); k = N0.index('Breakdown'); s, L = sec0[k][1:]; nx = sec0[k + 1]; dst = nx[1] + nx[2]; END = sec0[-1][1] + sec0[-1][2]
    ok(len(sec0) >= 5 and L > 0, 'Fractals: sections, the Breakdown at %g for %g beats, then %s' % (s, L, nx[0]), sec0[k:k + 3])
    BD = J(R, "S.sections.find(s=>s.name==='Breakdown').id")
    ok(J(R, "['arr.secDup','arr.insertBars','arr.secDelete'].every(i=>SCA.some(a=>a.id===i))"), 'three commands in the registry: arr.secDup, arr.insertBars, arr.secDelete')
    ok(J(R, "typeof FT_HOOKS.arrangerMoves.move==='function'"), 'hook FT_HOOKS.arrangerMoves')
    TR[:] = J(R, "S.tracks.filter(t=>['Kick','Lead','Acid'].includes(t.name)).map(t=>t.id)")
    W0, W1 = s - 8, dst + 8
    h0 = rhash(pg, W0, W1); h0b = rhash(pg, W0, W1); ok(h0 == h0b, 'the render (Kick, Lead, Acid, each alone) is repeatable', h0)
    S0 = R(CANON)
    # 1. move: the Breakdown after the next section, against the same cuts and moves by hand
    u0 = J(R, "UNDO.length"); ok(J(R, "FT_HOOKS.arrangerMoves.move(%s,%g)" % (json.dumps(BD), dst)), 'move the Breakdown to after %s' % nx[0])
    ok(J(R, "UNDO.length") - u0 == 1, 'one undo step')
    sc = J(R, SEC); N1 = names(R)
    ok(N1[k] == nx[0] and N1[k + 1] == 'Breakdown' and sc[k + 1][1] == s + nx[2] and N1[k + 2:] == N0[k + 2:], 'sections: %s now before the Breakdown, which starts at %g' % (nx[0], s + nx[2]), sc[k:k + 3])
    pA = J(R, PLACES); hA = rhash(pg, W0, W1)
    R("undo()"); ok(R(CANON) == S0, 'undo gives back the song exactly')
    R(HAND_CUT % json.dumps([s, s + L, dst]) + ";for(const t of S.tracks)for(const c of t.clips){if(c.start>=%g-1e-6&&c.start<%g-1e-6)c.start+=%g;else if(c.start>=%g-1e-6&&c.start<%g-1e-6)c.start-=%g}changed(false)" % (s, s + L, nx[2], s + L, dst, L))
    pB = J(R, PLACES); hB = rhash(pg, W0, W1)
    ok(pA == pB, 'every clip lands where the same cuts and moves by hand put it')
    ok(hA == hB and hA != h0, 'the render is bit-identical to the same edit by hand (and differs from the original)', (hA, hB, h0))
    R("undo()"); ok(R(CANON) == S0, 'back to the original')
    # 2. copy: the Breakdown copied after the next section
    ok(J(R, "FT_HOOKS.arrangerMoves.copy(%s,%g)" % (json.dumps(BD), dst)), 'copy the Breakdown to after %s' % nx[0])
    sc = J(R, SEC); N2 = names(R)
    ok(N2[:k + 2] == N0[:k + 2] and N2[k + 2] == 'Breakdown' and sc[k + 2][1:] == [dst, L] and N2[k + 3:] == N0[k + 2:] and sc[-1][1] == sec0[-1][1] + L, 'the copy is a new Breakdown at %g, everything after moved %g later' % (dst, L), sc[k:k + 4])
    ok(len(set(J(R, "S.sections.map(s=>s.id)"))) == len(sec0) + 1, 'the copied section has its own id')
    W2, W3 = dst - 8, dst + L + 8
    pA = J(R, PLACES); hA = rhash(pg, W2, W3); R("undo()")
    R(HAND_CUT % json.dumps([s, s + L, dst]) + ";for(const t of S.tracks){const add=[];for(const c of t.clips){if(c.start>=%g-1e-6)c.start+=%g;else if(c.start>=%g-1e-6&&c.start<%g-1e-6){const k=JSON.parse(JSON.stringify(c));k.id=rid();k.start=c.start-%g+%g;add.push(k)}}t.clips.push(...add)}changed(false)" % (dst, L, s, s + L, s, dst))
    pB = J(R, PLACES); hB = rhash(pg, W2, W3); R("undo()")
    ok(pA == pB and hA == hB, 'copy: the same clips and a bit-identical render as the same copy by hand', (hA, hB))
    ok(R(CANON) == S0, 'undo after the copy: the song exactly as it was')
    lk = J(R, "(()=>{const f=S.tracks.find(t=>t.name==='Kick');return f.clips.filter(c=>c.link&&c.start>=%g&&c.start<%g).length})()" % (s, s + L))
    # 3. automation, tempo and signature changes go with the music
    R("pushUndo();S.tempo=[{b:%g,bpm:150,ramp:false},{b:%g,bpm:145,ramp:false},{b:%g,bpm:140,ramp:true},{b:%g,bpm:150,ramp:false}];S.tempoV=(S.tempoV||0)+1;S.sigs=[{b:%g,n:2,d:4},{b:%g,n:4,d:4}];S.sigV=(S.sigV||0)+1;S.pauto=S.pauto||{};S.pauto['test:a']=[{b:0,v:.2},{b:%g,v:.9},{b:%g,v:.4},{b:%g,v:1}];changed(false)" % (s, s + L, s + L + 8, dst, s, s + L, s + 16, s + L + 16, dst + 16))
    n = int(END + 2 * L + 8); OLD = J(R, GRID % n); S1 = R(CANON)
    R("FT_HOOKS.arrangerMoves.move(%s,%g)" % (json.dumps(BD), dst))
    mp = lambda x: x + nx[2] if s <= x < s + L else (x - L if s + L <= x < dst else x)
    NEW = J(R, GRID % n)
    bad = [i for i in range(n) if abs(NEW['t'][int(mp(i + .5))] - OLD['t'][i]) > 1e-6]
    ok(not bad, 'move: the tempo of every beat went with its music (step and glide)', bad[:5])
    bad = [i for i in range(n) if abs(NEW['a'][int(mp(i + .5))] - OLD['a'][i]) > 1e-5]
    ok(not bad, 'move: the automation of every beat went with its music', bad[:5])
    bad = [i for i in range(n) if NEW['s'][int(mp(i + .5))] != OLD['s'][i]]
    ok(not bad and NEW['s'][int(s + nx[2] + 1)] == '2/4', 'move: the 2/4 bars went with the Breakdown', bad[:5])
    ok(J(R, "S.pauto['test:a'].length") <= 10, 'only a few edge points added to the automation', J(R, "S.pauto['test:a']"))
    R("undo()"); ok(R(CANON) == S1, 'undo: tempo, signatures and automation back')
    R("FT_HOOKS.arrangerMoves.copy(%s,%g)" % (json.dumps(BD), dst)); NEW = J(R, GRID % (n + L))
    ok(all(abs(NEW['t'][int(i - s + dst)] - OLD['t'][i]) < 1e-6 and abs(NEW['a'][int(i - s + dst)] - OLD['a'][i]) < 1e-5 and NEW['s'][int(i - s + dst)] == OLD['s'][i] for i in range(int(s), int(s + L))), 'copy: the copy has the tempo, signature and automation of the original')
    ok(all(abs(NEW['t'][int(i + L)] - OLD['t'][i]) < 1e-6 and abs(NEW['a'][int(i + L)] - OLD['a'][i]) < 1e-5 for i in range(int(dst), n)) and all(abs(NEW['t'][i] - OLD['t'][i]) < 1e-6 and abs(NEW['a'][i] - OLD['a'][i]) < 1e-5 for i in range(0, int(dst))), 'copy: what is before stays, what is after moved later with its tempo and automation')
    R("undo()")
    # 4. insert empty bars, delete and close the gap
    b2 = sec0[1][1]; R("FT_HOOKS.arrangerMoves.insert(%g,16)" % b2); sc = J(R, SEC)
    ok(sc[0][1:] == sec0[0][1:] and all(sc[i][1] == sec0[i][1] + 16 for i in range(1, len(sc))), 'insert 4 empty bars at the start of %s: every later section 16 beats later' % sec0[1][0])
    ok(J(R, "S.tracks.every(t=>t.clips.every(c=>c.start+c.len<=%g+.01||c.start>=%g-1e-6))" % (b2, b2 + 16)), 'nothing plays in the inserted bars')
    NEW = J(R, GRID % (n + 16)); ok(all(abs(NEW['t'][i + 16] - OLD['t'][i]) < 1e-6 and abs(NEW['a'][i + 16] - OLD['a'][i]) < 1e-5 for i in range(int(b2), n)), 'insert: the tempo and automation moved later too')
    R("undo()"); R("FT_HOOKS.arrangerMoves.del(%s)" % json.dumps(BD)); sc = J(R, SEC)
    ok(names(R) == N0[:k] + N0[k + 1:] and sc[k][1] == s, 'delete the Breakdown and close the gap: %s starts at %g' % (nx[0], s), sc[k - 1:k + 2])
    NEW = J(R, GRID % n); ok(all(abs(NEW['t'][int(i - L)] - OLD['t'][i]) < 1e-6 and abs(NEW['a'][int(i - L)] - OLD['a'][i]) < 1e-5 for i in range(int(s + L), n)), 'delete: the tempo and automation after it moved up')
    ok(J(R, "S.tracks.every(t=>t.clips.every(c=>Math.abs(c.start+c.len-%g)<1e-6||c.start+c.len<%g||c.start>=%g-1e-6))" % (s, s, s)), 'delete: no clip left inside the removed part')
    R("undo()"); ok(R(CANON) == S1, 'undo after insert and delete: as it was'); R("undo()")
    ok(R(CANON) == S0, 'the song is the original again')
    # 5. linked clips copied stay linked
    R("FT_HOOKS.arrangerMoves.copy(%s,%g)" % (json.dumps(BD), dst))
    lk2 = J(R, "(()=>{const f=S.tracks.find(t=>t.name==='Kick');return f.clips.filter(c=>c.link&&c.start>=%g&&c.start<%g).length})()" % (dst, dst + L))
    ok(lk2 == lk, 'linked Kick clips copied with the section stay linked', (lk, lk2)); R("undo()")
    # 6. the loop of a section follows it
    R("loopSection(S.sections.find(s=>s.name==='Breakdown'))"); R("FT_HOOKS.arrangerMoves.move(%s,%g)" % (json.dumps(BD), dst))
    ok(J(R, "S.loopRange&&[S.loopRange.a,S.loopRange.b]") == [s + nx[2], s + nx[2] + L], 'a looped section keeps its loop where it moved to', J(R, "S.loopRange"))
    R("undo()"); R("S.loopRange=null;S.loop=false;syncTransportUI()")
    # 7. the menus
    R("V.x=%g;V.ppb=Math.max(2,(arr.clientWidth-X0)/%g);clampV();dirty=true" % (max(0, s - 2 * L), 5 * L))
    R("(()=>{const sc=S.sections.find(s=>s.name==='Breakdown');secMenu(700,160,sc.start+1)})()"); pg.wait_for_timeout(200)
    labels = J(R, "[...document.querySelectorAll('#ctxm button')].map(b=>b.textContent.trim())")
    want = ['Duplicate section', 'Insert empty bars before', 'Insert empty bars after', 'Delete section and close the gap', 'Remove the marker only']
    ok(all(any(l.startswith(w) for l in labels) for w in want), 'section menu: Duplicate, Insert before and after, Delete and close the gap, Remove the marker only', [l for l in labels if l])
    ok(not any('—' in x for x in labels), 'no em dash in the menu')
    tips = J(R, "[...document.querySelectorAll('#ctxm button')].filter(b=>/Duplicate section|Insert empty|close the gap|marker only/.test(b.textContent)).map(b=>b.title)")
    ok(len(tips) == 5 and all(t and '—' not in t for t in tips), 'every new entry has a tooltip', tips)
    pg.screenshot(path=os.path.join(OUT, 'f2_menu.png'))
    ok(menu_click(R, pg, 'Duplicate section') == 'ok' and names(R) == N0[:k + 1] + ['Breakdown'] + N0[k + 1:], 'Duplicate section from the menu: a copy right after it')
    R("undo()")
    R("(()=>{const sc=S.sections.find(s=>s.name==='%s');secMenu(700,160,sc.start+1)})()" % nx[0]); pg.wait_for_timeout(100)
    menu_click(R, pg, 'Insert empty bars before'); pg.wait_for_timeout(150)
    bar = int(nx[1] // 4 + 1)
    ok(J(R, "!document.getElementById('dlg').hidden&&document.getElementById('dlgT').textContent.includes('bar %d')" % bar), 'Insert empty bars before %s asks how many, at bar %d' % (nx[0], bar), J(R, "document.getElementById('dlgT').textContent"))
    pg.fill('#dlgI', '2'); pg.press('#dlgI', 'Enter'); pg.wait_for_timeout(200)
    ok(J(R, "S.sections.find(s=>s.name==='%s').start" % nx[0]) == nx[1] + 8, '2 bars inserted: %s starts 8 beats later' % nx[0])
    R("undo()")
    R("secMenu(500,160,%g)" % (END + 40)); pg.wait_for_timeout(100); labels = J(R, "[...document.querySelectorAll('#ctxm button')].map(b=>b.textContent.trim())")
    ok(any(l.startswith('Insert empty bars here') for l in labels), 'the empty strip: Insert empty bars here', [l for l in labels if l])
    R("closeMenu()")
    R("pos=%g;SCA.find(a=>a.id==='arr.secDelete').run()" % (s + 2)); ok(names(R) == N0[:k] + N0[k + 1:], 'command arr.secDelete with the playhead in the Breakdown')
    R("undo()"); R("SCA.find(a=>a.id==='arr.secDup').run()"); ok(len(J(R, SEC)) == len(sec0) + 1, 'command arr.secDup'); R("undo()")
    ok(R(CANON) == S0, 'the song is the original again')
    # 8. the real mouse: drag the Breakdown after the next section; Alt-drag copies
    pg.wait_for_timeout(300)
    def sx(beat): return J(R, "(()=>{const r=arr.getBoundingClientRect(),z=ZOOM;return[r.left+(X0+(%g-V.x)*V.ppb)*z,r.top+(TY+RUL+SECH/2)*z]})()" % beat)
    x0, y0 = sx(s + 6); x1, _ = sx(s + 6 + nx[2]); pg.mouse.move(x0, y0); pg.mouse.down(); pg.mouse.move(x0 + 20, y0, steps=4); pg.mouse.move(x1, y0, steps=12); pg.wait_for_timeout(150)
    pg.screenshot(path=os.path.join(OUT, 'f2_drag.png')); pg.mouse.up(); pg.wait_for_timeout(200)
    ok(names(R) == N1, 'mouse: the Breakdown dragged after %s' % nx[0], names(R)[k - 1:k + 3])
    ok('with its clips' in J(R, "document.getElementById('toast').textContent"), 'the toast says it moved with its clips', J(R, "document.getElementById('toast').textContent"))
    R("undo()"); ok(R(CANON) == S0, 'mouse drag undone in one step')
    pg.keyboard.down('Alt'); pg.mouse.move(x0, y0); pg.mouse.down(); pg.mouse.move(x0 + 20, y0, steps=4); x2, _ = sx(s + 6 + L + nx[2]); pg.mouse.move(x2, y0, steps=12); pg.wait_for_timeout(150)
    pg.screenshot(path=os.path.join(OUT, 'f2_altdrag.png')); pg.mouse.up(); pg.keyboard.up('Alt'); pg.wait_for_timeout(200)
    ok(names(R) == N2, 'mouse: Alt-drag copies the Breakdown after %s' % nx[0], names(R)[k - 1:k + 4])
    R("undo()"); ok(R(CANON) == S0, 'Alt-drag undone in one step')
    # Light mode
    R("document.body.classList.add('light')"); R("(()=>{const sc=S.sections.find(s=>s.name==='Breakdown');secMenu(700,160,sc.start+1)})()"); pg.wait_for_timeout(150)
    pg.screenshot(path=os.path.join(OUT, 'f2_menu_light.png')); R("closeMenu()"); R("document.body.classList.remove('light')")
    ok(not logs, 'no console errors', logs[:3])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL))); sys.exit(1 if FAIL else 0)
