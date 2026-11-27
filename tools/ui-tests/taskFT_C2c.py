#!/usr/bin/env python3
"""Task FT-C2c (v0.243): Ableton Push 1, part 3 (sections as scenes): Session mode with the fake Push 1: the grid of 8 tracks by 8 sections,
the scene buttons and pads launching sections (stopped: play from there; playing: at the next bar, at the end of the section, at once),
the queue and its cancel, scrolling, the encoders on track volume, Note back, the Launch setting.
   python3 tools/ui-tests/taskFT_C2c.py [index.html] [out dir]"""
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


def btns(R): return {x[1]: x[2] for x in J(R, "FAKEMIDI.sent.filter(x=>x.port==='Ableton Push'&&x.data[0]===0xB0).map(x=>x.data)")}
def msg(R, *ms): R(";".join("FAKEMIDI.msg('Ableton Push',%s)" % json.dumps(list(m)) for m in ms))
def press(R, cc): msg(R, [0xB0, cc, 127], [0xB0, cc, 0])
def leds(R): return {int(k): v for k, v in J(R, "Object.fromEntries([...CTL.devs.values()][0].p1.led)").items()}
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
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 243), 'version 0.243 or later', v)
    R("initMidi()"); pg.wait_for_timeout(200)
    bass = J(R, "(()=>{const t=S.tracks.find(t=>t.name==='Bass');selectTrack(t.id);pos=0;return t.id})()")
    R("FAKEMIDI.plug('Ableton Push','Ableton')"); pg.wait_for_timeout(300)
    B = btns(R); ok(B.get(51) == 1 and all(B.get(36 + r, 0) == 0 for r in range(8)), 'before Session: Session dim, scene buttons dark', (B.get(51), [B.get(36 + r) for r in range(8)]))
    R("FAKEMIDI.sent.length=0"); press(R, 51); pg.wait_for_timeout(100)
    secs = J(R, "p1cSecs()"); tracks = J(R, "S.tracks"); L = lines(R)
    ok(J(R, "[...CTL.devs.values()][0].p1.ses") and btns(R).get(51) == 4, 'Session on, its button lit')
    ok(secs[0]['name'][:8] in L[3] and secs[1]['name'][:8] in L[3] and 'Now: ' + secs[0]['name'] in L[2] and 'Launch: Next bar' in L[2], 'display: the 8 sections for the scene buttons, the section now, the launch setting', L)
    ok('>Bass' in L[0] and all(len(x) == 68 for x in L.values()), 'line 1: the 8 tracks across (68 characters a line)', L.get(0))
    tb = J(R, "[...CTL.devs.values()][0].p1.b.tb"); row = tracks[tb:tb + 8]; P = leds(R)
    exp = {36 + (7 - r) * 8 + x: (bool(row[x:x + 1]) and r < len(secs) and has(row[x], secs[r], tracks)) for r in range(8) for x in range(8)}
    bad = [n for n, e in exp.items() if (P.get(n, 0) != 0) != e]
    ok(not bad and sum(exp.values()) > 5, 'pads: lit where the track plays something in the section (checked against the song data: %d of 64 lit)' % sum(exp.values()), bad[:8])
    lit = [n for n, e in exp.items() if e]; x0 = (lit[0] - 36) % 8
    ok(all(P[n] == J(R, "p1Col(%s)" % json.dumps(row[(n - 36) % 8]['color'])) for n in lit), 'lit pads in the track colour (stopped)')
    B = btns(R); ok([B.get(36 + r) for r in range(min(8, len(secs)))] == [7] * min(8, len(secs)), 'scene buttons: one per section, dim', [B.get(36 + r) for r in range(8)])
    # stopped: a scene button plays from the section
    press(R, 38); pg.wait_for_timeout(500)
    ok(J(R, "play.on") and secs[2]['start'] <= J(R, "curBeat()") < secs[2]['start'] + 3, 'stopped: scene 3 plays from %s (beat %g)' % (secs[2]['name'], secs[2]['start']), J(R, "curBeat()"))
    P = leds(R); r2 = [36 + 5 * 8 + x for x in range(8) if exp[36 + 5 * 8 + x]]
    ok(all(P[n] == 21 for n in r2) and btns(R).get(38) == 22, 'the section playing: its pads green, its scene button green', [P[n] for n in r2])
    # playing: launch section 4 at the next bar
    b0 = J(R, "curBeat()"); press(R, 39); q = J(R, "P1C.q")
    ok(q and q['id'] == secs[3]['id'] and q['at'] % 4 == 0 and 0 < q['at'] - b0 <= 4.05, 'playing: section 4 queued for the next bar', (b0, q))
    ok(btns(R).get(39) == 16 and 'Next: ' + secs[3]['name'][:6] in lines(R).get(2, ''), 'queued: scene button yellow, the display says what is next', lines(R).get(2))
    pg.wait_for_timeout(int((q['at'] - b0) * 60000 / J(R, "S.bpm")) + 600)
    cb = J(R, "curBeat()"); ok(J(R, "P1C.q") is None and secs[3]['start'] <= cb < secs[3]['start'] + 3 and J(R, "play.on"), 'at the bar line it jumps to %s and keeps playing' % secs[3]['name'], cb)
    ok('Now: ' + secs[3]['name'][:6] in lines(R).get(2, ''), 'the display follows the section playing', lines(R).get(2))
    # pressing the queued section again cancels it
    press(R, 36); ok(J(R, "P1C.q") is not None, 'queued again'); press(R, 36); ok(J(R, "P1C.q") is None and J(R, "P1C.qT") == 0, 'pressing the queued section again cancels it (and its timer)')
    # Shift+scene: at once
    msg(R, [0xB0, 49, 127]); press(R, 37); msg(R, [0xB0, 49, 0]); pg.wait_for_timeout(200)
    ok(secs[1]['start'] <= J(R, "curBeat()") < secs[1]['start'] + 1.5, 'Shift+scene button: at once', J(R, "curBeat()"))
    # the end of the section, as a scene in Live
    R("p1Set('sq','sec')"); cur = J(R, "p1cCur()"); press(R, 36); q = J(R, "P1C.q")
    ok(q and abs(q['at'] - (cur['start'] + cur['len'])) < 1e-6, 'Launch "End of the section": queued for the end of %s (beat %g)' % (cur['name'], cur['start'] + cur['len']), q)
    press(R, 29); pg.wait_for_timeout(200); ok(not J(R, "play.on") and J(R, "P1C.q") is None and J(R, "P1C.qT") == 0, 'Stop clears the queue')
    R("p1Set('sq','bar')")
    # a pad launches and selects its track
    k = (lit[0] - 36) % 8; r = 7 - ((lit[0] - 36) >> 3); R("selectTrack(%s)" % json.dumps(row[(k + 1) % 8]['id']))
    msg(R, [0x90, lit[0], 100], [0x80, lit[0], 0]); pg.wait_for_timeout(300)
    ok(J(R, "selT") == row[k]['id'] and J(R, "play.on") and secs[r]['start'] <= J(R, "curBeat()") < secs[r]['start'] + 2, 'a pad selects its track and launches its section', (J(R, "selT"), J(R, "curBeat()")))
    R("VO=[];{const o=voiceOn;voiceOn=function(t,p,v){VO.push(p);return o.apply(this,arguments)}}0"); msg(R, [0x90, 36, 100], [0x80, 36, 0]); ok(J(R, "VO") == [], 'pads in Session do not play notes')
    ok(J(R, "!!P1C.iv"), 'while playing in Session the follower runs')
    press(R, 85); pg.wait_for_timeout(300); ok(not J(R, "play.on") and not J(R, "P1C.iv"), 'stopped: the follower stops')
    # scrolling and encoders
    R("FAKEMIDI.sent.length=0"); press(R, 47); L = lines(R)
    ok(J(R, "[...CTL.devs.values()][0].p1.so") == 1 and L.get(3, '').startswith(secs[1]['name'][:8]), 'Down arrow: the grid starts one section later', L.get(3))
    press(R, 46); press(R, 45); ok(J(R, "[...CTL.devs.values()][0].p1.b.tb") == tb + 1, 'Right arrow: one track later')
    press(R, 44); tr = J(R, "p1bRow([...CTL.devs.values()][0]).map(t=>t.id)"); i = tr.index(bass); v0 = J(R, "S.tracks.find(t=>t.id===%s).vol" % json.dumps(bass))
    msg(R, *[[0xB0, 71 + i, 127]] * 6); ok(J(R, "S.tracks.find(t=>t.id===%s).vol" % json.dumps(bass)) < v0, 'encoders: the volume of the track above them')
    # a learned mapping on a scene button wins
    R("ctlG().maps.push({id:'mS',dev:'Ableton Push',type:'cc',ch:0,num:43,target:'ms',min:0,max:1,take:'jump',enc:'abs',fb:false});ctlDirty()")
    press(R, 43); ok(not J(R, "play.on"), 'a learned mapping on a scene button wins'); R("ctlG().maps=ctlG().maps.filter(m=>m.id!=='mS');ctlDirty()")
    # Note: back
    R("selectTrack(%s)" % json.dumps(bass)); R("FAKEMIDI.sent.length=0"); press(R, 50); L = lines(R)
    ok(not J(R, "[...CTL.devs.values()][0].p1.ses") and 'Morph' in L.get(0, '') and btns(R).get(51) == 1 and set(btns(R).get(36 + r) for r in range(8)) == {0}, 'Note: back to the device and the note grid, scene buttons dark', L.get(0))
    R("VO.length=0"); msg(R, [0x90, 36, 100], [0x80, 36, 0]); ok(len(J(R, "VO")) == 1, 'the pads play notes again')
    # no sections
    R("window.__ss=S.sections;S.sections=[]"); press(R, 51); L = lines(R); ok('No sections yet' in L.get(2, '') and set(leds(R).values()) == {0}, 'a song without sections: the display says so, pads dark', L.get(2)); R("S.sections=__ss"); press(R, 50)
    # the Controllers page
    press(R, 51); R("ctlPage()"); pg.wait_for_timeout(200)
    s = J(R, "(()=>{const e=document.querySelector('#ctlWin .p1set select[data-p1c=sq]');return e?{v:e.value,t:e.title,lt:e.closest('label').title,o:[...e.options].map(o=>o.textContent)}:null})()")
    ok(s and s['v'] == 'bar' and s['t'] and s['lt'] and s['o'] == ['Next bar', 'End of the section', 'At once'], 'the Controllers page has the Launch setting, with tooltips', s)
    pg.locator('#ctlWin select[data-p1c=sq]').select_option('now'); ok(J(R, "UI.p1.sq") == 'now' and 'At once' in lines(R).get(2, ''), 'a change there is kept (UI.p1.sq) and shown on the Push')
    h = J(R, "document.querySelector('#ctlWin .p1help').textContent"); ok('Session' in h and '—' not in h, 'the guide mentions Session, no em dash')
    R("p1Set('sq','bar')")
    pg.screenshot(path=os.path.join(OUT, 'c2c_page.png'))
    # idle
    R("window.__to=0;window.__ts=[];{const o=setTimeout;window.setTimeout=function(f,ms){__to++;__ts.push(String(f).slice(0,80)+' '+ms);return o.apply(this,arguments)}}{const o=setInterval;window.setInterval=function(f,ms){__to++;__ts.push('iv '+String(f).slice(0,80));return o.apply(this,arguments)}}"); pg.wait_for_timeout(1500)
    mine = J(R, "__ts.filter(x=>/p1|P1|ctl|CTL/.test(x))")
    ok(not mine and not J(R, "P1C.iv") and not J(R, "P1C.qT"), 'nothing of the Push runs while stopped and still (%d timers of the app itself in 1.5 s)' % J(R, "__to"), mine)
    R("FAKEMIDI.sent.length=0;dispatchEvent(new Event('pagehide'))"); bb = btns(R)
    ok(36 in bb and set(bb.values()) == {0} and set(pads(R).values()) == {0}, 'page hidden: scene buttons and pads dark')
    ok(not logs, 'no console errors', logs)
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
