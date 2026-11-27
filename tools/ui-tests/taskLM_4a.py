"""Task LM-4a (lane M, Learn): the lesson runner and the four psytrance lessons (LM_LESSONS).
Walks every lesson headless on the Fractals song: for each step the check is made false, the lesson is started at that step,
the target control must be found and visible and the card must not cover it, the check must be false, then the step's action
(the user's own move, or "Do it for me") must make it pass and move on. Also: "already done" skips, Esc ends, nothing is
blocked (a real click on the metronome works during a lesson), "Do it for me" is one undo step, a lesson without actions
changes nothing in the song, nothing exists or runs while no lesson runs, progress in UI.lm, the first-run offer.
  python3 tools/ui-tests/taskLM_4a.py [index.html] [out dir]"""
import sys, os, json, re
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
import tempfile
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(tempfile.gettempdir(), 'out_LM_4a'); os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('lm4a')){sessionStorage.setItem('lm4a','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
BASS = "LM_G.pump(LM_G.trk('bass'))"
# per lesson: [unset (makes the check false; None = nothing), action ('doit' = the card's button by mouse, 'click:<sel>' = the user clicks, JS = the user's move)]
WALK = {
 'lm.rollingBass': [
   ["setBpm(120)", 'doit'],
   ["play.on&&toggle()", 'doit'],
   ["play.on&&toggle();pos=160;{const c=LM_G.clip(LM_G.trk('bass'));c.notes=c.notes.filter(n=>n.s>=(c.off||0)+1);c.notes.push({p:33,s:(c.off||0),l:.2,v:1})}", 'doit'],
   ["LM_G.trk('bass').inst.d=0.3", 'doit'],
   [None, "LM_G.trk('bass').inst.cut=1200"]],
 'lm.sidechain': [
   ["play.on&&toggle()", 'doit'],
   [BASS + ".f.on=false", 'doit'],
   [BASS + ".f.p.depth=20", 'doit'],
   [BASS + ".f.p.shape=90", 'doit'],
   [None, "(async()=>{const f=" + BASS + ".f;f.on=false;await new Promise(r=>setTimeout(r,450));f.on=true})()"]],
 'lm.filterBuild': [
   ["S.loop=false;S.loopRange=null;syncTransportUI()", 'doit'],
   ["LM_G.trk('bass').inst.cut=900", 'doit'],
   ["UI.autoRec=false;paSyncBtn();LM_G.trk('bass').autoArm=false;renderHeaders()", 'doit'],
   ["play.on&&toggle()", 'doit'],
   ["{const t=LM_G.trk('bass');for(const k of Object.keys(S.pauto||{}))if(k.includes(t.id))delete S.pauto[k]}",
    "{const t=LM_G.trk('bass');S.pauto=S.pauto||{};S.pauto['c:'+t.id+':cut']=[{b:544,v:.08},{b:552,v:.3},{b:562,v:.62},{b:572,v:.9}]}"],
   [None, 'doit']],
 'lm.mixDrop': [
   ["play.on&&toggle();S.loop=false;S.loopRange=null;syncTransportUI()", 'doit'],
   ["for(const t of S.tracks)t.solo=false;renderHeaders()", 'doit'],
   ["{const t=LM_G.trk('kick');t.vol=.12;changed(false);LM_RUN.pk=[]}", 'kick'],
   [None, 'doit'],
   [None, 'bass'],
   [BASS + ".f.p.depth=10", 'doit']]}
UNDO_FIX = {'tempo', 'roll', 'decay', 'pumpOn', 'depth', 'release', 'dark', 'soloKick', 'unsolo', 'pumpCheck'}
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body=''))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(6000)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    def W(c, t=15000):
        for _ in range(t // 100):
            if J('!!(' + c + ')'): return True
            pg.wait_for_timeout(100)
        raise TimeoutError(c)
    SONG = "JSON.stringify(S,(k,v)=>k==='work'?undefined:v)"
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 276), 'version 0.276 or later', R('VERSION'))
    ok(J("S.tracks.some(t=>t.name==='Bass')&&S.bpm===145"), 'the Fractals song is open')
    # --- the data ---
    L = J("LM_LESSONS.map(l=>({id:l.id,t:l.title,n:l.steps.length,s:l.steps.map(s=>({al:s.al,alt:s.alt||[],want:s.want||null,check:s.check,live:s.live||null,fix:s.fix||null,cmd:s.command||null,t:s.t,b:s.b,must:!!s.mustAct}))}))")
    ok([l['id'] for l in L] == ['lm.rollingBass', 'lm.sidechain', 'lm.filterBuild', 'lm.mixDrop'], 'four psytrance lessons: rolling bass, sidechain, filter build, mixing a drop')
    ok(all(4 <= l['n'] <= 6 for l in L), 'each lesson has 4 to 6 steps', [l['n'] for l in L])
    alls = [s for l in L for s in l['s']]
    bad = [a for s in alls for a in [s['al']] + s['alt'] if not J("XTCI.has(%s)" % json.dumps(a))]
    ok(not bad, 'every step names a released control id (CONTROLS, data-al), never a position or selector', bad)
    ok(all(J("typeof LM_CHECK[%s]==='function'" % json.dumps(s['check'])) for s in alls), 'every step has a state check')
    ok(all((not s['fix'] or J("typeof LM_FIX[%s]==='function'" % json.dumps(s['fix']))) and (not s['live'] or J("typeof LM_LIVE[%s]==='function'" % json.dumps(s['live']))) for s in alls), 'every fix and live line exists')
    ok(all(not s['cmd'] or J("xtCommandId(%s)===%s" % (json.dumps(s['cmd']), json.dumps(s['cmd']))) for s in alls), 'commands are released command ids (COMMANDS, runCommand)')
    ok(not [s for s in alls if '—' in s['t'] + s['b']] and not [l for l in L if '—' in l['t']], 'no em dash in the lesson text')
    ok(sum(1 for s in alls if s['must']) == 2, 'two steps need a fresh move (mustAct): Cutoff moved, pump switched twice')
    # --- nothing while idle ---
    pg.wait_for_timeout(7000)
    ok(J("!document.getElementById('lmg')&&!document.getElementById('lmgO')&&LM_RUN.tm===0&&!LM_RUN.les"), 'no lesson: nothing in the page, no timer; the first-run offer never shows under automation')
    ok(J("typeof LM_HOOKS.point==='function'&&typeof ovGuide==='undefined'"), 'until lane F releases ovGuide the stand-in pointer is used through LM_HOOKS.point')
    # --- a lesson without any action changes nothing in the song ---
    R("setBpm(120)"); R("UNDO.pop()"); s0 = J(SONG); u0 = J("UNDO.length")
    R("lmLsStart('lm.rollingBass')"); pg.wait_for_timeout(900); R("lmLsAct('skip')"); pg.wait_for_timeout(500); R("lmLsAct('back')"); pg.wait_for_timeout(500); R("lmLsEnd()")
    ok(J(SONG) == s0 and J("S.bpm") == 120 and J("UNDO.length") == u0, 'a lesson run with Skip and Back but no action leaves the song and undo as they were')
    R("setBpm(145)"); R("UNDO.pop()")
    # --- already done ---
    R("lmLsStart('lm.rollingBass')")
    ok(J("LM_RUN.already&&LM_RUN.i===0") and 'Already done' in J("document.querySelector('#lmg .lmgC').innerText"), 'a step already true (tempo 145) says "Already done"')
    W("LM_RUN.i===1", 4000); ok(J("LM_RUN.i") == 1, 'and moves on by itself')
    # --- nothing blocked ---
    m0 = J("$('#bClick').getAttribute('aria-pressed')"); pg.click('#bClick'); m1 = J("$('#bClick').getAttribute('aria-pressed')"); pg.click('#bClick')
    ok(m0 != m1, 'during a lesson a real click on the metronome works (nothing is blocked)', (m0, m1))
    ok(J("getComputedStyle(document.getElementById('lmg')).pointerEvents==='none'&&getComputedStyle(document.querySelector('#lmg .lmgR')).pointerEvents==='none'"), 'the ring and leader let every click through; only the card takes the pointer')
    # --- Esc ---
    pg.mouse.move(800, 500); pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok(J("!LM_RUN.les&&!document.getElementById('lmg')&&LM_RUN.tm===0"), 'Esc ends the lesson; nothing stays in the page, no timer')
    # --- walk every step of every lesson ---
    for l in L:
        for i, st in enumerate(l['s']):
            unset, act = WALK[l['id']][i]
            if unset: R(unset)
            if act in ('kick', 'bass'): pg.wait_for_timeout(1800)  # the meter settles on the new level before the step starts
            R("lmLsStart(%s,%d)" % (json.dumps(l['id']), i)); pg.wait_for_timeout(350)
            name = '%s %d/%d (%s)' % (l['t'], i + 1, l['n'], st['check'])
            ok(J("!LM_RUN.already&&!lmLsCheck(LM_RUN.les.steps[LM_RUN.i])"), name + ': false before the action')
            geo = J("(()=>{const st=LM_RUN.les.steps[LM_RUN.i],e=lmLsFind(st),c=document.querySelector('#lmg .lmgC');if(!e||!c)return null;const a=e.getBoundingClientRect(),q=c.getBoundingClientRect();return{al:e.dataset.al,hit:!(q.right<=a.left||q.left>=a.right||q.bottom<=a.top||q.top>=a.bottom),inv:q.left>=0&&q.top>=0&&q.right<=innerWidth&&q.bottom<=innerHeight}})()")
            ok(geo and geo['al'] in [st['al']] + st['alt'] and not geo['hit'] and geo['inv'], name + ': points at its control, visible; the card does not cover it and stays in the window', geo)
            u0 = J("UNDO.length")
            if act == 'doit':
                ok(J("!!document.querySelector('#lmg [data-lg=doit]')"), name + ': offers "Do it for me"'); pg.click('#lmg [data-lg=doit]')
            elif act.startswith('click:'): pg.click(act[6:] if act != 'doit' else '#hdrin .hdr[data-id="%s"] [data-a=aar]' % J("LM_G.trk('bass').id"))
            elif act in ('kick', 'bass'):
                # the user drags the fader while watching the master peak (real playback and the real meter)
                for k in range(6):
                    pg.wait_for_timeout(1700)
                    pk = J("LM_G.peak()")
                    if J("LM_RUN.les&&LM_RUN.ok||!LM_RUN.les||LM_RUN.i!==%d" % i): break
                    if act == 'kick': R("{const t=LM_G.trk('kick');t.vol=Math.min(2,t.vol*Math.pow(10,(-6-(%f))/20));changed(false)}" % max(pk, -40))
                    else: R("{const k=LM_G.trk('kick'),t=LM_G.trk('bass');t.vol=Math.min(t.vol,k.vol*Math.pow(10,-3/20));if(%f>=-1.5)t.vol*=.7;changed(false)}" % pk)
            else: R(act)
            W("!LM_RUN.les||LM_RUN.les.id!==%s||LM_RUN.i>%d" % (json.dumps(l['id']), i))
            ok(True, name + ': passes after its action and moves on', J("LM_G.peak()") if act in ('kick', 'bass') else '')
            if act == 'doit' and st['fix'] in UNDO_FIX:
                ok(J("UNDO.length") == u0 + 1, name + ': "Do it for me" is one undo step', (u0, J("UNDO.length")))
            if i == 0 and l['id'] == 'lm.rollingBass': pg.screenshot(path=os.path.join(OUT, 'lm4a_step.png'))
        ok(J("!LM_RUN.les") and J("UI.lm.p[%s]" % json.dumps(l['id'])) == 'done', l['t'] + ': finished, progress kept in UI.lm')
        R("play.on&&toggle()")
    ok(J("LM_HOOKS.progress()") == '4 of 4 done', 'quiet progress: "4 of 4 done"', J("LM_HOOKS.progress()"))
    pg.wait_for_timeout(400); ok(J("(JSON.parse(localStorage.getItem('audiolab-ui')||'{}').lm||{p:{}}).p['lm.mixDrop']") == 'done', 'UI.lm is saved with the UI')
    # undo the last Do it for me restores the song state
    R("for(const t of S.tracks)t.solo=false"); u0 = J("UNDO.length"); R("lmLsStart('lm.mixDrop',1)"); pg.wait_for_timeout(300); pg.click('#lmg [data-lg=doit]'); pg.wait_for_timeout(300)
    ok(J("LM_G.soloOnly(LM_G.trk('kick'))"), 'Do it for me solos the kick'); R("lmLsEnd()"); R("undo()")
    ok(J("LM_G.noSolo()") and J("UNDO.length") == u0, 'one undo puts it back')
    # --- the first-run offer ---
    ok(J("lmLsOffer(true)") and J("document.querySelectorAll('#lmgO .lmgRow').length") == 4, 'the first-run offer lists the four lessons')
    ok('4 of 4 done' in J("document.getElementById('lmgO').textContent"), 'with quiet progress ("4 of 4 done", ticks)', J("document.getElementById('lmgO').textContent")[:40])
    pg.screenshot(path=os.path.join(OUT, 'lm4a_offer.png'))
    pg.click('#lmgO [data-lo="lm.sidechain"]'); pg.wait_for_timeout(300)
    ok(J("LM_RUN.les&&LM_RUN.les.id==='lm.sidechain'&&!document.getElementById('lmgO')"), 'choosing one starts it and closes the offer')
    R("document.body.classList.add('lite')"); pg.wait_for_timeout(300); pg.screenshot(path=os.path.join(OUT, 'lm4a_lite.png'))
    ok(J("getComputedStyle(document.querySelector('#lmg .lmgC')).boxShadow==='none'"), 'Light mode: the card draws flat'); R("document.body.classList.remove('lite')"); R("lmLsEnd()")
    ok(not errs, 'no console errors', errs[:4])
    b.close()
print('%d of %d checks passed' % (N[1], N[0]))
sys.exit(1 if FAIL else 0)
