#!/usr/bin/env python3
"""Task FT-F1 (linked clips): the Fractals song's Kick and Bass clips linked, an edit changes every copy in one undo step, envelopes in
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

def notes(R, cid): return J(R, "findClip(%s).c.notes.map(n=>[n.s,n.p,n.l,n.v])" % json.dumps(cid))
def menu_click(R, pg, label):
    return R("(()=>{const b=[...document.querySelectorAll('#ctxm button')].find(b=>b.textContent.trim().startsWith(%s));if(!b)return 'none';b.click();return 'ok'})()" % json.dumps(label))
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 255), 'version 0.255 or later', v)
    L = J(R, "S.tracks.filter(t=>t.clips.length).map(t=>[t.name,t.clips.filter(c=>c.link).length,new Set(t.clips.filter(c=>c.link).map(c=>c.link)).size])")
    d = {x[0]: x[1:] for x in L}
    ok(d['Kick'] == [24, 2] and d['Bass'] == [24, 2], 'Fractals: the repeated Kick and Bass clips are linked (2 groups of 12 each)', (d['Kick'], d['Bass']))
    ok(all(v[0] == 0 for k, v in d.items() if k not in ('Kick', 'Bass')), 'no other track is linked')
    ok(J(R, "(()=>{const t=S.tracks.find(t=>t.name==='Kick'),c=t.clips.find(c=>c.link);return clipSig(t,c).endsWith('|L')})()"), 'a linked clip draws its chain mark (in the clip picture key)')
    # an edit to one changes every copy, one undo step
    g = J(R, "(()=>{const t=S.tracks.find(t=>t.name==='Kick'),c=t.clips.filter(c=>c.link).sort((a,b)=>a.start-b.start)[0];return lkGroup(c.link).map(x=>x.c.id)})()")
    a, bb = g[0], g[-1]; u0 = J(R, "UNDO.length"); n0 = notes(R, bb)
    R("selC=%s;pushUndo();findClip(selC).c.notes.forEach(n=>n.p+=1);changed(false)" % json.dumps(a))
    ok(notes(R, bb) == [[s, p + 1, l, v_] for s, p, l, v_ in n0] and all(notes(R, x) == notes(R, a) for x in g), 'an edit to one Kick clip changes all 12 copies at once', len(g))
    ok(J(R, "UNDO.length") - u0 == 1, 'one undo step')
    R("undo()"); ok(all(notes(R, x) == n0 for x in g), 'undo puts every copy back')
    R("redo()"); ok(notes(R, bb)[0][1] == n0[0][1] + 1, 'redo: every copy again'); R("undo()")
    # the clip menu: Transpose on a linked clip, the new entries
    R("(()=>{const f=findClip(%s);clipMenu(300,300,f.t,f.c)})()" % json.dumps(a)); pg.wait_for_timeout(100)
    labels = J(R, "[...document.querySelectorAll('#ctxm button')].map(b=>b.textContent.trim())")
    ok(any(x.startswith('Duplicate as linked copy') for x in labels) and any(x.startswith('Make unique') for x in labels) and any(x.startswith('Select linked copies') for x in labels), 'clip menu: Duplicate as linked copy, Make unique, Select linked copies', [x for x in labels if 'ink' in x or 'nique' in x])
    ok(not any('—' in x for x in labels), 'no em dash in the menu')
    pg.screenshot(path=os.path.join(OUT, 'f1_menu.png'))
    ok(menu_click(R, pg, 'Transpose +1 octave') == 'ok' and notes(R, bb)[0][1] == n0[0][1] + 12, 'Transpose +1 octave from the menu: every copy')
    R("undo()")
    R("(()=>{const f=findClip(%s);clipMenu(300,300,f.t,f.c)})()" % json.dumps(a)); menu_click(R, pg, 'Select linked copies')
    ok(J(R, "SELCS.size") == 12, 'Select linked copies selects the 12')
    R("selClear()")
    # envelopes: shared in content time; a left resize is not an edit
    R("(()=>{const f=findClip(%s),c=f.c,sh=4;pushUndo();c.start+=sh;c.off=(c.off||0)+sh;c.len-=sh;for(const k in c.env)c.env[k]=c.env[k].map(q=>({b:q.b-sh,v:q.v})).filter(q=>q.b>=0&&q.b<=c.len);selC=c.id;changed(false)})()" % json.dumps(bb))
    e0 = J(R, "findClip(%s).c.env" % json.dumps(a))
    ok(J(R, "findClip(%s).c.env" % json.dumps(a)) == e0 and J(R, "findClip(%s).c.off" % json.dumps(a)) == 0, 'resizing one copy from the left changes no other copy')
    R("(()=>{const c=findClip(%s).c;pushUndo();c.env.vol=c.env.vol||[];c.env.vol.push({b:2,v:.3});c.env.vol.sort((x,y)=>x.b-y.b);selC=c.id;changed(false)})()" % json.dumps(bb))
    ea = J(R, "findClip(%s).c.env.vol" % json.dumps(a))
    ok(ea and any(abs(q['b'] - 6) < 1e-6 and abs(q['v'] - .3) < 1e-6 for q in ea), 'an envelope point at beat 2 of the resized copy shows at beat 6 of the others (content time)', ea)
    nb = notes(R, bb); R("selC=%s;pushUndo();findClip(selC).c.notes[0].v=.5;changed(false)" % json.dumps(bb))
    ok(notes(R, a)[0][3] == .5, 'a note edit on the resized copy reaches the others')
    # Make unique
    R("selC=%s;SCM.get('clip.unique').run()" % json.dumps(bb)); ok(not J(R, "findClip(%s).c.link||null" % json.dumps(bb)), 'Make unique (command): the link is gone')
    va = notes(R, a)[0][3]; R("selC=%s;pushUndo();findClip(selC).c.notes[0].v=.25;changed(false)" % json.dumps(bb)); ok(notes(R, a)[0][3] == va, 'its edits stay its own')
    # Duplicate as linked copy on a plain clip (command), then each follows the other
    lead = J(R, "(()=>{const t=S.tracks.find(t=>t.name==='Lead');return t.clips[0].id})()")
    n_l = J(R, "S.tracks.find(t=>t.name==='Lead').clips.length"); R("selC=%s;SCM.get('clip.linkedDup').run()" % json.dumps(lead))
    cp = J(R, "selC"); ok(J(R, "S.tracks.find(t=>t.name==='Lead').clips.length") == n_l + 1 and cp != lead and J(R, "findClip(%s).c.link===findClip(%s).c.link&&!!findClip(%s).c.link" % (json.dumps(cp), json.dumps(lead), json.dumps(cp))), 'Duplicate as linked copy: a copy after it, both linked')
    R("selC=%s;pushUndo();findClip(selC).c.notes.push({s:.5,p:70,l:.25,v:.8});changed(false)" % json.dumps(cp)); ok(any(n[1] == 70 for n in notes(R, lead)), 'a note added to the copy shows in the original')
    # Alt+Shift-drag linked, Shift-drag plain
    R("(()=>{V.x=60;V.ppb=24;V.y=0;clampV();dirty=true})()"); pg.wait_for_timeout(300)
    pos = lambda cid: J(R, "(()=>{const f=findClip(%s);const i=S.tracks.indexOf(f.t),G=clipGeom(i,f.c),r=arr.getBoundingClientRect();return{x:r.left+G.x,y:r.top+G.y,w:G.w,h:G.h}})()" % json.dumps(cid))
    kc = J(R, "(()=>{const t=S.tracks.find(t=>t.name==='Kick');const c=t.clips.find(c=>c.start>=64&&c.start<80);return c.id})()")
    kl = J(R, "findClip(%s).c.link||null" % json.dumps(kc)); nK = J(R, "S.tracks.find(t=>t.name==='Kick').clips.length")
    P = pos(kc); cx, cy = P['x'] + min(P['w'] / 2, 40), P['y'] + P['h'] * .7
    pg.mouse.click(cx, cy); pg.keyboard.down('Shift'); pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx + 60, cy, steps=5); pg.mouse.move(cx + 24 * 8, cy, steps=8); pg.mouse.up(); pg.keyboard.up('Shift'); pg.wait_for_timeout(200)
    c1 = J(R, "selC"); ok(J(R, "S.tracks.find(t=>t.name==='Kick').clips.length") == nK + 1 and c1 != kc and not J(R, "findClip(%s).c.link||null" % json.dumps(c1)), 'Shift-drag of a linked clip: a plain copy', (kl, c1))
    R("selClear()"); pg.mouse.click(cx, cy); pg.keyboard.down('Alt'); pg.keyboard.down('Shift'); pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx + 60, cy + 1, steps=5); pg.mouse.move(cx + 24 * 16, cy, steps=8); pg.mouse.up(); pg.keyboard.up('Shift'); pg.keyboard.up('Alt'); pg.wait_for_timeout(200)
    c2 = J(R, "selC"); l2 = J(R, "[findClip(%s).c.link||null,findClip(%s).c.link||null]" % (json.dumps(c2), json.dumps(kc)))
    ok(J(R, "S.tracks.find(t=>t.name==='Kick').clips.length") == nK + 2 and c2 not in (kc, c1) and l2[0] and l2[0] == l2[1] and (kl is None or l2[0] == kl), 'Alt+Shift-drag: a linked copy, linked with the original (its group, or a new link)', (c2, kl, l2))
    ok(abs(J(R, "findClip(%s).c.start" % json.dumps(kc)) - J(R, "findClip(%s).c.start" % json.dumps(c2))) > 1, 'the original stays where it was, the copy moved')
    pg.wait_for_timeout(400); pg.screenshot(path=os.path.join(OUT, 'f1_arr.png'))
    pg.screenshot(path=os.path.join(OUT, 'f1_arr_zoom.png'), clip={'x': P['x'] - 40, 'y': P['y'] - 30, 'width': 700, 'height': 200})
    # audio: gain follows, fades stay
    vx = J(R, "(()=>{const t=S.tracks.find(t=>t.kind==='audio');return t.clips[0].id})()"); R("selC=%s;SCM.get('clip.linkedDup').run()" % json.dumps(vx)); vc = J(R, "selC")
    R("(()=>{const c=findClip(%s).c;pushUndo();c.gain=-3;c.fi=1;selC=c.id;changed(false)})()" % json.dumps(vc))
    ok(J(R, "findClip(%s).c.gain" % json.dumps(vx)) == -3 and J(R, "findClip(%s).c.fi||0" % json.dumps(vx)) != 1, 'audio: gain is shared, a fade stays its own')
    # a link left with one clip is dropped
    R("(()=>{const f=findClip(%s);pushUndo();f.t.clips=f.t.clips.filter(c=>c!==f.c);selC=null;changed(false)})()" % json.dumps(vc)); pg.wait_for_timeout(400)
    ok(not J(R, "findClip(%s).c.link||null" % json.dumps(vx)), 'the other copy deleted: the last one is a plain clip again')
    # file size: links add only their ids
    sz = J(R, "(()=>{const a=JSON.stringify(S).length,b=JSON.stringify(S,(k,v)=>k==='link'?undefined:v).length;return[a,b]})()")
    ok(sz[0] - sz[1] < sz[1] * .01, 'the song with links is less than 1 % bigger than without (copies keep their notes for older versions; the file is gzipped)', sz)
    # a song from a file with links (and an older one without) opens and keeps working
    R("window.__P=JSON.stringify(S)"); R("restore(__P)"); g2 = J(R, "lkGroup(findClip(%s).c.link).map(x=>x.c.id)" % json.dumps(a))
    R("selC=%s;pushUndo();findClip(selC).c.notes[1].p+=2;changed(false)" % json.dumps(a)); ok(len(g2) >= 11 and all(notes(R, x) == notes(R, a) for x in g2), 'reloaded song: the links work', (len(g2), [notes(R, x)[1] for x in g2][:4], J(R, "[LK.S===S,LK.base.size,LK.n.prop]")))
    R("restore(JSON.stringify(JSON.parse(__P),(k,v)=>k==='link'?undefined:v))"); ok(J(R, "lkAllLinked().length") == 0 and J(R, "S.tracks.length") > 10, 'a song without links opens as before (no clip linked)')
    R("restore(__P)")
    # idle
    pg.wait_for_timeout(600)
    R("window.__to=[];{const o=setTimeout;window.setTimeout=function(){const s=(new Error().stack||'');if(/lk[A-Z]/.test(s))__to.push(s.slice(0,200));return o.apply(this,arguments)}}"); pg.wait_for_timeout(1500)
    ok(J(R, "__to") == [], 'nothing of the links runs while still', J(R, "__to"))
    ok(not logs, 'no console errors', logs)
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
