"""Preset library, part 2: the preset menus of the drums, percussion, samplers, particle instruments, FX, Grid, Sub, Psy Bass, Bounce,
the Kick designer's own menu, a drum pad's kick menu and the Bouncy Notes menu.
python3 tools/ui-tests/preset_menus2.py [index.html] [out dir]
Checks: groups with Init first, every entry has a tooltip, no dash characters, the menu shows every preset (the Kick designer: all but
the hidden one), choosing an entry applies it and the menu keeps its groups. Pictures of the Kick designer and Drum kit menus opened."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
out = sys.argv[2] if len(sys.argv) > 2 else '.'
al = AudioLab(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); al.start()
print('errors after load', al.errors)
INSTS = ['kick', 'zsnare', 'zclap', 'zhat', 'ztom', 'perc', 'drums', 'sampler', 'emit', 'vgrain', 'sfx', 'grid', 'sbass', 'psyb', 'bball']
bad = []
def menu(sel, table):
    return json.loads(al.run("""(()=>{const s=document.querySelector('#fxin %s');if(!s)return JSON.stringify({none:1});
      const g=[...s.querySelectorAll('optgroup')].map(x=>x.label+' '+x.children.length),o=[...s.options];
      return JSON.stringify({groups:g,n:o.length,table:%s,notip:o.filter(x=>!x.title).map(x=>x.value),psy:o.filter(x=>/· psy$/.test(x.textContent)).length,
        first:(s.querySelector('optgroup')||{}).label,dash:/[\\u2013\\u2014]/.test(o.map(x=>x.textContent+x.title).join('')),seltitle:s.title})})()""" % (sel, table)))
def check(name, r, want_init=True):
    if r.get('none'): bad.append(name + ': no menu'); print(name, 'NO MENU'); return
    print('%-10s %3d presets in %2d groups (first %s): %s; marked psy outside the group %d; no tooltip %s; dash %s' % (name, r['n'], len(r['groups']), r['first'], ', '.join(r['groups']), r['psy'], r['notip'], r['dash']))
    if r['n'] != r['table']: bad.append('%s: menu shows %d of %d' % (name, r['n'], r['table']))
    if want_init and r['first'] != 'Init': bad.append(name + ': Init is not first')
    if r['notip']: bad.append(name + ': presets without tooltip ' + str(r['notip']))
    if r['dash']: bad.append(name + ': dash character')
for inst in INSTS:
    al.build({'bpm': 120, 'tracks': [{'name': 'T', 'preset': inst, 'clips': [{'start': 0, 'len': 4, 'notes': [{'p': 60, 's': 0, 'l': 1, 'v': .8}]}]}]})
    al.run("selT=S.tracks[0].id;renderFx();1"); al.page.wait_for_timeout(500)
    if inst == 'kick':
        sel, tb = 'select[data-s=kpre]', "Object.keys(KPRE).filter(k=>!(PSMETA.kick[k]||{}).h).length"
    else:
        sel, tb = 'select[data-s=ipre]', "Object.keys(IPRE['%s'][0]).length" % inst
    check(inst, menu(sel, tb))
    k = al.run("Object.keys(%s)[3]" % ('KPRE' if inst == 'kick' else "IPRE['%s'][0]" % inst))
    al.run("(()=>{const s=document.querySelector('#fxin %s');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()" % (sel, k))
    al.page.wait_for_timeout(400)
    r2 = json.loads(al.run("JSON.stringify({ipk:S.tracks[0].inst.%s,g:document.querySelectorAll('#fxin %s optgroup').length,v:(document.querySelector('#fxin %s')||{}).value})" % ('kp' if inst == 'kick' else 'ipk', sel, sel)))
    if r2['ipk'] != k or r2['v'] != k or r2['g'] < 2: bad.append('%s: choosing %s gave %s' % (inst, k, r2))
    if inst == 'drums':
        al.run("S.tracks[0].inst.psel=0;S.tracks[0].inst.pads[0].type='kick';renderFx();1"); al.page.wait_for_timeout(300)
        check('pad kick', menu('select[data-s=pkp]', "Object.keys(KPRE).filter(k=>!(PSMETA.kick[k]||{}).h).length"))
    if inst in ('kick', 'drums'):
        s2 = sel
        al.run("(()=>{const s=document.querySelector('#fxin %s');s.size=30;s.style.height='auto';s.style.position='fixed';s.style.left='20px';s.style.top='20px';s.style.zIndex=99999;s.style.width='320px';s.style.background='#15171d';s.style.color='#e8ebf2';return 1})()" % s2)
        al.page.wait_for_timeout(300); al.page.screenshot(path=os.path.join(out, 'presets_menu_%s.png' % inst), clip={'x': 10, 'y': 10, 'width': 350, 'height': 540})
# Bouncy Notes: an effect in front of Soft keys
al.build({'bpm': 120, 'tracks': [{'name': 'T', 'preset': 'keys', 'fx': [{'type': 'bnotes'}], 'clips': [{'start': 0, 'len': 4, 'notes': [{'p': 60, 's': 0, 'l': 1, 'v': .8}]}]}]})
al.run("selT=S.tracks[0].id;renderFx();1"); al.page.wait_for_timeout(500)
check('bnotes', menu('select[data-x=pre]', 'Object.keys(FXPRE.bnotes).length'), want_init=False)
print('page errors', al.errors)
print('PROBLEMS', bad if bad else 'none')
al.stop()
