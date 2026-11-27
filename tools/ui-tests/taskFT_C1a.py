#!/usr/bin/env python3
"""Task FT-C1a (v0.230): the controller layer, tested with a fake MIDI device (a stub of navigator.requestMIDIAccess with SysEx,
injected before the page loads) that sends messages and records what AudioLab sends back.
   python3 tools/ui-tests/taskFT_C1a.py [index.html] [out dir]"""
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

with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 230), 'version 0.230 or later', v)
    s = J(R, "{ctl:typeof CTL,start:typeof ctlStart,hook:typeof FT_HOOKS.controllersPage,a:SCM.get('ctl.learn')&&SCM.get('ctl.learn').d,b:!!SCM.get('ctl.mappings'),al:SCM.get('learn')===SCM.get('ctl.learn'),started:CTL.started,asked:FAKEMIDI.asked.length}")
    ok(s['ctl'] == 'object' and s['start'] == 'function' and s['hook'] == 'function', 'the controller layer is there, with the hook FT_HOOKS.controllersPage for lane B', s)
    ok(s['a'] == 'Mod+L' and s['b'] and s['al'], 'commands ctl.learn (Mod+L) and ctl.mappings; the old id learn is an alias of ctl.learn', s)
    ok(not s['started'] and s['asked'] == 0, 'in a browser that never allowed MIDI nothing asks for it at the start (as before)', s)
    # ---- the old links are read once into global mappings ----
    kn = J(R, "[...document.querySelectorAll('#fxin .kn[data-c^=\"fx:\"],#fxin .vb[data-c^=\"fx:\"]')].filter(e=>e.offsetWidth&&e.dataset.c.split(':').length===3).slice(0,4).map(e=>e.dataset.c)")
    ok(len(kn) >= 3, 'the device panel shows knobs to map', kn)
    R("UI.midiMap={'0:7':%s};delete UI.ctl;0" % json.dumps(kn[2]))
    m = J(R, "(ctlG(),UI.ctl.maps.map(m=>[m.dev,m.type,m.ch,m.num,m.target,m.take,m.scope]))")
    ok(m == [['*', 'cc', 0, 7, kn[2], 'jump', 'global']], 'the old link "channel 1, CC 7" becomes a global mapping for any device, jump as before', m)
    ok(J(R, "UI.midiMap") == {'0:7': kn[2]}, 'the old UI.midiMap is kept for an older build')
    ok(J(R, "(ctlG(),UI.ctl.maps.length)") == 1, 'read only once')
    # ---- start: SysEx asked, devices found, output paired ----
    R("FAKEMIDI.plug('Fake Keys','Fakeco')"); R("initMidi()"); pg.wait_for_timeout(300)
    s = J(R, "{asked:FAKEMIDI.asked,sx:CTL.sysex,devs:[...CTL.devs.values()].map(d=>[d.name,d.prof.id,d.out&&d.out.name]),seen:UI.ctlSeen}")
    ok(s['asked'] == [True] and s['sx'], 'MIDI is asked for with SysEx', s)
    ok(s['devs'] == [['Fake Keys', 'generic', 'Fake Keys']], 'the device is found, generic profile, its output paired by name', s)
    ok(s['seen'] == 1, 'remembered, so the next start finds the devices without a click')
    R("FAKEMIDI.plug('MIDIIN2 (Pad Thing)','Pads','MIDIOUT2 (Pad Thing)')"); pg.wait_for_timeout(100)
    s = J(R, "[...CTL.devs.values()].map(d=>[d.name,d.out&&d.out.name])")
    ok(['MIDIIN2 (Pad Thing)', 'MIDIOUT2 (Pad Thing)'] in s, 'plugged in later: found; Windows names "MIDIIN2 (x)" and "MIDIOUT2 (x)" paired', s)
    ok('Controller connected' in R("$('#toast').textContent"), 'a toast says a controller was connected', R("$('#toast').textContent"))
    R("FAKEMIDI.unplug('MIDIIN2 (Pad Thing)')"); pg.wait_for_timeout(100)
    ok(J(R, "CTL.devs.size") == 1 and 'unplugged' in R("$('#toast').textContent"), 'unplugged: gone, with a toast')
    # ---- a generic device behaves as before ----
    R("window.NOTES=[];window.CCL=[];{const o=noteOn;noteOn=function(p,v,k){NOTES.push([p,+v.toFixed(3),k]);return o.apply(this,arguments)};const c=ccLive;ccLive=function(k,v){CCL.push([String(k),+(+v).toFixed(4)]);return c.apply(this,arguments)}}0")
    R("FAKEMIDI.msg('Fake Keys',[0x90,60,100])"); R("FAKEMIDI.msg('Fake Keys',[0x80,60,0])")
    ok(J(R, "NOTES") == [[36, round(100 / 127, 3), 'm60']], 'a note plays the selected track as before (note 60 is noteOn(36), key m60)', J(R, "NOTES"))
    ok(J(R, "LIVE.has('m60')") is False, 'and stops on note off')
    R("FAKEMIDI.msg('Fake Keys',[0xB0,64,127])"); R("FAKEMIDI.msg('Fake Keys',[0xE0,0,64])"); R("FAKEMIDI.msg('Fake Keys',[0xB0,64,0])")
    ok(J(R, "CCL") == [['64', 1], ['pb', round((64 << 7) / 16383, 4)], ['64', 0]], 'controller moves and pitch bend go to the recorded lanes and the sustain pedal as before', J(R, "CCL"))
    # the migrated mapping (any device, CC 7, jump) moves its knob
    R("FAKEMIDI.msg('Fake Keys',[0xB0,7,0])"); n0 = J(R, "(C=>C.spec.n(C.get()))(CT.get(%s))" % json.dumps(kn[2]))
    R("FAKEMIDI.msg('Fake Keys',[0xB0,7,127])"); n1 = J(R, "(C=>C.spec.n(C.get()))(CT.get(%s))" % json.dumps(kn[2]))
    ok(n0 < .01 and n1 > .99, 'the old link still moves its knob (jump)', (n0, n1))
    # ---- learn: click a knob, move a CC ----
    R("midiLearn(true)"); ok(J(R, "document.body.classList.contains('mlearn')"), 'learn on')
    el = pg.locator('#fxin [data-c=%s]' % json.dumps(kn[0])).first; el.click(); pg.wait_for_timeout(100)
    ok(J(R, "ML.sel") == kn[0], 'clicking a knob in learn picks it', J(R, "ML.sel"))
    pg.screenshot(path=os.path.join(OUT, 'c1a_learn.png'))
    R("FAKEMIDI.msg('Fake Keys',[0xB0,21,40])")
    m = J(R, "UI.ctl.maps.filter(m=>m.target===%s).map(m=>[m.dev,m.type,m.ch,m.num,m.take,m.enc,m.fb])" % json.dumps(kn[0]))
    ok(m == [['Fake Keys', 'cc', 0, 21, 'pickup', 'abs', True]], 'learned: Fake Keys CC 21, pick up, absolute, feedback on', m)
    ok('Linked CC 21 (channel 1) on Fake Keys' in R("$('#toast').textContent"), 'the toast names the message, device and control', R("$('#toast').textContent"))
    ok(J(R, "[...document.querySelectorAll('[data-c].mmap')].map(e=>e.dataset.c).includes(%s)" % json.dumps(kn[0])), 'the mapped knob is marked in learn mode')
    R("midiLearn(false)")
    # ---- pick up ----
    K = json.dumps(kn[0]); nv = lambda: J(R, "+(C=>C.spec.n(C.get()))(CT.get(%s)).toFixed(4)" % K)
    R("(C=>{C.set(C.spec.v(.5));paintSel(%s)})(CT.get(%s))" % (K, K)); start = nv()
    for x in (10, 20, 30, 40): R("FAKEMIDI.msg('Fake Keys',[0xB0,21,%d])" % x)
    ok(abs(nv() - start) < .005, 'pick up: the knob far below the control does not move it', (start, nv()))
    for x in (50, 60, 70): R("FAKEMIDI.msg('Fake Keys',[0xB0,21,%d])" % x)
    ok(abs(nv() - 70 / 127) < .01, 'pick up: once the knob passes the control it follows', nv())
    R("(C=>{C.set(C.spec.v(.2));paintSel(%s)})(CT.get(%s))" % (K, K)); R("FAKEMIDI.msg('Fake Keys',[0xB0,21,72])")
    ok(abs(nv() - .2) < .01, 'moved with the mouse: the knob has to catch it again', nv())
    # ---- scale ----
    mid = J(R, "UI.ctl.maps.find(m=>m.target===%s).id" % K); R("ctlEdit(%s,{take:'scale'})" % json.dumps(mid))
    R("(C=>{C.set(C.spec.v(.3));paintSel(%s)})(CT.get(%s))" % (K, K))
    seq = []
    for x in range(64, 128, 8): R("FAKEMIDI.msg('Fake Keys',[0xB0,21,%d])" % x); seq.append(nv())
    R("FAKEMIDI.msg('Fake Keys',[0xB0,21,127])"); seq.append(nv())
    ok(all(seq[i] <= seq[i + 1] + 1e-6 for i in range(len(seq) - 1)) and seq[1] > .3 and seq[-1] > .99, 'scale: the control moves up with the knob, more slowly, and meets it at the top', seq)
    R("FAKEMIDI.msg('Fake Keys',[0xB0,21,64])"); ok(abs(nv() - 64 / 127) < .01, 'scale: after they met it follows the knob', nv())
    # ---- jump and range ----
    R("ctlEdit(%s,{take:'jump',min:.25,max:.75})" % json.dumps(mid)); R("FAKEMIDI.msg('Fake Keys',[0xB0,21,0])"); a = nv(); R("FAKEMIDI.msg('Fake Keys',[0xB0,21,127])"); bb = nv()
    ok(abs(a - .25) < .01 and abs(bb - .75) < .01, 'jump with a range of 25 to 75 %', (a, bb))
    R("ctlEdit(%s,{min:.75,max:.25})" % json.dumps(mid)); R("FAKEMIDI.msg('Fake Keys',[0xB0,21,0])")
    ok(abs(nv() - .75) < .01, 'a reversed range turns the knob around', nv())
    R("ctlEdit(%s,{min:0,max:1})" % json.dumps(mid))
    # ---- relative encoders ----
    for enc, steps, want in (('rel2c', [1, 1, 127, 1, 2], 1), ('relsb', [1, 1, 65, 1, 2], 1)):
        K2 = json.dumps(kn[1]); R("ctlUnmap(%s)" % K2)
        R("midiLearn(true)"); pg.locator('#fxin [data-c=%s]' % K2).first.click(); R("FAKEMIDI.msg('Fake Keys',[0xB0,30,1])"); R("midiLearn(false)")
        R("(C=>{C.set(C.spec.v(.5));paintSel(%s)})(CT.get(%s))" % (K2, K2))
        for x in steps: R("FAKEMIDI.msg('Fake Keys',[0xB0,30,%d])" % x)
        mm = J(R, "UI.ctl.maps.find(m=>m.target===%s)" % K2)
        R("(C=>{C.set(C.spec.v(.5));paintSel(%s)})(CT.get(%s))" % (K2, K2))
        for x in [1] * 5: R("FAKEMIDI.msg('Fake Keys',[0xB0,30,%d])" % x)
        up = J(R, "(C=>C.spec.n(C.get()))(CT.get(%s))" % K2)
        R("FAKEMIDI.msg('Fake Keys',[0xB0,30,%d])" % (123 if enc == 'rel2c' else 69)); dn = J(R, "(C=>C.spec.n(C.get()))(CT.get(%s))" % K2)
        ok(mm['enc'] == enc and 'auto' not in mm and abs(up - (.5 + 5 / 127)) < .006 and abs(dn - (up - 5 / 127)) < .006, 'an endless knob is recognised as %s and steps from where the control is' % enc, (mm['enc'], up, dn))
    # ---- feedback ----
    R("FAKEMIDI.sent.length=0"); R("(C=>{C.set(C.spec.v(.5));paintSel(%s)})(CT.get(%s))" % (K, K)); pg.wait_for_timeout(120)
    try: pg.wait_for_function("()=>FAKEMIDI.sent.length>0", timeout=2000)  # a busy machine can hold the 33 ms timer longer
    except Exception: pass
    fb = J(R, "FAKEMIDI.sent.map(x=>x.data)")
    ok([0xB0, 21, round(.5 * 127)] in fb, 'a mouse move of a mapped control goes back to the controller (CC 21 = 64)', fb)
    R("FAKEMIDI.sent.length=0")
    R("window.__CT=CT;window.__ps=paintSel;0")
    pg.evaluate("""()=>new Promise(res=>{let i=0;const C=__CT.get(%s),t=setInterval(()=>{C.set(C.spec.v((i%%100)/100));__ps(%s);if(++i>=150){clearInterval(t);setTimeout(res,100)}},2)})""" % (K, K))
    sent = J(R, "FAKEMIDI.sent.map(x=>x.t)"); dur = (sent[-1] - sent[0]) / 1000 if len(sent) > 1 else 0
    ok(len(sent) >= 2 and (len(sent) - 1) / max(dur, .001) <= 31, 'feedback at most 30 messages a second while dragging', (len(sent), round(dur, 3)))
    R("FAKEMIDI.sent.length=0"); R("FAKEMIDI.msg('Fake Keys',[0xB0,21,90])"); pg.wait_for_timeout(120)
    ok(J(R, "FAKEMIDI.sent.length") == 0, 'no echo of the controller\'s own move', J(R, "FAKEMIDI.sent"))
    ok(J(R, "CTL.fbT") == 0, 'nothing pending when idle (no timer)')
    # ---- notes as switches, pitch bend ----
    R("midiLearn(true)"); pg.locator('#fxin [data-c=%s]' % json.dumps(kn[3])).first.click(); R("FAKEMIDI.msg('Fake Keys',[0x90,48,100])"); R("midiLearn(false)"); R("FAKEMIDI.msg('Fake Keys',[0x80,48,0])")
    R("NOTES.length=0"); K3 = json.dumps(kn[3])
    R("(C=>{C.set(C.spec.v(0));paintSel(%s)})(CT.get(%s))" % (K3, K3)); R("FAKEMIDI.msg('Fake Keys',[0x90,48,100])"); R("FAKEMIDI.msg('Fake Keys',[0x80,48,0])"); a = J(R, "(C=>C.spec.n(C.get()))(CT.get(%s))" % K3)
    R("FAKEMIDI.msg('Fake Keys',[0x90,48,100])"); bb = J(R, "(C=>C.spec.n(C.get()))(CT.get(%s))" % K3)
    ok(abs(a - 1) < .01 and bb < .01 and J(R, "NOTES") == [], 'a learned note switches its control between its ends and does not play', (a, bb, J(R, "NOTES")))
    R("FAKEMIDI.msg('Fake Keys',[0x90,50,90])"); ok(J(R, "NOTES.length") == 1, 'other notes still play'); R("FAKEMIDI.msg('Fake Keys',[0x80,50,0])")
    # ---- project scope ----
    R("midiLearn(true)"); pg.locator('#fxin [data-c=%s]' % json.dumps(kn[2])).first.click(modifiers=['Shift']); R("FAKEMIDI.msg('Fake Keys',[0xB0,7,10])"); R("midiLearn(false)")
    s = J(R, "{p:S.ctl&&S.ctl.v,pm:S.ctl&&S.ctl.maps.map(m=>[m.num,m.target]),g:UI.ctl.maps.filter(m=>m.num===7).length}")
    ok(s['p'] == 1 and s['pm'] == [[7, kn[2]]], 'Shift-click learns into this project only (S.ctl, version 1)', s)
    ok(s['g'] == 1, 'the global CC 7 link stays for other projects', s)
    R("ctlEdit(UI.ctl.maps.find(m=>m.num===7).id,{target:%s})" % json.dumps(kn[1]))
    R("(C=>{C.set(C.spec.v(.5));paintSel(%s)})(CT.get(%s))" % (json.dumps(kn[1]), json.dumps(kn[1])))
    R("S.ctl.maps[0].take='jump'"); R("FAKEMIDI.msg('Fake Keys',[0xB0,7,127])")
    ok(J(R, "(C=>C.spec.n(C.get()))(CT.get(%s))" % json.dumps(kn[2])) > .99 and abs(J(R, "(C=>C.spec.n(C.get()))(CT.get(%s))" % json.dumps(kn[1])) - .5) < .01, 'for the same message the project mapping wins over the global one')
    js = J(R, "JSON.parse(JSON.stringify(S)).ctl")
    ok(js and js['v'] == 1 and len(js['maps']) == 1, 'saved with the project', js)
    R("undo()"); pg.wait_for_timeout(200); ok(J(R, "!S.ctl||S.ctl.maps.length===0"), 'undo takes the project mapping back')
    # ---- device switch ----
    R("UI.ctlOff={'Fake Keys':1};NOTES.length=0"); R("FAKEMIDI.msg('Fake Keys',[0x90,60,100])")
    ok(J(R, "NOTES.length") == 0, 'a device switched off is ignored'); R("UI.ctlOff={}")
    # ---- pinned window: learn reaches it, mapping names the panel's control ----
    pb = pg.locator('#fxin .dev[data-d=fx] .pinbtn').first
    if pb.count():
        pb.click(); pg.wait_for_timeout(800)
        pk = J(R, "(e=>e&&e.dataset.c)([...document.querySelectorAll('.pinw [data-c^=\"pn:\"]')].find(e=>e.offsetWidth&&e.classList.contains('kn')))")
        if pk:
            R("midiLearn(true)"); pg.locator('.pinw [data-c=%s]' % json.dumps(pk)).first.click(); R("FAKEMIDI.msg('Fake Keys',[0xB0,40,0])"); R("midiLearn(false)")
            t = J(R, "(UI.ctl.maps.find(m=>m.num===40)||{}).target")
            ok(t and not t.startswith('pn:') and pk.endswith(':' + t), 'learn in a pinned window maps the device\'s own control (not the window copy)', (pk, t))
            R("ctlEdit(UI.ctl.maps.find(m=>m.num===40).id,{take:'jump'})"); R("FAKEMIDI.msg('Fake Keys',[0xB0,40,0])"); o0 = J(R, "document.querySelector('.pinw [data-c=%s] output').textContent" % json.dumps(pk))
            R("FAKEMIDI.msg('Fake Keys',[0xB0,40,127])"); pg.wait_for_timeout(50); o1 = J(R, "document.querySelector('.pinw [data-c=%s] output').textContent" % json.dumps(pk))
            ok(J(R, "(C=>C.spec.n(C.get()))(CT.get(%s))" % json.dumps(pk)) > .99 and o0 != o1, 'the knob in the pinned window moves and is redrawn', (o0, o1))
            pg.screenshot(path=os.path.join(OUT, 'c1a_pinned.png'))
            R("for(const w of document.querySelectorAll('.pinw .pinun'))w.click()")
        else: ok(False, 'a knob in the pinned window')
    else: ok(True, 'no pinnable effect on this track (skipped)')
    # ---- the Controllers window ----
    R("ctlPage()"); pg.wait_for_timeout(400)
    s = J(R, "{vis:!document.getElementById('ctlWin').hidden,rows:document.querySelectorAll('#ctlWin :is(.crow,.cmr):not(.h)').length,dev:[...document.querySelectorAll('#ctlWin :is(.cdev,.cmdev) b')].map(b=>b.textContent),tips:[...document.querySelectorAll('#ctlWin .fwb button,#ctlWin .fwb select,#ctlWin .fwb input')].filter(e=>!e.title&&!e.dataset.tip).length,em:/—/.test(document.getElementById('ctlWin').textContent)}")
    ok(s['vis'] and s['rows'] == J(R, "ctlAll().length") and s['dev'] == ['Fake Keys'], 'the Controllers window lists the device and every mapping', s)
    ok(s['tips'] == 0 and not s['em'], 'every control there has a tooltip; no em dashes', s)
    pg.screenshot(path=os.path.join(OUT, 'c1a_window.png'))
    n = J(R, "ctlAll().length"); pg.locator('#ctlWin :is(.cdel,button[data-k2=del])').first.click(); pg.wait_for_timeout(100)
    ok(J(R, "ctlAll().length") == n - 1 and J(R, "document.querySelectorAll('#ctlWin :is(.crow,.cmr):not(.h)').length") == n - 1, 'delete from the list')
    sel = pg.locator('#ctlWin select:is([data-ck=take],[data-k2=take])').first; mid = sel.get_attribute('data-m'); sel.select_option('jump')
    ok(J(R, "ctlAll().find(m=>m.id===%s).take" % json.dumps(mid)) == 'jump', 'takeover changed from the list')
    R("const c=$('#liteChk');if(!c.checked){c.checked=true;c.dispatchEvent(new Event('change'))}"); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(OUT, 'c1a_window_light.png'))
    R("const c=$('#liteChk');c.checked=false;c.dispatchEvent(new Event('change'))")
    R("for(const w of document.querySelectorAll('#ctlWin .fwc'))w.click()")
    ok(J(R, "SCM.get('ctl.mappings').run(),!document.getElementById('ctlWin').hidden"), 'the command ctl.mappings opens it')
    ok(J(R, "CTL.n.in>0&&CTL.last&&CTL.last.dev==='Fake Keys'"), 'the last message is kept for the mappings page', J(R, "CTL.last"))
    ok(not logs, 'no console errors', logs)
    b.close()
    # ---- SysEx refused: plain MIDI still works ----
    b, pg, logs, R = boot(p, refuse=True)
    R("FAKEMIDI.plug('Fake Keys')"); R("initMidi()"); pg.wait_for_timeout(300)
    s = J(R, "{a:FAKEMIDI.asked,sx:CTL.sysex,n:CTL.devs.size,f:ctlSend([...CTL.devs.values()][0],[0xF0,0x47,0x7F,0xF7]),c:ctlSend([...CTL.devs.values()][0],[0xB0,1,1])}")
    ok(s['a'] == [True, False] and not s['sx'] and s['n'] == 1 and s['f'] is False and s['c'] is True, 'SysEx refused: asked again without it; devices work, SysEx is not sent', s)
    ok(not logs, 'no console errors', logs)
    b.close()
print('\n%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('  FAIL', f)
sys.exit(1 if FAIL else 0)
