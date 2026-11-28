"""Task XT-DL5: UI rules, hide and rename a control, the right-click Advanced entries (docs/extensions-plan.md 9.6 b, 9.7 DL5; pick K12a).
Fails when a right-click entry does not name its control or sits outside the marked Advanced group, when the first use does not explain
what happens and how to undo it, when a hidden control's command stops working, when a protected control can be hidden, when a rule is
lost on restart or cannot be undone from What is changed, or when anything is added with no rule at all.
  python3 tools/ui-tests/taskXT_DL5.py [index.html] [out dir]"""
# for: task XT-DL5 (lane H)
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('dl5')){sessionStorage.setItem('dl5','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1,xtWsSeen:1,wsShow:false}))}"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.split('?')[0].endswith('/') else r.fulfill(status=404, body='')))
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    def ready(t=2500):
        pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(t)
    def menu():
        return J("ctxm.hidden?null:{adv:!!ctxm.querySelector('.ovgl.adv'),advText:(ctxm.querySelector('.ovgl.adv')||{}).textContent||'',rows:[...ctxm.querySelectorAll('button[data-i]')].map(b=>({l:b.querySelector('.mlab')?b.querySelector('.mlab').firstChild.textContent:b.textContent,dis:b.disabled,tip:b.dataset.tip||''})),html:ctxm.innerHTML.length}")
    def rclick(sel, i=0):
        R("closeMenu()"); el = pg.locator(sel).nth(i); el.scroll_into_view_if_needed(); bb = el.bounding_box()
        pg.mouse.click(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2, button='right'); pg.wait_for_timeout(250); return menu()
    def click_row(label):
        i = J("[...ctxm.querySelectorAll('button[data-i]')].findIndex(b=>b.textContent.startsWith(%s))" % json.dumps(label)); assert i >= 0, label
        pg.locator('#ctxm button[data-i]').nth(i).click(); pg.wait_for_timeout(250)
    vis = lambda sel: J("(()=>{const e=document.querySelector(%s);return!!e&&getComputedStyle(e).display!=='none'})()" % json.dumps(sel))
    pg.goto('https://app.test/'); ready()
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 316), 'version 0.316 or later', R('VERSION'))
    ok(J("!document.getElementById('xtRulesCss')&&UI.xtRules===undefined&&XT_RL.hid.size===0&&XT_RL.ren.size===0&&!document.querySelector('[data-xtren]')"), 'with no rules: no stylesheet, no rule, no rename (nothing added)')
    ok(J("XT_SAFE.K.includes('xtRules')"), 'safe mode sets the rules aside, and Reset my customisations covers them')
    ok(J("typeof XT_HOOKS.rules.items==='function'&&XT_HOOKS.rules.items(XTCI.get('transport.loop')).length===3"), 'the hook for lane F (OV3) gives the Advanced entries of a control')
    # a control with no menu of its own: the Loop button
    m = rclick('#bLoop')
    ok(m and m['adv'] and 'Advanced' in m['advText'], 'right-click the Loop button: a menu with the marked Advanced group', m and m['advText'])
    L = [r['l'] for r in (m or {'rows': []})['rows']]
    ok('Hide the Loop button' in L and 'Customise the Loop button…' in L, 'the entries name the control: Hide the Loop button, Customise the Loop button…', L)
    ok(all(r['tip'] and 'Advanced' in r['tip'] for r in m['rows'] if r['l'].startswith(('Hide the', 'Customise the'))), 'each entry has a tooltip that says it is advanced')
    pg.screenshot(path=os.path.join(OUT, 'xt_dl5_menu_loop.png'))
    # a control with its own menu: Play keeps its entries, the group comes after them
    m = rclick('#bPlay'); L = [r['l'] for r in m['rows']]
    ok(len(L) > 2 and L[-2] == 'Hide the Play button' and L[-1] == 'Customise the Play button…' and m['adv'], 'right-click Play: its own menu, then the Advanced group last', L[:3] + L[-2:])
    # the track header: the track menu plus the group, for every track
    m = rclick('#hdrin .hdr [data-a=mute]'); L = [r['l'] for r in m['rows']]
    ok('Hide the track Mute button' in L and any('every track' in r['tip'] for r in m['rows']), 'right-click a track Mute button: the track menu with "Hide the track Mute button" (on every track)', L[-2:])
    pg.screenshot(path=os.path.join(OUT, 'xt_dl5_menu_track.png'))
    # protected: Record
    m = rclick('#bRec'); row = [r for r in m['rows'] if r['l'] == 'Hide the Record button']
    ok(row and row[0]['dis'] and 'Protected' in row[0]['tip'], 'the Record button is protected: its Hide entry is off and says why', row)
    ok(not J("xtRuleSet('transport.record',{hide:true}).ok") and vis('#bRec'), 'a protected control cannot be hidden by a rule either')
    # first use: explained, then hidden
    m = rclick('#bLoop'); click_row('Hide the Loop button')
    d = J("$('#cdlg').hidden?null:{t:$('#cdT').textContent,p:$('#cdP').textContent}")
    ok(d and 'Advanced' in d['t'] and 'Loop button' in d['t'] and 'advanced' in d['p'] and 'What is changed' in d['p'] and 'shortcut' in d['p'], 'the first use explains: advanced, what disappears, the key still works, how to bring it back', d)
    pg.screenshot(path=os.path.join(OUT, 'xt_dl5_first_use.png'))
    pg.click('#cdB .pri'); pg.wait_for_timeout(300)
    ok(not vis('#bLoop') and J("UI.xtRules.layouts.all.some(o=>o.id==='transport.loop'&&o.hide===true)&&!!document.getElementById('xtRulesCss')"), 'the Loop button is hidden, the rule stored by its id')
    c0 = J("S.loop"); R("runCommand('transport.loop')"); pg.wait_for_timeout(150); c1 = J("S.loop"); R("runCommand('transport.loop')"); pg.wait_for_timeout(150)
    ok(c0 != c1, 'hidden is not gone: its command still works', (c0, c1))
    # second use: no dialog
    rclick('#hdrin .hdr [data-a=mute]'); click_row('Hide the track Mute button')
    ok(J("$('#cdlg').hidden") and J("[...document.querySelectorAll('#hdrin .hdr [data-a=mute]')].every(e=>getComputedStyle(e).display==='none')"), 'after the first use no question; the Mute button is hidden on every track')
    R("renderHeaders()"); pg.wait_for_timeout(200)
    ok(J("[...document.querySelectorAll('#hdrin .hdr [data-a=mute]')].length>2&&[...document.querySelectorAll('#hdrin .hdr [data-a=mute]')].every(e=>getComputedStyle(e).display==='none')"), 'still hidden after the headers are built again')
    # rename
    ok(J("xtRuleSet('transport.tap',{rename:'Tap <b>it</b> now'}).ok"), 'a rename is accepted and cleaned of markup')
    R("trApply()"); pg.wait_for_timeout(150)
    t = J("({t:$('#bTap').textContent,ti:$('#bTap').title,a:$('#bTap').getAttribute('aria-label')})")
    ok(t['t'] == 'Tap bit/b now' and t['ti'].startswith(t['t']) and t['a'] == t['t'], 'the renamed Tap button shows the name, its tooltip and spoken name follow, also after the transport bar is rebuilt', t)
    ok(not J("xtRuleSet('transport.tap',{rename:'x'.repeat(25)}).ok"), 'a name longer than 24 characters is refused')
    m = rclick('#bTap'); L = [r['l'] for r in m['rows']]
    ok('Hide the Tap tempo button' in L and any(t['t'] in r['tip'] for r in m['rows']), 'a renamed control keeps its own name in the menu, the tooltip says its new name', L[-2:])
    R("closeMenu()")
    # an unknown id is kept and changes nothing
    R("UI.xtRules.layouts.all.push({id:'transport.fromTheFuture',hide:true});saveUINow();xtRulesApply()")
    ok(J("UI.xtRules.layouts.all.length===4&&XT_RL.bad.length===1"), 'a rule with an unknown id is kept and ignored')
    # What is changed lists them, ✕ undoes one
    R("runCommand('view.whatIsChanged')"); pg.wait_for_timeout(400)
    rows = J("[...document.querySelectorAll('#xtWs .xtcr')].map(r=>r.textContent)")
    ok(sum('control rule' in r for r in rows) == 4 and any('not used' in r for r in rows) and any('Loop button' in r and 'hidden' in r for r in rows), 'What is changed lists every rule, the unknown one as not used', [r[:60] for r in rows])
    ok('—' not in J("$('#xtWs .xtchg').textContent"), 'no em dash')
    pg.screenshot(path=os.path.join(OUT, 'xt_dl5_changed.png'))
    pg.click('#xtWs [data-xc=x][data-id="xtr:transport.loop"]'); pg.wait_for_timeout(200)
    ok(vis('#bLoop') and not J("UI.xtRules.layouts.all.some(o=>o.id==='transport.loop')"), '✕ brings the Loop button back')
    R("xtWsClose()")
    # restart keeps the rules
    pg.reload(); ready()
    ok(J("[...document.querySelectorAll('#hdrin .hdr [data-a=mute]')].every(e=>getComputedStyle(e).display==='none')") and J("$('#bTap').textContent.startsWith('Tap')&&!!$('#bTap').dataset.xtren"), 'after a restart the rules are applied again')
    ok(vis('#bLoop'), 'the Loop button stays back')
    # Customise: show it again, put back
    R("setTimeout(()=>xtRuleCustom(XTCI.get('track.mute')),0)"); pg.wait_for_timeout(250)  # a hidden control cannot be right-clicked: What is changed or the hook
    d = J("{t:$('#cdT').textContent,b:[...$('#cdB').children].map(b=>b.textContent)}")
    ok('Advanced' in d['t'] and 'Show it again' in d['b'] and 'Put it back as it came' in d['b'] and 'Rename…' in d['b'], 'Customise is marked Advanced and offers Rename, Show it again, Put it back', d)
    pg.locator('#cdB button', has_text='Show it again').click(); pg.wait_for_timeout(200)
    ok(J("[...document.querySelectorAll('#hdrin .hdr [data-a=mute]')].every(e=>getComputedStyle(e).display!=='none')"), 'Show it again brings the Mute buttons back')
    R("xtRuleSet('transport.tap',{rename:null})"); R("trApply()"); pg.wait_for_timeout(150)
    ok(J("!$('#bTap').dataset.xtren&&!document.querySelector('[data-xtren]')"), 'removing the rename gives the Tap button its own words back')
    R("UI.xtRules&&(UI.xtRules.layouts.all=UI.xtRules.layouts.all.filter(o=>o.id!=='transport.fromTheFuture'));if(UI.xtRules&&!UI.xtRules.layouts.all.length)delete UI.xtRules;saveUINow();xtRulesApply()")
    ok(J("!document.getElementById('xtRulesCss')&&UI.xtRules===undefined"), 'with every rule gone, the stylesheet is gone too')
    R("document.body.classList.add('lite')"); m = rclick('#bLoop'); pg.screenshot(path=os.path.join(OUT, 'xt_dl5_menu_light.png')); R("closeMenu()")
    ok(m and m['adv'], 'the group shows in Light mode too')
    ok(not errs, 'no console errors', errs[:4])
    b.close()
print('%d of %d checks passed' % (N[1], N[0]))
if FAIL: sys.exit(1)
