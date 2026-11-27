#!/usr/bin/env python3
"""Task FT-C3a (generic controllers and templates). Based on the C2b harness.
Task FT-C2b (v0.239): Ableton Push 1, part 2 (control): encoders on the selected device and on track volume and pan, the two rows of
track buttons, transport, tempo, master, undo, duplicate, delete, quantize, the drum kit's 4x4 pads and 16-step lane, with the fake Push 1.
   python3 tools/ui-tests/taskFT_C2b.py [index.html] [out dir]"""
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



MPK = 'MPK mini 3'
def msg(R, dev, *ms): R(";".join("FAKEMIDI.msg(%s,%s)" % (json.dumps(dev), json.dumps(list(m))) for m in ms))
val = lambda R, id: J(R, "(C=>C?C.spec.n(C.get()):null)(CT.get(%s))" % json.dumps(id))
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 246), 'version 0.246 or later', v)
    R("window.VO=[];{const o=voiceOn;voiceOn=function(t,p,v){VO.push([t.name,p]);return o.apply(this,arguments)}}0")
    R("FAKEMIDI.plug('Fake Keys','Fakeco')"); R("initMidi()"); pg.wait_for_timeout(300)
    ok(J(R, "ctlAll().length") == 0, 'an unknown keyboard gets no template by itself', J(R, "ctlAll().length"))
    bass = J(R, "(()=>{const t=S.tracks.find(t=>t.name==='Bass');selectTrack(t.id);return t.id})()"); pg.wait_for_timeout(200)
    # ---- a known controller: the template is applied when it is first plugged in ----
    R("FAKEMIDI.plug(%s,'AKAI')" % json.dumps(MPK)); pg.wait_for_timeout(200)
    ms = J(R, "ctlAll().filter(m=>m.dev===%s).map(m=>[m.type,m.ch,m.num,m.target,m.tpl])" % json.dumps(MPK))
    ok(len(ms) == 24 and ['cc', 0, 70, '@dev:0', 'mpkmini'] in ms and ['note', 9, 36, '@pad:0', 'mpkmini'] in ms and ['note', 9, 51, '@pad:15', 'mpkmini'] in ms, 'MPK mini plugged in: its template is applied (8 knobs CC 70 to 77, 16 pads on channel 10)', len(ms))
    ok('MPK mini 3' in R("$('#toast').textContent") and 'drum kit' in R("$('#toast').textContent"), 'a toast says so', R("$('#toast').textContent"))
    ok(J(R, "UI.ctlTplSeen[%s]" % json.dumps(MPK)) == 1, 'remembered, so removing it is not undone at the next start')
    # knobs follow the selected device
    P = J(R, "ctlTDev()"); ok(P['i'] >= 0 and len(P['ids']) >= 2, 'the selected track shows a device with knobs', [P['i'], len(P['devs']), P['ids'][:3]])
    k0 = P['ids'][0]; R("(C=>C.set(C.spec.v(.5)))(CT.get(%s))" % json.dumps(k0))
    msg(R, MPK, [0xB0, 70, 10]); ok(abs(val(R, k0) - .5) < .01, 'pick up: knob 1 far from the control does not move it yet', val(R, k0))
    msg(R, MPK, [0xB0, 70, 64], [0xB0, 70, 100]); ok(abs(val(R, k0) - 100 / 127) < .01, 'once the knob passes the control it moves it', val(R, k0))
    ok(J(R, "ctlLabel('@dev:0')") == 'Selected device, knob 1' and J(R, "ctlLabel('@pad:3')") == 'Drum kit pad 4', 'template targets have plain names')
    # another track selected: the same knob moves that track's device
    t2 = J(R, "(()=>{const t=S.tracks.find(t=>t.kind==='inst'&&t.id!=='%s'&&!(t.inst&&t.inst.preset==='drums'));selectTrack(t.id);return t.id})()" % bass); pg.wait_for_timeout(200)
    P2 = J(R, "ctlTDev()"); k2 = P2['ids'][0] if P2['ids'] else None
    ok(k2 and k2 != k0, 'another track selected: knob 1 now points at its device', [k0, k2])
    R("(C=>C.set(C.spec.v(.2)))(CT.get(%s))" % json.dumps(k2)); msg(R, MPK, [0xB0, 70, 25], [0xB0, 70, 40])
    ok(abs(val(R, k2) - 40 / 127) < .03, 'knob 1 moves the new device', val(R, k2))
    # ---- pads: the drum kit when a drum kit is selected, notes otherwise ----
    R("window.NO=[];{const o=noteOn;noteOn=function(p,v,k){NO.push([p,k]);return o.apply(this,arguments)}}0"); msg(R, MPK, [0x99, 36, 100], [0x89, 36, 0]); vo = J(R, "NO")
    ok(vo == [[12, 'm36']], 'an instrument track selected: a pad plays a note as before (noteOn(12), key m36)', vo)
    ok(J(R, "[...LIVE.keys()]") == [], 'and the note stops', J(R, "[...LIVE.keys()]"))
    dr = J(R, "(()=>{const t=S.tracks.find(t=>t.inst&&t.inst.preset==='drums');selectTrack(t.id);return t.name})()"); pg.wait_for_timeout(200)
    R("VO.length=0"); msg(R, MPK, [0x99, 38, 90]); ok(J(R, "VO") == [[dr, 38]] and J(R, "LIVE.has('ctp:MPK mini 3:9:38')"), 'a drum kit selected: pad 3 plays the kit pad 3', J(R, "VO"))
    msg(R, MPK, [0x89, 38, 0]); ok(not J(R, "LIVE.has('ctp:MPK mini 3:9:38')"), 'and stops on note off')
    # ---- a keyboard with no known template: set up by moving ----
    R("ctlPage()"); pg.wait_for_timeout(200)
    rows = J(R, "[...document.querySelectorAll('#ctlWin .cmtp')].map(e=>e.dataset.d)")
    ok(rows == ['Fake Keys', MPK], 'the Controllers page lists both controllers under Templates', rows)
    ok(J(R, "document.querySelector('#ctlWin .cmtp[data-d=\"MPK mini 3\"] select').value") == 'mpkmini', 'the MPK shows its template in use')
    R("CTT.sel['Fake Keys']='g88';ctlPagePaint()")
    R("document.querySelector('#ctlWin .cmtp[data-d=\"Fake Keys\"] [data-k3=guide]').click()"); pg.wait_for_timeout(100)
    ok('Knob 1' in R("document.querySelector('#ctlWin .cmgd').textContent"), 'set up by moving: asks for Knob 1', R("document.querySelector('#ctlWin .cmgd').textContent")[:120])
    pg.screenshot(path=os.path.join(OUT, 'c3a_guide.png'))
    for i in range(8): msg(R, 'Fake Keys', [0xB0, 20 + i, 10], [0xB0, 20 + i, 12], [0xB0, 20 + i, 14])
    msg(R, 'Fake Keys', [0xB0, 20, 30])  # knob 1 again: ignored
    ok('Fader 1' in R("document.querySelector('#ctlWin .cmgd').textContent"), 'each knob fills one slot; turning on or going back to a set knob is ignored', R("document.querySelector('#ctlWin .cmgd').textContent")[:120])
    for i in range(3): msg(R, 'Fake Keys', [0xB0, 40 + i, 50])
    R("for(let i=0;i<6;i++)ctlGuideSkip()")  # 5 faders and the master: not there
    msg(R, 'Fake Keys', [0xB0, 115, 127], [0xB0, 115, 0]); msg(R, 'Fake Keys', [0xB0, 116, 127], [0xB0, 116, 0])
    R("document.querySelector('#ctlWin [data-k3=gdone]').click()"); pg.wait_for_timeout(100)
    fk = J(R, "ctlAll().filter(m=>m.dev==='Fake Keys').map(m=>[m.num,m.target])")
    ok(len(fk) == 13 and [20, '@dev:0'] in fk and [42, '@vol:2'] in fk and [115, '@cmd:play'] in fk and [116, '@cmd:stop'] in fk and J(R, "CTT.guide") is None, 'Finish: 8 knobs, 3 faders, Play and Stop are mapped', fk)
    # faders on track levels of the bank of 8
    t0 = J(R, "S.tracks[0].id"); R("(C=>C.set(C.spec.v(.3)))(CT.get('hd:%s'))" % t0); msg(R, 'Fake Keys', [0xB0, 40, 38], [0xB0, 40, 60])
    ok(abs(val(R, 'hd:' + t0) - 60 / 127) < .01, 'fader 1 moves the level of track 1', val(R, 'hd:' + t0))
    # Play and Stop buttons
    msg(R, 'Fake Keys', [0xB0, 115, 127]); pg.wait_for_timeout(200); on1 = J(R, "play.on"); msg(R, 'Fake Keys', [0xB0, 115, 0])
    msg(R, 'Fake Keys', [0xB0, 116, 127], [0xB0, 116, 0]); pg.wait_for_timeout(200)
    ok(on1 and not J(R, "play.on"), 'Play button starts, Stop button stops', on1)
    # MMC transport from a keyboard with no mapping
    msg(R, 'Fake Keys', [0xF0, 0x7F, 0x7F, 0x06, 0x02, 0xF7]); pg.wait_for_timeout(200); on2 = J(R, "play.on")
    msg(R, 'Fake Keys', [0xF0, 0x7F, 0x7F, 0x06, 0x01, 0xF7]); pg.wait_for_timeout(200)
    ok(on2 and not J(R, "play.on"), 'transport messages (MMC Play, Stop) work', on2)
    # navigation: next device
    nd = J(R, "[ctlTDev().i,ctlTDev().devs.length]"); R("ctlTNav('devNext')"); ok(nd[0] + 1 >= nd[1] or J(R, "ctlTDev().i") == nd[0] + 1, 'Next device moves the knobs on', nd)
    ok('Knobs:' in R("$('#toast').textContent"), 'and says which device', R("$('#toast').textContent"))
    # ---- save as my template, use it on another device ----
    R("CTT.saving='Fake Keys';ctlPagePaint()"); R("const i=document.querySelector('#ctlWin [data-k3=nm]');i.value='Studio keys';document.querySelector('#ctlWin [data-k3=savego]').click()"); pg.wait_for_timeout(100)
    u = J(R, "UI.ctlTpl.map(t=>[t.name,t.slots.length])"); ok(u == [['Studio keys', 13]], 'saved as the user template "Studio keys"', u)
    R("FAKEMIDI.plug('Other Keys','X')"); pg.wait_for_timeout(100); n = J(R, "ctlTplApply('Other Keys',UI.ctlTpl[0].id)")
    ok(n == 13 and J(R, "ctlAll().filter(m=>m.dev==='Other Keys').length") == 13, 'the user template maps another controller', n)
    ok(J(R, "ctlTplRemove('Other Keys')") == 13, 'Remove takes those mappings away')
    # the mappings page lists template mappings with plain names
    R("ctlPagePaint()"); pg.wait_for_timeout(100)
    t = R("document.querySelector('#ctlWin').textContent")
    ok('Selected device, knob 1' in t and 'Drum kit pad 16' in t and 'Play or pause' in t, 'the mappings list names template mappings plainly')
    tips = J(R, "[...document.querySelectorAll('#ctlWin .cmtp button,#ctlWin .cmtp select')].filter(e=>!e.title).map(e=>e.outerHTML.slice(0,80))")
    ok(tips == [], 'every new control has a tooltip', tips)
    ok('—' not in R("[...document.querySelectorAll('#ctlWin .cmtpl *')].map(e=>e.textContent+(e.title||'')).join(' ')"), 'no em dash in the new text')
    pg.screenshot(path=os.path.join(OUT, 'c3a_page.png'))
    R("const c=$('#liteChk');if(!c.checked){c.checked=true;c.dispatchEvent(new Event('change'))}"); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(OUT, 'c3a_page_light.png'))
    R("const c=$('#liteChk');c.checked=false;c.dispatchEvent(new Event('change'))")
    # Launchkey DAW port gets nothing; old projects untouched
    R("FAKEMIDI.plug('Launchkey Mini MK3 DAW Port','Novation')"); pg.wait_for_timeout(100)
    ok(J(R, "ctlAll().filter(m=>m.dev==='Launchkey Mini MK3 DAW Port').length") == 0, 'the Launchkey DAW port is left alone')
    ok(J(R, "S.ctl==null||!S.ctl.maps.some(m=>m.tpl)"), 'templates are kept for every project, not written into the project')
    # idle
    R("window.__to=[];{const o=setTimeout;window.setTimeout=function(){const s=(new Error().stack||'');if(/ctl|p1/.test(s))__to.push(s.slice(0,200));return o.apply(this,arguments)}}"); pg.wait_for_timeout(1500)
    ok(J(R, "__to") == [], 'nothing of the controller layer runs while the controllers are still', J(R, "__to"))
    ok(not logs, 'no console errors', logs)
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
