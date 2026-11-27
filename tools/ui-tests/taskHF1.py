"""Task HF1: controllers can never drive AudioLab by themselves; lkSel is the look colour again; the update window keeps its buttons in view.
Fake Web MIDI in Chromium (the real desktop app is covered by tools/release-gate/smoke_electron.js):
 - a port named like a Push 1 is a plain device until it is turned on as a control surface: nothing is sent to it, its buttons run nothing
 - turned on, with a port that echoes what it gets (a MIDI loop): no track, selection or transport change, the device is stopped with a notice
 - an echo of what AudioLab sent within 50 ms is ignored, a note-off never; a flood stops the device
 - Stop all controllers: nothing read, nothing sent, kept in UI; the command is in the list
 - lkSel(a) returns a colour (the linked-clips helper is ftLinkSel); the update window with 40 long lines: buttons in view, newest first, at most 8
  python3 tools/ui-tests/taskHF1.py [index.html] [out dir]"""
import sys, os, json
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
FAKE = r"""(()=>{const F=window.FAKEMIDI={sent:[],loop:{}};const acc={inputs:new Map(),outputs:new Map(),onstatechange:null,sysexEnabled:true};
 F.plug=(name)=>{const i={id:'in-'+name,name,manufacturer:'Fake',type:'input',state:'connected',onmidimessage:null};
   const o={id:'out-'+name,name,manufacturer:'Fake',type:'output',state:'connected',send(d){const a=Array.from(d);F.sent.push({port:name,data:a});if(F.loop[name]&&F.sent.length<5000)setTimeout(()=>{if(i.onmidimessage)i.onmidimessage({data:new Uint8Array(a)})},2)}};
   acc.inputs.set(i.id,i);acc.outputs.set(o.id,o);if(acc.onstatechange)acc.onstatechange({port:i})};
 F.msg=(name,b)=>{const i=acc.inputs.get('in-'+name);if(i&&i.onmidimessage)i.onmidimessage({data:new Uint8Array(b)})};
 Object.defineProperty(navigator,'requestMIDIAccess',{configurable:true,value:()=>Promise.resolve(acc)})})()"""
INIT = "if(!sessionStorage.getItem('hf1')){sessionStorage.setItem('hf1','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.add_init_script(INIT + ';' + FAKE)
    pg.route('https://app.test/**', lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') or r.request.url.endswith('index.html') else r.fulfill(status=404, body=''))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=60000); pg.wait_for_timeout(2500)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 261), 'version 0.261 or later', R('VERSION'))
    ok(J("typeof lkSel(.5)") == 'string' and J("lkSel(.5)").startswith('rgba(') and J("Array.isArray(ftLinkSel())"), 'lkSel(a) is the selection colour again, ftLinkSel() the linked clips', J("lkSel(.5)"))
    R("openDemoFractals()"); pg.wait_for_timeout(7000); R("ctlStart()"); pg.wait_for_timeout(300)
    SNAP = "S.tracks.map(t=>t.name+(t.mute?'M':'')+(t.solo?'S':'')).join(',')+'|'+selT+'|'+play.on+'|'+S.tracks.length"
    s0 = R(SNAP)
    R("FAKEMIDI.loop['Ableton Push']=1;FAKEMIDI.plug('Ableton Push')"); pg.wait_for_timeout(600)
    d = J("(d=>({prof:d.prof.id,cand:d.cand&&d.cand.id}))([...CTL.devs.values()].find(x=>x.name==='Ableton Push'))")
    ok(d == {'prof': 'generic', 'cand': 'push1'}, 'a port named like a Push 1 is a plain device until it is turned on as a surface', d)
    ok(J("FAKEMIDI.sent.length") == 0, 'nothing is sent to it', J("FAKEMIDI.sent.length"))
    R("FAKEMIDI.msg('Ableton Push',[0xB0,85,127]);FAKEMIDI.msg('Ableton Push',[0xB0,88,127]);FAKEMIDI.msg('Ableton Push',[0xB0,46,127])"); pg.wait_for_timeout(300)
    ok(R(SNAP) == s0, 'its Play, Duplicate and arrow buttons run nothing', R(SNAP))
    R("ctlSurfSet('Ableton Push',true)"); pg.wait_for_timeout(2500)
    h = J("[...CTL.devs.values()].find(x=>x.name==='Ableton Push').halt")
    ok(R(SNAP) == s0, 'turned on with a port that echoes (a loop): no track, selection, transport or track count change', R(SNAP))
    ok(h == 'loop', 'the looping device is stopped', h)
    ok('MIDI loop' in R("$('#toast').textContent"), 'with a notice', R("$('#toast').textContent"))
    n = J("FAKEMIDI.sent.length"); pg.wait_for_timeout(500); ok(J("FAKEMIDI.sent.length") == n, 'nothing more is sent to it', (n, J("FAKEMIDI.sent.length")))
    # echoes and note-offs on a plain keyboard
    R("FAKEMIDI.plug('Keys')"); pg.wait_for_timeout(300)
    e = J("(()=>{const d=[...CTL.devs.values()].find(x=>x.name==='Keys');ctlEcho([0xB0,20,5]);ctlEcho([0x90,60,0]);const a=ctlGuard(d,[0xB0,20,5]),b=ctlGuard(d,[0x90,60,0]),c=ctlGuard(d,[0xB0,20,6]);return[a,b,c]})()")
    ok(e == [True, False, False], 'an echo within 50 ms is ignored; a note-off and anything else are not', e)
    f = J("(()=>{const d=[...CTL.devs.values()].find(x=>x.name==='Keys');d.rate=null;for(let i=0;i<1600;i++)ctlGuard(d,[0xB0,1,i&127]);return d.halt})()")
    ok(f == 'flood', 'a device sending over 1500 messages a second is stopped', f)
    # Stop all controllers
    R("ctlStopAll(true)"); pg.wait_for_timeout(200)
    ok(J("UI.ctlStop") == 1 and J("[...CTL.devs.values()].every(d=>ctlOff(d))"), 'Stop all controllers: every device off, kept in UI')
    ok(J("!!SCM.get('ctl.stopAll')"), 'Stop all controllers is in the command list')
    R("SCM.get('ctl.mappings').run()"); pg.wait_for_timeout(500)
    ok(J("!!document.querySelector('[data-hf=stop]')&&document.querySelector('[data-hf=stop]').textContent==='Start controllers'"), 'the Controllers page has the switch (Start controllers while stopped)')
    ok(J("document.querySelectorAll('input[data-hf=surf]').length") >= 2, 'every device has a Control surface switch', J("document.querySelectorAll('input[data-hf=surf]').length"))
    pg.screenshot(path=os.path.join(OUT, 'hf1_controllers.png'))
    R("ctlStopAll(false)"); pg.wait_for_timeout(200); ok(J("UI.ctlStop") == 0, 'and on again')
    R("SCM.get('closewins').run();if(play.on)stop()")
    # the update window
    long = "\n".join('Line %d: %s' % (i + 1, 'a long note about what changed, ' * 12) for i in range(40))
    for w, hgt in ((1600, 1000), (1024, 640)):
        pg.set_viewport_size({'width': w, 'height': hgt}); pg.wait_for_timeout(300)
        R("localStorage.removeItem('al-upd-later');UYW.closed='';uywShow({kind:'ota',to:'9.999',notes:%s});if(!UYW.open)uywOpen(true)" % json.dumps(long)); pg.wait_for_selector('#uywM .uywb button', timeout=5000); pg.wait_for_timeout(400)
        c = pg.evaluate("""()=>{const m=document.getElementById('uywM');const bs=[...m.querySelectorAll('.uywb button')].map(b=>{const r=b.getBoundingClientRect(),h=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return r.bottom<=innerHeight&&r.top>=0&&!!h&&(h===b||b.contains(h))});
          return{bs,li:m.querySelectorAll('.uywnl li').length,first:m.querySelector('.uywnl li').textContent.slice(0,7),more:(m.querySelector('.uywnl li.more')||{}).textContent||''}}""")
        ok(c['bs'] and all(c['bs']) and c['li'] == 9 and c['first'] == 'Line 1:' and '32' in c['more'], 'update window %dx%d: Later and Restart now in view and clickable; newest first, 8 shown and "32 earlier"' % (w, hgt), c)
        if w == 1024: pg.screenshot(path=os.path.join(OUT, 'hf1_update_window.png'))
        R("uywClose()")
    ok(not errs, 'no page errors', errs[:3])
    b.close()
print('\n%d checks, %d failed' % (N[0], N[0] - N[1]))
for f in FAIL: print('  FAIL', f)
sys.exit(1 if FAIL else 0)
