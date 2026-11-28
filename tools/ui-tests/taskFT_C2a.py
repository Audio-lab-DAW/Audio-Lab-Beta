#!/usr/bin/env python3
"""Task FT-C2a (v0.238): Ableton Push 1, part 1 (connect, display, pads), with a fake Push 1 on the fake MIDI system of FT-C1a:
it sends Push 1 messages (pads, buttons, encoders, strip) and records the SysEx and notes AudioLab sends back.
   python3 tools/ui-tests/taskFT_C2a.py [index.html] [out dir]"""
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


PUSH = 'Ableton Push'
def sx(R): return J(R, "FAKEMIDI.sent.filter(x=>x.port==='Ableton Push'&&x.data[0]===0xF0).map(x=>x.data)")
def lines(R):
    out = {}
    for d in sx(R):
        if d[:4] == [0xF0, 0x47, 0x7F, 0x15] and 0x18 <= d[4] <= 0x1B: out[d[4] - 0x18] = ''.join(chr(c) for c in d[8:-1])
        if d[:4] == [0xF0, 0x47, 0x7F, 0x15] and 0x1C <= d[4] <= 0x1F: out[d[4] - 0x1C] = ''
    return out
def pads(R): return {d[1]: d[2] for d in J(R, "FAKEMIDI.sent.filter(x=>x.port==='Ableton Push'&&x.data[0]===0x90).map(x=>x.data)")}
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 238), 'version 0.238 or later', v)
    R("initMidi()"); pg.wait_for_timeout(200)
    # an instrument track selected, key A minor, colour red
    t = J(R, "(()=>{const t=S.tracks.find(t=>t.kind==='inst');selectTrack(t.id);PR.root=9;PR.scale='minor';t.color='#e5484d';return t.name})()")
    R("FAKEMIDI.plug('Ableton Push','Ableton');FAKEMIDI.plug('Ableton Push User Port','Ableton');FAKEMIDI.plug('Ableton Push 2','Ableton')"); pg.wait_for_timeout(200)
    s = J(R, "Object.fromEntries([...CTL.devs.values()].map(d=>[d.name,d.prof.id]))")
    ok(s == {'Ableton Push': 'push1', 'Ableton Push User Port': 'generic', 'Ableton Push 2': 'generic'}, 'the Live port gets the Push 1 profile; its User port and a Push 2 stay generic', s)
    ok(J(R, "P1.match||1") and J(R, "['MIDIIN2 (Ableton Push)','Ableton Push Live Port'].map(n=>p1Match({name:n}))") == [False, True], 'Windows user port (MIDIIN2) left alone, "Live Port" matched')
    X = sx(R)
    ok([0xF0, 0x47, 0x7F, 0x15, 0x62, 0, 1, 0, 0xF7] in X, 'hello: Live mode by SysEx (F0 47 7F 15 62 00 01 00 F7)')
    ok([0xF0, 0x47, 0x7F, 0x15, 0x5C, 0, 1, 0, 0xF7] in X and [0xF0, 0x47, 0x7F, 0x15, 0x63, 0, 1, 6, 0xF7] in X, 'pressure per pad (5C) and touch strip as pitch bend (63, mode 6)')
    L = lines(R); ok(sorted(L) == [0, 1, 2, 3] and all(len(L[k]) in (0, 68) for k in L), 'the 4 display lines written, 68 characters each (F0 47 7F 15 18..1B 00 45 00 ... F7)', L)
    w = [d for d in X if 0x18 <= d[4] <= 0x1B and d[8:-1]]
    ok(all(d[5:8] == [0, 69, 0] and len(d) == 77 for d in w), 'line message shape: 00, 69 bytes follow (offset 0 + 68), 77 bytes in all', [d[:8] for d in w])
    ok(t[:16] in L[2] and 'A minor' in L[2] and 'Oct 2' in L[2], 'display: track name, key and octave (on line 3 since FT-C2b: lines 1 and 2 show the device)', L)
    P = pads(R); ok(sorted(P) == list(range(36, 100)), 'all 64 pads coloured', len(P))
    ok(P[36] == 5 and P[42] == 3 and P[37] == 3 and P[43] == 5, 'in key: the root pad (bottom left) in the track colour (red = 5), other pads white (3), the octave above red again', (P[36], P[37], P[42], P[43]))
    root_pads = [n for n in range(36, 100) if P[n] == 5]; ok(len(root_pads) >= 8, 'root pads repeat up the grid', root_pads)
    btn = J(R, "FAKEMIDI.sent.filter(x=>x.port==='Ableton Push'&&x.data[0]===0xB0).map(x=>x.data)")
    ok([0xB0, 55, 4] in btn and [0xB0, 54, 4] in btn and [0xB0, 58, 1] in btn and [0xB0, 50, 4] in btn, 'buttons lit: octave up and down, Scales dim, Note', btn)
    ok(not [x for x in J(R, "FAKEMIDI.sent.filter(x=>x.port!=='Ableton Push').map(x=>x.data)") if x[0] == 0xF0], 'nothing sent to the User port or the Push 2')
    # pads play, in key, A minor, octave 2: pad 36 = A1 (MIDI 45), pad 37 = B (47), row 2 (pad 44) = 4th degree D (50)
    R("window.VO=[];{const o=voiceOn;voiceOn=function(t,p,v){VO.push([t.name,p,+v.toFixed(3)]);return o.apply(this,arguments)}}0")
    R("FAKEMIDI.sent.length=0;FAKEMIDI.msg('Ableton Push',[0x90,36,127]);FAKEMIDI.msg('Ableton Push',[0x90,37,64]);FAKEMIDI.msg('Ableton Push',[0x90,44,100])")
    vo = J(R, "VO")
    ok([x[1] for x in vo] == [45 - 24, 47 - 24, 50 - 24] and vo[0][0] == t, 'pads play the selected track, unarmed, in A minor: A, B, and D one row up (fourths)', vo)
    ok(abs(vo[1][2] - 64 / 127) < .002, 'linear velocity', vo[1])
    P = pads(R); ok(P.get(36) == 21 and P.get(37) == 21 and P.get(44) == 21, 'held pads turn green', P)
    same = [n for n, c in P.items() if c == 21]
    ok(len(same) > 3, 'pads with the same note elsewhere light up too', same)
    R("FAKEMIDI.sent.length=0;FAKEMIDI.msg('Ableton Push',[0x80,36,0]);FAKEMIDI.msg('Ableton Push',[0x90,37,0]);FAKEMIDI.msg('Ableton Push',[0x80,44,0])")
    ok(J(R, "[...LIVE.keys()].filter(k=>String(k).startsWith('p1:')).length") == 0, 'note off (also note on with velocity 0) stops them')
    P = pads(R); ok(P.get(36) == 5 and P.get(37) == 3 and len(P) < 30, 'colours back; only changed pads sent', (P.get(36), len(P)))
    # encoder touch and strip touch never play; strip as pitch bend
    R("VO.length=0;window.CCL=[];{const c=ccLive;ccLive=function(k,v){CCL.push([String(k),+(+v).toFixed(3)]);return c.apply(this,arguments)}};FAKEMIDI.msg('Ableton Push',[0x90,0,127]);FAKEMIDI.msg('Ableton Push',[0x90,12,127]);FAKEMIDI.msg('Ableton Push',[0xE0,0,96])")
    ok(J(R, "VO.length") == 0 and J(R, "CCL") == [['pb', round((96 << 7) / 16383, 3)]], 'encoder and strip touches do not play; the strip bends pitch', J(R, "CCL"))
    R("CCL.length=0;FAKEMIDI.msg('Ableton Push',[0xB0,56,127]);FAKEMIDI.msg('Ableton Push',[0xB0,56,0])")
    ok(J(R, "CCL") == [], 'Push buttons are not recorded into controller lanes')
    # octave
    R("FAKEMIDI.sent.length=0;FAKEMIDI.msg('Ableton Push',[0xB0,55,127]);FAKEMIDI.msg('Ableton Push',[0xB0,55,0])")
    L = lines(R); ok(J(R, "p1S().oct") == 3 and list(L) == [2] and 'Oct 3' in L[2], 'Octave up: octave 3, only the changed display line sent', L)
    R("VO.length=0;FAKEMIDI.msg('Ableton Push',[0x90,36,100]);FAKEMIDI.msg('Ableton Push',[0x80,36,0])")
    ok(J(R, "VO.map(x=>x[1])") == [57 - 24], 'pad 36 now plays A2 (MIDI 57)', J(R, "VO"))
    R("FAKEMIDI.msg('Ableton Push',[0xB0,54,127])")
    # Scales mode: encoders change key, scale, layout...
    R("FAKEMIDI.sent.length=0;FAKEMIDI.msg('Ableton Push',[0xB0,58,127])"); L = lines(R)
    ok(J(R, "[...CTL.devs.values()].find(d=>d.name==='Ableton Push').p1.scales") and 'Root' in L.get(0, '') and 'Layout' in L.get(0, '') and 'Octave' in L.get(0, ''), 'Scales: the display shows the 8 settings', L)
    ok(all(len(L[k]) in (0, 68) for k in L), 'still 68 characters a line')
    R("for(let i=0;i<3;i++)FAKEMIDI.msg('Ableton Push',[0xB0,71,1])")
    ok(J(R, "PR.root") == 10, 'encoder 1 (3 steps) moves the root up a semitone: A# ', J(R, "PR.root"))
    R("for(let i=0;i<3;i++)FAKEMIDI.msg('Ableton Push',[0xB0,71,127])")
    R("for(let i=0;i<3;i++)FAKEMIDI.msg('Ableton Push',[0xB0,73,1])")
    ok(J(R, "p1S().lay") == 'chrom', 'encoder 3: chromatic layout')
    P = {int(k): v for k, v in J(R, "Object.fromEntries([...CTL.devs.values()].find(d=>d.name==='Ableton Push').p1.led)").items()}; ok(pads(R).get(37) == 0 and P.get(36) == 5 and P.get(37) == 0 and P.get(38) == 3, 'chromatic: root in colour, A# dark (out of key), B white', (P.get(36), P.get(37), P.get(38)))
    R("VO.length=0;FAKEMIDI.msg('Ableton Push',[0x90,44,100]);FAKEMIDI.msg('Ableton Push',[0x80,44,0])")
    ok(J(R, "VO.map(x=>x[1])") == [45 + 5 - 24], 'chromatic fourths: one row up is 5 semitones', J(R, "VO"))
    R("for(let i=0;i<6;i++)FAKEMIDI.msg('Ableton Push',[0xB0,75,1])")
    ok(J(R, "p1S().vc") == 'hard', 'encoder 5: velocity curve (two steps: hard)', J(R, "p1S().vc"))
    R("for(let i=0;i<3;i++)FAKEMIDI.msg('Ableton Push',[0xB0,75,1])"); ok(J(R, "p1S().vc") == 'fixed', 'fixed')
    R("FAKEMIDI.sent.length=0;for(let i=0;i<3;i++)FAKEMIDI.msg('Ableton Push',[0xB0,77,1])")
    ok(J(R, "p1S().strip") == 'mod' and [0xF0, 0x47, 0x7F, 0x15, 0x63, 0, 1, 10, 0xF7] in sx(R), 'encoder 7: the strip becomes modulation (strip mode 10 sent)')
    R("for(let i=0;i<6;i++)FAKEMIDI.msg('Ableton Push',[0xB0,76,1])")
    ok(J(R, "p1S().at") == 'chan' and [0xF0, 0x47, 0x7F, 0x15, 0x5C, 0, 1, 1, 0xF7] in sx(R), 'encoder 6: pressure for the whole grid (5C 1 sent)')
    R("window.__PRS=[];FT_HOOKS.pressure=(n,v)=>__PRS.push([n,+v.toFixed(3)]);FAKEMIDI.msg('Ableton Push',[0xD0,64])")
    ok(J(R, "__PRS") == [[None, round(64 / 127, 3)]], 'pressure goes to the hook FT_HOOKS.pressure for later steps', J(R, "__PRS"))
    R("FAKEMIDI.msg('Ableton Push',[0xB0,58,127])")
    R("VO.length=0;CCL.length=0;FAKEMIDI.msg('Ableton Push',[0x90,36,20]);FAKEMIDI.msg('Ableton Push',[0x80,36,0]);FAKEMIDI.msg('Ableton Push',[0xE0,0,127])")
    ok(abs(J(R, "VO[0][2]") - 100 / 127) < .002 and J(R, "CCL")[0][0] == '1', 'fixed velocity plays 100; the strip moves the mod wheel lane', (J(R, "VO"), J(R, "CCL")))
    # outside Scales, the encoders can be learned (endless knobs)
    kn = J(R, "[...document.querySelectorAll('#fxin .kn[data-c^=\"fx:\"],#fxin .vb[data-c^=\"fx:\"]')].filter(e=>e.offsetWidth).map(e=>e.dataset.c)")
    if kn:
        R("midiLearn(true);ML.sel=%s;FAKEMIDI.msg('Ableton Push',[0xB0,71,1]);midiLearn(false);FAKEMIDI.msg('Ableton Push',[0xB0,71,1]);FAKEMIDI.msg('Ableton Push',[0xB0,71,127])" % json.dumps(kn[0]))
        ok(J(R, "ctlAll().filter(m=>m.dev==='Ableton Push'&&m.num===71).map(m=>m.enc)") == ['rel2c'], 'outside Scales an encoder can be learned, found as an endless knob')
    # track colour and selection follow
    R("FAKEMIDI.sent.length=0;(t=>{t.color='#2040ff';changed(false)})(curT())"); pg.wait_for_timeout(200)
    P = pads(R); ok(P.get(36) == 45, 'track colour changed to blue: root pads blue (45)', P.get(36))
    # the Controllers page shows the Push settings
    R("ctlPage()"); pg.wait_for_timeout(200)
    s = J(R, "(()=>{const w=document.querySelector('#ctlWin .p1set');return w?{sel:[...w.querySelectorAll('select[data-p1]')].map(x=>x.dataset.p1),tips:[...w.querySelectorAll('select,label')].filter(e=>!e.title).length,em:/\u2014/.test(w.textContent)}:null})()")
    ok(s and s['sel'] == ['lay', 'rows', 'vc', 'at', 'strip', 'oct'] and s['tips'] == 0 and not s['em'], 'the Controllers page has the Push 1 settings, with tooltips, no em dash', s)
    pg.locator('#ctlWin .p1set select[data-p1=lay]').select_option('key'); pg.wait_for_timeout(100)
    ok(J(R, "p1S().lay") == 'key' and J(R, "UI.p1.lay") == 'key', 'a change on the page reaches the Push (kept in UI.p1)')
    pg.screenshot(path=os.path.join(OUT, 'c2a_page.png'))
    R("const c=$('#liteChk');if(!c.checked){c.checked=true;c.dispatchEvent(new Event('change'))}"); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(OUT, 'c2a_page_light.png'))
    R("const c=$('#liteChk');c.checked=false;c.dispatchEvent(new Event('change'))")
    # idle: no timers from the Push
    # only the controller layer's own timers count (scheduled from a p1*/ctl* function, or from inside the callback of one): the glass copy
    # (elSoon from gbCopy) and other lanes' timers run while idle too and made this check flaky (task RG, 28 Nov); all timers are listed for the detail
    R("window.__to=0;window.__toAll=0;window.__toOther={};{const o=setTimeout,RX=/\\b(p1[A-Z]\\w*|P1|ctl[A-Z]\\w*|CTL)\\b/;let inP=0;window.setTimeout=function(fn){__toAll++;"
      "const st=(new Error().stack||'').split('\\n').slice(2).join(' '),mine=inP||RX.test(st)||RX.test(typeof fn==='function'&&fn.name||'');if(mine)__to++;else{const k=(st.match(/at (\\S+)/)||[])[1]||'?';__toOther[k]=(__toOther[k]||0)+1}"
      "const a=[].slice.call(arguments);if(mine&&typeof fn==='function')a[0]=function(){inP++;try{return fn.apply(this,arguments)}finally{inP--}};return o.apply(this,a)}}"); pg.wait_for_timeout(1500)
    ok(J(R, "__to") < 2, 'nothing runs while the Push is still (its own timers)', [J(R, "__to"), J(R, "__toAll"), J(R, "__toOther")])
    # the count is real: an edit (changed()) makes the Push repaint through its own timer (p1All), and that one is counted
    n0 = J(R, "__to"); R("changed()"); pg.wait_for_timeout(200)
    ok(J(R, "__to") > n0, 'a Push repaint after an edit is counted as the Push\'s own timer', [n0, J(R, "__to")])
    # goodbye: switched off on the page, and on page hide
    R("FAKEMIDI.sent.length=0")
    pg.locator('#ctlWin input[data-k2=dev][data-d="Ableton Push"]').uncheck(); pg.wait_for_timeout(100)
    L = lines(R); P = pads(R)
    ok(L == {0: '', 1: '', 2: '', 3: ''} and len(P) == 64 and set(P.values()) == {0}, 'switched off: display cleared (1C..1F) and every pad dark', (L, len(P)))
    pg.locator('#ctlWin input[data-k2=dev][data-d="Ableton Push"]').check(); pg.wait_for_timeout(100)
    ok(len(lines(R)) == 4 and len(pads(R)) == 64, 'switched on again: hello again, display and pads back')
    R("FAKEMIDI.sent.length=0;dispatchEvent(new Event('pagehide'))")
    ok(lines(R) == {0: '', 1: '', 2: '', 3: ''} and set(pads(R).values()) == {0}, 'page hidden (AudioLab quits): display cleared and pads dark')
    ok(not logs, 'no console errors', logs)
    b.close()
    # SysEx refused: the pads still play, no SysEx sent
    b, pg, logs, R = boot(p, refuse=True)
    R("initMidi()"); pg.wait_for_timeout(200)
    R("(t=>selectTrack(t.id))(S.tracks.find(t=>t.kind==='inst'));FAKEMIDI.plug('Ableton Push','Ableton')"); pg.wait_for_timeout(200)
    R("window.VO=[];{const o=voiceOn;voiceOn=function(t,p,v){VO.push(p);return o.apply(this,arguments)}};FAKEMIDI.msg('Ableton Push',[0x90,36,100]);FAKEMIDI.msg('Ableton Push',[0x80,36,0])")
    ok(J(R, "VO.length") == 1 and not sx(R) and len(pads(R)) == 64, 'without SysEx: pads play and are coloured, no SysEx sent')
    ok(not logs, 'no console errors (without SysEx)', logs)
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
