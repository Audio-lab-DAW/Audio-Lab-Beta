#!/usr/bin/env python3
"""Task FT-C3b (Mackie Control and HUI, fake surfaces). Based on the C2b harness.
Task FT-C2b (v0.239): Ableton Push 1, part 2 (control): encoders on the selected device and on track volume and pan, the two rows of
track buttons, transport, tempo, master, undo, duplicate, delete, quantize, the drum kit's 4x4 pads and 16-step lane, with the fake Push 1.
   python3 tools/ui-tests/taskFT_C2b.py [index.html] [out dir]"""
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




XT = 'X-Touch'; EXT = 'X-Touch-Ext'; HU = 'Fake HUI'
def msg(R, dev, *ms): R(";".join("FAKEMIDI.msg(%s,%s)" % (json.dumps(dev), json.dumps(list(m))) for m in ms))
def sent(R, dev): return J(R, "FAKEMIDI.sent.filter(x=>x.port===%s).map(x=>x.data)" % json.dumps(dev))
val = lambda R, id: J(R, "(C=>C?C.spec.n(C.get()):null)(CT.get(%s))" % json.dumps(id))
def lcd(R, dev, xt=0x14):
    out = ['', '']
    for d in sent(R, dev):
        if d[:6] == [0xF0, 0, 0, 0x66, xt, 0x12]:
            o = d[6]; t = ''.join(chr(c) for c in d[7:-1]); line = o // 56; out[line] = (out[line].ljust(56)[:o % 56] + t)[:56]
    return out
def tc(R, dev):
    m = {0x40 + 9 - int(k[1:]): v for k, v in J(R, "[...[...CTL.devs.values()].find(d=>d.name===%s).mc.out].filter(x=>x[0][0]==='t')" % json.dumps(dev))}
    s = ''
    for cc in range(0x49, 0x3F, -1):
        v = m.get(cc, 0x20); ch = v & 0x3F; s += (chr(ch + 0x40) if ch < 0x20 else chr(ch)) + ('.' if v & 0x40 else '')
    return s
def leds(R, dev): return {d[1]: d[2] for d in sent(R, dev) if d[0] == 0x90}
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 248), 'version 0.248 or later', v)
    R("initMidi()"); pg.wait_for_timeout(200)
    R("FAKEMIDI.plug(%s,'Behringer')" % json.dumps(XT)); pg.wait_for_timeout(300)
    ok(J(R, "[...CTL.devs.values()].find(d=>d.name==='X-Touch').prof.id") == 'mcu', 'an X-Touch is a Mackie Control surface by its name')
    ok(J(R, "ctlAll().filter(m=>m.dev==='X-Touch').length") == 0, 'no template is put on it')
    T = J(R, "S.tracks.slice(0,8).map(t=>[t.id,t.name,t.vol,t.mute,t.solo])")
    L = lcd(R, XT); ok(L[0].startswith(T[0][1][:6]) and T[1][1][:6] in L[0], 'display line 1: the 8 track names, 7 characters each', L[0])
    ok(len(L[1].strip()) > 0, 'display line 2: their pans', L[1])
    pb = {d[0] & 15: (d[2] << 7) | d[1] for d in sent(R, XT) if d[0] & 0xF0 == 0xE0}
    exp = [round(val(R, 'hd:' + T[i][0]) * 16383) for i in range(8)]
    ok([pb.get(i) for i in range(8)] == exp and 8 in pb, 'motor faders sent to the levels of tracks 1 to 8 and the master', ([pb.get(i) for i in range(8)], exp))
    ok(tc(R, XT).replace(' ', '') == '1.1.01.001', 'time code display: bar 1, beat 1, 16th 01, tick 001', tc(R, XT))
    # fader 1 moved with touch: one undo step, no echo while touched
    u0 = J(R, "UNDO.length"); R("FAKEMIDI.sent.length=0"); msg(R, XT, [0x90, 104, 127], [0xE0, 0, 32], [0xE0, 0, 40])
    ok(abs(val(R, 'hd:' + T[0][0]) - (40 << 7) / 16383) < .002, 'fader 1 moves track 1 level', val(R, 'hd:' + T[0][0]))
    pg.wait_for_timeout(120); ok(not [d for d in sent(R, XT) if d[0] == 0xE0], 'no motor message back while it is touched')
    msg(R, XT, [0x90, 104, 0]); pg.wait_for_timeout(120); ok(J(R, "UNDO.length") == u0 + 1, 'one undo step for the touch', J(R, "UNDO.length") - u0)
    # level changed on screen: motor follows
    R("FAKEMIDI.sent.length=0;(C=>{C.set(C.spec.v(.25));paintCtl(document.querySelector('[data-c=\"hd:%s\"]')||document.body)})(CT.get('hd:%s'))" % (T[1][0], T[1][0])); R("changed(false)"); pg.wait_for_timeout(200)
    m1 = [((d[2] << 7) | d[1]) for d in sent(R, XT) if d[0] == 0xE1]; ok(m1 and m1[-1] == round(.25 * 16383), 'a level changed in AudioLab moves fader 2', m1)
    # buttons: mute, solo, select, LEDs
    msg(R, XT, [0x90, 16 + 2, 127], [0x90, 16 + 2, 0]); pg.wait_for_timeout(100)
    ok(J(R, "S.tracks[2].mute") != T[2][3] and leds(R, XT).get(18) == (127 if not T[2][3] else 0), 'Mute 3 mutes track 3 and lights', leds(R, XT).get(18))
    msg(R, XT, [0x90, 24 + 3, 127], [0x90, 24 + 3, 0]); pg.wait_for_timeout(100)
    ok(J(R, "selT") == T[3][0] and leds(R, XT).get(27) == 127, 'Select 4 selects track 4 and lights', J(R, "selT"))
    # V-pot pan, press resets
    hp = 'hp:' + T[0][0]; R("(C=>C.set(C.spec.d!=null?C.spec.d:C.spec.v(.5)))(CT.get('%s'))" % hp); n0 = val(R, hp)
    msg(R, XT, [0xB0, 16, 5]); n1 = val(R, hp); msg(R, XT, [0xB0, 16, 0x40 | 10]); n2 = val(R, hp)
    ok(abs(n1 - n0 - .05) < .02 and abs(n2 - n1 + .10) < .02, 'V-pot 1 pans track 1 (5 steps right, 10 left)', (n0, n1, n2))
    msg(R, XT, [0x90, 32, 127], [0x90, 32, 0]); ok(abs(val(R, hp) - n0) < .01, 'pressing it puts pan back to the middle', val(R, hp))
    pg.wait_for_timeout(100); rg = {d[1]: d[2] for d in sent(R, XT) if d[0] == 0xB0 and 0x30 <= d[1] <= 0x37}; ok(rg.get(0x30) == 0x16, 'its LED ring shows the middle (boost and cut mode, LED 6)', rg.get(0x30))
    # Plug-in: V-pots on the selected device
    R("selectTrack(S.tracks.find(t=>t.name==='Bass').id)"); pg.wait_for_timeout(200)
    msg(R, XT, [0x90, 43, 127], [0x90, 43, 0]); pg.wait_for_timeout(100); ids = J(R, "ctlTDev().ids")
    ok(J(R, "MC.vm") == 'plug' and leds(R, XT).get(43) == 127, 'Plug-in: V-pots on the selected device, Plug-in lit')
    k0 = val(R, ids[0]); msg(R, XT, [0xB0, 16, 3]); ok(val(R, ids[0]) > k0, 'V-pot 1 turns the device knob 1', (k0, val(R, ids[0])))
    pg.wait_for_timeout(100); L = lcd(R, XT); lab = J(R, "p1bA(CT.get(%s).label)" % json.dumps(ids[0]))
    ok(L[0].startswith(lab[:6]), 'the display shows the parameter names', L[0])
    msg(R, XT, [0x90, 42, 127], [0x90, 42, 0])
    # banks
    msg(R, XT, [0x90, 47, 127], [0x90, 47, 0]); pg.wait_for_timeout(100); ok(J(R, "MC.tb") == min(8, J(R, "S.tracks.length-1")), 'Bank right: tracks 9 to 16', J(R, "MC.tb"))
    L = lcd(R, XT); nm = J(R, "S.tracks[8]&&S.tracks[8].name"); ok(nm is None or L[0].startswith(nm[:6]), 'the display follows', L[0])
    msg(R, XT, [0x90, 48, 127], [0x90, 48, 0]); ok(J(R, "MC.tb") == J(R, "Math.min(8,S.tracks.length-1)") - 1, 'Channel left: one track back')
    msg(R, XT, [0x90, 46, 127], [0x90, 46, 0]); ok(J(R, "MC.tb") == 0, 'Bank left: back to the start')
    # transport, jog, rewind
    msg(R, XT, [0xB0, 60, 4]); pg.wait_for_timeout(100); ok(J(R, "pos") == 1, 'jog wheel: 4 steps is 4 sixteenths (one beat)', J(R, "pos"))
    ok(tc(R, XT).replace(' ', '') == '1.2.01.001', 'the time code follows', tc(R, XT))
    msg(R, XT, [0x90, 92, 127], [0x90, 92, 0]); ok(J(R, "pos") == 4, 'Fast forward: next bar', J(R, "pos"))
    msg(R, XT, [0x90, 91, 127], [0x90, 91, 0]); ok(J(R, "pos") == 0, 'Rewind: bar start', J(R, "pos"))
    msg(R, XT, [0x90, 94, 127], [0x90, 94, 0]); pg.wait_for_timeout(600); on = J(R, "play.on"); t1 = tc(R, XT)
    ok(on and leds(R, XT).get(94) == 127, 'Play plays and lights', on)
    ok(t1.replace(' ', '') != '1.1.01.001', 'while playing the time code moves', t1)
    msg(R, XT, [0x90, 93, 127], [0x90, 93, 0]); pg.wait_for_timeout(300); ok(not J(R, "play.on") and leds(R, XT).get(94) == 0, 'Stop stops, Play dark')
    pg.wait_for_timeout(300); ok(not J(R, "MC.pollT"), 'the check stops with the song')
    n = J(R, "UNDO.length"); msg(R, XT, [0x90, 81, 127], [0x90, 81, 0]); ok(J(R, "UNDO.length") < n or n == 0, 'Undo undoes')
    # a learned mapping on a surface control wins
    R("ctlG().maps.push({id:'mt',dev:'X-Touch',type:'cc',ch:0,num:17,target:%s,min:0,max:1,take:'jump',enc:'relsb',fb:false});ctlDirty()" % json.dumps(ids[1]))
    hp2 = 'hp:' + J(R, "S.tracks[1].id"); p0 = val(R, hp2); msg(R, XT, [0xB0, 17, 2]); ok(val(R, hp2) == p0, 'V-pot 2 with a learned mapping no longer pans', (p0, val(R, hp2)))
    R("ctlG().maps=ctlG().maps.filter(m=>m.id!=='mt');ctlDirty()")
    # extender
    R("FAKEMIDI.plug(%s,'Behringer')" % json.dumps(EXT)); pg.wait_for_timeout(200)
    L2 = lcd(R, EXT, 0x15); nm = J(R, "S.tracks[8]&&S.tracks[8].name")
    ok(J(R, "[...CTL.devs.values()].find(d=>d.name==='X-Touch-Ext').mc.off") == 8 and (nm is None or L2[0].startswith(nm[:6])), 'an extender shows tracks 9 to 16 (its own display id 0x15)', L2[0])
    # ---- HUI ----
    R("FAKEMIDI.plug(%s,'Fake')" % json.dumps(HU)); pg.wait_for_timeout(200)
    ok(J(R, "[...CTL.devs.values()].find(d=>d.name==='Fake HUI').prof.id") == 'hui', 'a HUI device is found by its name')
    R("FAKEMIDI.sent.length=0"); pg.wait_for_timeout(1150); pings = [d for d in sent(R, HU) if d == [0x90, 0, 0]]
    ok(len(pings) >= 1, 'pinged about once a second', len(pings))
    sc = {d[6]: ''.join(chr(c) for c in d[7:11]) for d in J(R, "FAKEMIDI.sent.length=0,[]") or []}
    R("for(const d of CTL.devs.values())if(d.name==='Fake HUI'){d.mc.lcd={};d.mc.fo=[];d.mc.out.clear()}mcAll()")
    sc = {d[7]: ''.join(chr(c) for c in d[8:12]) for d in sent(R, HU) if d[:7] == [0xF0, 0, 0, 0x66, 5, 0, 0x10]}
    ok(sc.get(0) == J(R, "p1bA(S.tracks[0].name).slice(0,4).padEnd(4)"), 'HUI strip displays: 4 letters of each track', sc)
    hf = [d for d in sent(R, HU) if d[0] == 0xB0 and d[1] in (0, 0x20)]; ok(len(hf) == 2, 'HUI motor fader 1: high and low byte', hf)
    msg(R, HU, [0xB0, 0x0F, 0], [0xB0, 0x2F, 0x40], [0xB0, 0, 50], [0xB0, 0x20, 0], [0xB0, 0x0F, 0], [0xB0, 0x2F, 0])
    ok(abs(val(R, 'hd:' + J(R, "S.tracks[0].id")) - (50 << 7) / 16383) < .002, 'HUI fader 1 (touch, high, low byte) moves track 1 level')
    mu = J(R, "S.tracks[1].mute"); msg(R, HU, [0xB0, 0x0F, 1], [0xB0, 0x2F, 0x42], [0xB0, 0x0F, 1], [0xB0, 0x2F, 2]); pg.wait_for_timeout(100)
    ok(J(R, "S.tracks[1].mute") != mu, 'HUI zone 1 port 2: Mute 2', mu)
    lz = [d for d in sent(R, HU) if d[0] == 0xB0 and d[1] in (0x0C, 0x2C)]; ok([0xB0, 0x0C, 1] in lz and ([0xB0, 0x2C, 0x42] in lz or [0xB0, 0x2C, 2] in lz), 'its LED is set by zone and port', lz[-4:])
    msg(R, HU, [0xB0, 0x0F, 0x0E], [0xB0, 0x2F, 0x44], [0xB0, 0x0F, 0x0E], [0xB0, 0x2F, 4]); pg.wait_for_timeout(300); on = J(R, "play.on")
    msg(R, HU, [0xB0, 0x0F, 0x0E], [0xB0, 0x2F, 0x43]); pg.wait_for_timeout(300); ok(on and not J(R, "play.on"), 'HUI Play and Stop (zone 0E)')
    p0 = val(R, 'hp:' + J(R, "S.tracks[0].id")); msg(R, HU, [0xB0, 0x40, 0x43]); ok(val(R, 'hp:' + J(R, "S.tracks[0].id")) > p0, 'HUI V-pot 1 (0x43 = 3 steps right) pans')
    # ---- Works as, page ----
    R("FAKEMIDI.plug('Plain Box','Fake')"); pg.wait_for_timeout(100); R("ctlPage()"); pg.wait_for_timeout(200)
    R("const s=document.querySelector('#ctlWin .mcset [data-d=\"Plain Box\"] select');s.value='mcu';s.dispatchEvent(new Event('change',{bubbles:true}))"); pg.wait_for_timeout(200)
    ok(J(R, "[...CTL.devs.values()].find(d=>d.name==='Plain Box').prof.id") == 'mcu' and J(R, "UI.ctlAs['Plain Box']") == 'mcu', 'Works as: a device set to Mackie Control becomes one', J(R, "UI.ctlAs"))
    R("const s=document.querySelector('#ctlWin .mcset [data-d=\"Plain Box\"] select');s.value='';s.dispatchEvent(new Event('change',{bubbles:true}))"); pg.wait_for_timeout(200)
    ok(J(R, "[...CTL.devs.values()].find(d=>d.name==='Plain Box').prof.id") == 'generic', 'back to Automatic: generic again')
    tips = J(R, "[...document.querySelectorAll('#ctlWin .mcset select,#ctlWin .mcset .cmtpi')].filter(e=>!e.title).length"); ok(tips == 0, 'tooltips on the new controls')
    ok('—' not in R("[...document.querySelectorAll('#ctlWin .mcset *')].map(e=>e.textContent+(e.title||'')).join(' ')"), 'no em dash')
    pg.screenshot(path=os.path.join(OUT, 'c3b_page.png'))
    # unplug and page hidden: dark
    R("FAKEMIDI.sent.length=0;dispatchEvent(new Event('pagehide'))")
    L = [d for d in sent(R, XT) if d[:6] == [0xF0, 0, 0, 0x66, 0x14, 0x12]]; lo = [d for d in sent(R, XT) if d[0] == 0x90 and d[2]]
    ok(L and all(set(d[7:-1]) == {32} for d in L) and not lo, 'page hidden: display cleared, LEDs off')
    R("FAKEMIDI.unplug('Fake HUI')"); pg.wait_for_timeout(1200); ok(not J(R, "MC.pingT"), 'no HUI left: the ping stops')
    R("window.__to=[];{const o=setTimeout;window.setTimeout=function(){const s=(new Error().stack||'');if(/mc[A-Z]|hui|ctl/.test(s))__to.push(s.slice(0,200));return o.apply(this,arguments)}}"); pg.wait_for_timeout(1500)
    ok(J(R, "__to") == [], 'nothing of the surfaces runs while stopped and still', J(R, "__to"))
    ok(not logs, 'no console errors', logs)
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
