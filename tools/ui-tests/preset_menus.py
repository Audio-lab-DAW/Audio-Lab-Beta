"""Preset library, part 1 (v0.191): the preset menu of every synth in the page.
python3 tools/ui-tests/preset_menus.py [index.html] [out dir]
For every instrument: the device is shown, its preset menu has groups (Init first), every entry has a tooltip, presets made for
psytrance carry the mark, choosing an entry applies it and the menu keeps its groups afterwards, no dash characters.
Two menus are shown opened as a list (size=24) and saved as pictures, because a native drop-down is not part of a screenshot."""
import sys, os, json, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
out = sys.argv[2] if len(sys.argv) > 2 else '.'
al = AudioLab(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); al.start()
print('errors after load', al.errors)
INSTS = ['saw', 'square', 'pad', 'strings', 'pluck', 'keys', 'sub', 'bass', 'reese', 'plant', 'wtab', 'acid', 'venom', 'growl', 'vfm', 'orb']
bad = []
for inst in INSTS:
    al.build({'bpm': 120, 'tracks': [{'name': 'T', 'preset': inst, 'clips': [{'start': 0, 'len': 4, 'notes': [{'p': 60, 's': 0, 'l': 1, 'v': .8}]}]}]})
    al.run("selT=S.tracks[0].id;renderFx();1"); al.page.wait_for_timeout(500)
    r = json.loads(al.run("""(()=>{const s=document.querySelector('#fxin select[data-s=ipre]');if(!s)return JSON.stringify({none:1});
      const g=[...s.querySelectorAll('optgroup')].map(x=>x.label+' '+x.children.length),o=[...s.options];
      return JSON.stringify({groups:g,n:o.length,table:Object.keys(IPRE['%s'][0]).length,notip:o.filter(x=>!x.title).map(x=>x.value),psy:o.filter(x=>/· psy$/.test(x.textContent)).length,
        psyg:(s.querySelector('optgroup[label=Psytrance]')||{children:[]}).children.length,first:(s.querySelector('optgroup')||{}).label,
        dash:/[\\u2013\\u2014]/.test(o.map(x=>x.textContent+x.title).join('')),seltitle:s.title})})()""" % inst))
    if r.get('none'): bad.append(inst + ': no preset menu'); print(inst, 'NO MENU'); continue
    print('%-8s %3d presets in %d groups (first %s): %s; psytrance group %d, marked elsewhere %d; no tooltip %s; dash %s' % (inst, r['n'], len(r['groups']), r['first'], ', '.join(r['groups']), r['psyg'], r['psy'], r['notip'], r['dash']))
    if r['n'] != r['table']: bad.append('%s: menu shows %d of %d' % (inst, r['n'], r['table']))
    if r['first'] != 'Init': bad.append(inst + ': Init is not first')
    if r['notip']: bad.append(inst + ': presets without tooltip ' + str(r['notip']))
    if r['dash']: bad.append(inst + ': dash character')
    # choose the third preset through the menu: applied, menu rebuilt with groups
    k = al.run("Object.keys(IPRE['%s'][0])[2]" % inst)
    al.run("(()=>{const s=document.querySelector('#fxin select[data-s=ipre]');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()" % k)
    al.page.wait_for_timeout(400)
    r2 = json.loads(al.run("JSON.stringify({ipk:S.tracks[0].inst.ipk,g:document.querySelectorAll('#fxin select[data-s=ipre] optgroup').length,v:(document.querySelector('#fxin select[data-s=ipre]')||{}).value})"))
    if r2['ipk'] != k or r2['v'] != k or r2['g'] < 2: bad.append('%s: choosing %s gave %s' % (inst, k, r2))
    if inst in ('plant', 'saw'):
        al.run("(()=>{const s=document.querySelector('#fxin select[data-s=ipre]');s.size=26;s.style.height='auto';s.style.position='fixed';s.style.left='20px';s.style.top='20px';s.style.zIndex=99999;s.style.width='300px';s.style.background='#15171d';s.style.color='#e8ebf2';return 1})()")
        al.page.wait_for_timeout(300); al.page.screenshot(path=os.path.join(out, 'presets_menu_%s.png' % inst), clip={'x': 10, 'y': 10, 'width': 330, 'height': 470})
print('page errors', al.errors)
print('PROBLEMS', bad if bad else 'none')
al.stop()
