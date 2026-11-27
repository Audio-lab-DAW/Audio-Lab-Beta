#!/usr/bin/env python3
"""Task FT-C2b (v0.239): Ableton Push 1, part 2 (control): encoders on the selected device and on track volume and pan, the two rows of
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


PUSH = 'Ableton Push'
def sx(R): return J(R, "FAKEMIDI.sent.filter(x=>x.port==='Ableton Push'&&x.data[0]===0xF0).map(x=>x.data)")
def lines(R):
    out = {}
    for d in sx(R):
        if d[:4] == [0xF0, 0x47, 0x7F, 0x15] and 0x18 <= d[4] <= 0x1B: out[d[4] - 0x18] = ''.join(chr(c) for c in d[8:-1])
        if d[:4] == [0xF0, 0x47, 0x7F, 0x15] and 0x1C <= d[4] <= 0x1F: out[d[4] - 0x1C] = ''
    return out
def pads(R): return {d[1]: d[2] for d in J(R, "FAKEMIDI.sent.filter(x=>x.port==='Ableton Push'&&x.data[0]===0x90).map(x=>x.data)")}

def btns(R): return [d for d in J(R, "FAKEMIDI.sent.filter(x=>x.port==='Ableton Push'&&x.data[0]===0xB0).map(x=>x.data)")]
def msg(R, *ms): R(";".join("FAKEMIDI.msg('Ableton Push',%s)" % json.dumps(list(m)) for m in ms))
def press(R, cc): msg(R, [0xB0, cc, 127], [0xB0, cc, 0])
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 239), 'version 0.239 or later', v)
    R("initMidi()"); pg.wait_for_timeout(200)
    bass = J(R, "(()=>{const t=S.tracks.find(t=>t.name==='Bass');selectTrack(t.id);PR.root=9;PR.scale='minor';return t.id})()")
    R("FAKEMIDI.plug('Ableton Push','Ableton')"); pg.wait_for_timeout(300)
    L = lines(R)
    ok('Morph' in L[0] and 'Bloom' in L[0] and 'Reso' in L[0], 'Device mode: the first 8 parameters of the instrument (Plant) over the encoders', L.get(0))
    ok('Bass' in L[2] and 'Plant' in L[2] and 'Bank 1 of 2' in L[2] and 'A minor' in L[2], 'line 3: track, device, bank, key', L.get(2))
    ok('>Bass' in L[3], 'line 4: the tracks over the upper row, the selected one marked', L.get(3))
    ok(all(len(L[k]) == 68 for k in L), 'all lines 68 characters')
    B = btns(R); bm = {x[1]: x[2] for x in B}
    ok(bm.get(110) == 4 and bm.get(114) == 1 and bm.get(85) == 1 and bm.get(63) == 4 and bm.get(62) == 0, 'buttons: Device lit, Volume dim, Play dim, > lit (a second bank), < off', {k: bm.get(k) for k in (110, 114, 85, 62, 63)})
    k = J(R, "S.tracks.findIndex(t=>t.id===selT)")
    ok(bm.get(20 + k) == 10 and bm.get(20 + (k + 1) % 8) == 7 and bm.get(102 + k) == 7, 'upper row: selected track bright, others dim; lower row: not armed (dark red)', (bm.get(20 + k), bm.get(102 + k)))
    # encoder 1 turns Morph
    m0 = J(R, "CT.get('fx:pl:morph').spec.n(CT.get('fx:pl:morph').get())"); u0 = J(R, "UNDO.length")
    R("FAKEMIDI.sent.length=0"); msg(R, *[[0xB0, 71, 1]] * 10)
    m1 = J(R, "CT.get('fx:pl:morph').spec.n(CT.get('fx:pl:morph').get())")
    ok(abs(m1 - m0 - 10 / 127) < .01, 'encoder 1, 10 steps: Morph up by 10/127', (m0, m1))
    L = lines(R); ok(list(L) == [1], 'only the values line sent', L)
    ok(J(R, "UNDO.length") == u0 + 1, 'one undo step for the turn', J(R, "UNDO.length") - u0)
    msg(R, [0xB0, 49, 127], *[[0xB0, 71, 127]] * 10, [0xB0, 49, 0])
    m2 = J(R, "CT.get('fx:pl:morph').spec.n(CT.get('fx:pl:morph').get())")
    ok(abs(m1 - m2 - 1 / 127) < .004, 'Shift: fine steps (a tenth)', (m1, m2))
    press(R, 119); m3 = J(R, "CT.get('fx:pl:morph').spec.n(CT.get('fx:pl:morph').get())")
    ok(abs(m3 - m0) < .002, 'Undo on the Push puts it back', (m0, m3))
    msg(R, [0xB0, 49, 127]); press(R, 119); msg(R, [0xB0, 49, 0])
    ok(abs(J(R, "CT.get('fx:pl:morph').spec.n(CT.get('fx:pl:morph').get())") - m2) < .002, 'Shift+Undo: redo')
    # banks and devices
    press(R, 63); L = lines(R); ok('Voices' in L[0] and 'Bank 2 of 2' in L[2], '> : bank 2 (Voices, Sub, Noise, Level, Gain)', L)
    press(R, 62); press(R, 45); L = lines(R); ok('Pro EQ' in L[2] and 'Gain' in L[0], 'Right arrow: next device (Pro EQ)', L.get(2))
    press(R, 45); L = lines(R); ok('Sidechain' in L[2] and 'Shape' in L[0], 'again: Sidechain', L.get(2))
    press(R, 44); press(R, 44); L = lines(R); ok('Plant' in L[2], 'Left arrow back to Plant', L.get(2))
    # mapping wins over the device
    R("ctlG().maps.push({id:'mT',dev:'Ableton Push',type:'cc',ch:0,num:72,target:'fx:pl:space',min:0,max:1,take:'jump',enc:'rel2c',fb:false});ctlDirty()")
    f0 = J(R, "[CT.get('fx:pl:fenv').get(),CT.get('fx:pl:space').get()]"); msg(R, [0xB0, 72, 5])
    f1 = J(R, "[CT.get('fx:pl:fenv').get(),CT.get('fx:pl:space').get()]")
    ok(f1[0] == f0[0] and f1[1] != f0[1], 'a learned mapping on an encoder wins over the device (encoder 2 moves its mapping, not Bloom)', (f0, f1))
    R("ctlG().maps=ctlG().maps.filter(m=>m.id!=='mT');ctlDirty()")
    # Volume and Pan modes
    press(R, 114); L = lines(R); row = J(R, "S.tracks.slice(P1.b0=Math.floor(S.tracks.findIndex(t=>t.id===selT)/8)*8,P1.b0+8).map(t=>t.id)")
    ok('Volume' in L[2] and 'Lower row: Arm' in L[2], 'Volume: the display shows 8 tracks and their volumes', L)
    i = row.index(bass); v0 = J(R, "S.tracks.find(t=>t.id==='%s').vol" % bass)
    msg(R, *[[0xB0, 71 + i, 127]] * 8); v1 = J(R, "S.tracks.find(t=>t.id==='%s').vol" % bass)
    ok(v1 < v0, 'encoder over Bass turns its volume down', (v0, v1))
    press(R, 115); p0 = J(R, "S.tracks.find(t=>t.id==='%s').pan" % bass); msg(R, *[[0xB0, 71 + i, 3]] * 3)
    ok(J(R, "S.tracks.find(t=>t.id==='%s').pan" % bass) > p0 and 'Pan' in lines(R).get(2, 'Pan'), 'Pan & Send: the encoder pans it right')
    press(R, 110); ok(J(R, "[...CTL.devs.values()][0].p1.b.em") == 'dev', 'Device: back to the device')
    # track rows
    other = row[(i + 1) % len(row)]; press(R, 20 + (i + 1) % len(row)); ok(J(R, "selT") == other, 'upper row selects a track')
    press(R, 46); ok(J(R, "selT") == bass, 'Up arrow: the track before')
    press(R, 102 + i); pg.wait_for_timeout(200)
    ok(J(R, "S.tracks.find(t=>t.id==='%s').arm" % bass) is True and {x[1]: x[2] for x in btns(R)}.get(102 + i) == 5, 'lower row arms the track (lit red)')
    press(R, 102 + i); pg.wait_for_timeout(500); ok(not J(R, "S.tracks.find(t=>t.id==='%s').arm" % bass), 'and disarms')
    press(R, 60); press(R, 102 + i); ok(J(R, "S.tracks.find(t=>t.id==='%s').mute" % bass) is True and {x[1]: x[2] for x in btns(R)}.get(102 + i) == 13 and {x[1]: x[2] for x in btns(R)}.get(60) == 4, 'Mute: the lower row mutes (yellow), Mute lit')
    press(R, 102 + i); press(R, 61); press(R, 102 + i); ok(J(R, "S.tracks.find(t=>t.id==='%s').solo" % bass) is True and not J(R, "S.tracks.find(t=>t.id==='%s').mute" % bass), 'Solo: the lower row solos')
    press(R, 102 + i); press(R, 61); ok(J(R, "[...CTL.devs.values()][0].p1.b.lr") == 'arm', 'Solo again: back to arm')
    # transport
    press(R, 85); pg.wait_for_timeout(300); ok(J(R, "play.on") and {x[1]: x[2] for x in btns(R)}.get(85) == 4, 'Play plays, lit')
    press(R, 85); pg.wait_for_timeout(200); ok(not J(R, "play.on") and {x[1]: x[2] for x in btns(R)}.get(85) == 1, 'Play again stops, dim')
    l0 = J(R, "!!S.loop"); msg(R, [0xB0, 49, 127]); press(R, 85); msg(R, [0xB0, 49, 0]); ok(J(R, "!!S.loop") != l0 and not J(R, "play.on"), 'Shift+Play: loop on or off')
    c0 = J(R, "!!S.click"); press(R, 9); ok(J(R, "!!S.click") != c0 and {x[1]: x[2] for x in btns(R)}.get(9) == (4 if not c0 else 1), 'Metronome')
    press(R, 9)
    u0 = J(R, "UNDO.length"); msg(R, [0xB0, 14, 1], [0xB0, 14, 1]); ok(J(R, "S.bpm") == 147 and J(R, "UNDO.length") == u0 + 1, 'tempo encoder: 145 to 147 in one undo step', (J(R, "S.bpm"), J(R, "UNDO.length") - u0))
    press(R, 119); ok(J(R, "S.bpm") == 145, 'undo: 145 again')
    for _ in range(4): press(R, 3); pg.wait_for_timeout(400)
    bp = J(R, "S.bpm"); tp = J(R, "(T=>60000/((T[T.length-1]-T[0])/(T.length-1)))([...CTL.devs.values()][0].p1.b.tap)")
    ok(len(J(R, "[...CTL.devs.values()][0].p1.b.tap")) == 4 and abs(bp - tp) <= 1 and 100 <= bp <= 160, 'Tap tempo: 4 taps about 0.4 s apart set the tempo from their average (the test machine adds its own delay)', (bp, round(tp, 1)))
    R("setBpm(145)")
    ms0 = J(R, "S.master"); msg(R, *[[0xB0, 79, 127]] * 20); ok(J(R, "S.master") < ms0, 'master encoder turns the master level down', (ms0, J(R, "S.master")))
    # duplicate, quantize, delete on the selected clip
    cl = J(R, "(()=>{const t=S.tracks.find(t=>t.id==='%s');const c=t.clips.find(c=>c.notes&&c.notes.length);selC=c.id;return t.clips.length})()" % bass)
    press(R, 88); ok(J(R, "S.tracks.find(t=>t.id==='%s').clips.length" % bass) == cl + 1, 'Duplicate: the selected clip')
    R("(()=>{const t=S.tracks.find(t=>t.id==='%s');selC=t.clips.find(c=>c.notes&&c.notes.length).id;const c=t.clips.find(c=>c.id===selC);c.notes[0].s+=.03})()" % bass)
    press(R, 116); ok(J(R, "(()=>{const c=findClip(selC).c;return Math.abs(c.notes[0].s*4-Math.round(c.notes[0].s*4))<1e-6})()"), 'Quantize: the selected clip to 1/16')
    n0 = J(R, "S.tracks.find(t=>t.id==='%s').clips.length" % bass); press(R, 118)
    ok(J(R, "S.tracks.find(t=>t.id==='%s').clips.length" % bass) == n0 - 1 and J(R, "selC") is None, 'Delete: the selected clip')
    press(R, 119); ok(J(R, "S.tracks.find(t=>t.id==='%s').clips.length" % bass) == n0, 'undo brings it back')
    # drum kit: 4x4 pads and the step lane
    R("window.VO=[];{const o=voiceOn;voiceOn=function(t,p,v){VO.push([t.name,p]);return o.apply(this,arguments)}}0")
    crash = J(R, "(()=>{const t=S.tracks.find(t=>t.inst&&t.inst.preset==='drums');t.inst.psel=0;selectTrack(t.id);pos=0;return t.name})()"); pg.wait_for_timeout(200)
    P = J(R, "Object.fromEntries([...CTL.devs.values()][0].p1.led)"); P = {int(k): v for k, v in P.items()}
    tc = J(R, "p1Col(curT().color)")
    ok(P[36] == 3 and P[37] == tc and P[36 + 3 * 8 + 3] == tc and P[40] == 0 and P[36 + 4 * 8] == 0, 'drum kit: lower left 4x4 pads in the track colour, the chosen pad white, the rest of the lower half dark', (P[36], P[37], P[40], tc))
    ok(P[92] in (1, 2) and P[99] in (1, 2), 'top two rows: the 16 steps (empty, dim)', (P[92], P[99]))
    msg(R, [0x90, 37, 100], [0x80, 37, 0]); ok(J(R, "VO") == [[crash, 37]] and J(R, "curT().inst.psel") == 1, 'pad 2 plays the kit pad 2 (Rim) on the drum track and selects it', J(R, "VO"))
    L = lines(R); ok('Pad 2 Rim' in L.get(2, ''), 'the display shows the chosen pad', L.get(2))
    u0 = J(R, "UNDO.length"); nc = J(R, "curT().clips.length")
    msg(R, [0x90, 92, 100], [0x80, 92, 0])
    st = J(R, "(()=>{const t=curT(),L=p1bLane(t);return {on:L.on,c:!!L.c}})()")
    ok(st['on'][0] and sum(st['on']) >= 1 and J(R, "UNDO.length") == u0 + 1, 'step 1 of the lane: a note of pad 2 at the start of the bar, one undo step', st)
    P = {int(k): v for k, v in J(R, "Object.fromEntries([...CTL.devs.values()][0].p1.led)").items()}; ok(P[92] == tc, 'the step lights in the track colour', P[92])
    msg(R, [0x90, 92 + 4, 100]); st2 = J(R, "p1bLane(curT()).on"); ok(st2[4] and st2[0], 'step 5 too', st2)
    msg(R, [0x90, 92, 100]); ok(not J(R, "p1bLane(curT()).on")[0], 'pressing step 1 again removes it')
    msg(R, [0xB0, 118, 127], [0x90, 37, 100], [0x80, 37, 0], [0xB0, 118, 0]); ok(not any(J(R, "p1bLane(curT()).on")), 'Delete held + pad: clears that pad in the lane')
    ok(J(R, "S.tracks.find(t=>t.id==='%s').clips.length" % bass) == n0, 'Delete used with a pad deletes no clip')
    # Scales still works and the pads go back to notes on an instrument track
    press(R, 58); msg(R, [0xB0, 71, 1], [0xB0, 71, 1], [0xB0, 71, 1]); ok(J(R, "PR.root") == 10, 'Scales: encoder 1 still changes the root'); msg(R, [0xB0, 71, 127], [0xB0, 71, 127], [0xB0, 71, 127]); press(R, 58)
    R("selectTrack('%s')" % bass); pg.wait_for_timeout(150); R("VO.length=0"); msg(R, [0x90, 36, 100], [0x80, 36, 0])
    ok(J(R, "VO") == [['Bass', 45 - 24]], 'an instrument track: pads play notes again', J(R, "VO"))
    # the Controllers page has the short guide
    R("ctlPage()"); pg.wait_for_timeout(200)
    h = J(R, "(()=>{const e=document.querySelector('#ctlWin .p1help');return e?[e.title,e.textContent]:null})()")
    ok(h and h[0] and 'Shift+Play' in h[1] and '\u2014' not in h[1], 'the Controllers page explains the buttons, with a tooltip, no em dash', h)
    pg.screenshot(path=os.path.join(OUT, 'c2b_page.png'))
    R("const c=$('#liteChk');if(!c.checked){c.checked=true;c.dispatchEvent(new Event('change'))}"); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(OUT, 'c2b_page_light.png'))
    R("const c=$('#liteChk');c.checked=false;c.dispatchEvent(new Event('change'))")
    # idle: nothing runs
    R("window.__to=0;{const o=setTimeout;window.setTimeout=function(){__to++;return o.apply(this,arguments)}}{const o=setInterval;window.setInterval=function(){__to++;return o.apply(this,arguments)}}"); pg.wait_for_timeout(1500)
    ok(J(R, "__to") < 5 and not J(R, "P1B.iv"), 'nothing runs while the Push is still', J(R, "__to"))
    # playing on a drum track: the lane follows, and stops following at stop
    R("selectTrack(S.tracks.find(t=>t.inst&&t.inst.preset==='drums').id)"); press(R, 85); pg.wait_for_timeout(400); ok(J(R, "!!P1B.iv"), 'while playing on a drum kit the lane follows the bar')
    press(R, 85); pg.wait_for_timeout(400); ok(not J(R, "P1B.iv"), 'stopped: the follower stops')
    R("FAKEMIDI.sent.length=0;dispatchEvent(new Event('pagehide'))")
    bb = {x[1]: x[2] for x in btns(R)}; ok(bb and set(bb.values()) == {0} and 85 in bb and 20 in bb and 102 in bb, 'page hidden: every lit button dark, also the new ones', len(bb))
    ok(not logs, 'no console errors', logs)
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
