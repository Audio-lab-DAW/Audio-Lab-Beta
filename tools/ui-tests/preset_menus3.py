"""Preset library, part 3: the preset menu of every effect and MIDI effect (and the Pro EQ and Chord menus).
python3 tools/ui-tests/preset_menus3.py [index.html] [out dir]
Checks per effect: the menu is there, its groups, every visible preset is in it (hidden near copies left out), every entry has a tooltip,
no dash characters in names or tooltips, choosing an entry applies its values (and the effect does not share arrays with the preset table),
a new effect starts on the first preset. Pictures of three opened menus (Compressor, Space reverb, Sidechain)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
out = sys.argv[2] if len(sys.argv) > 2 else '.'
al = AudioLab(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); al.start()
print('version', al.version, 'errors after load', al.errors)
TYPES = json.loads(al.run("JSON.stringify(Object.keys(FXPRE).filter(t=>FXDEF[t]).concat(['eq','chord']))"))
MIDI = json.loads(al.run("JSON.stringify([...MIDIFX])"))
bad = []
for t in TYPES:
    inst = 'keys'
    al.build({'bpm': 145, 'tracks': [{'name': 'T', 'preset': inst, 'fx': [{'type': t}], 'clips': [{'start': 0, 'len': 4, 'notes': [{'p': 60, 's': 0, 'l': 1, 'v': .8}]}]}]})
    al.run("(()=>{const f=S.tracks[0].fx[0];const n=mkFx('%s');S.tracks[0].fx[0]=n;selT=S.tracks[0].id;renderFx();return 1})()" % t)
    al.page.wait_for_timeout(250)
    sel = 'select.eqpre' if t == 'eq' else 'select[data-x=cp]' if t == 'chord' else 'select[data-x=pre]'
    tb = "Object.keys(EQPRE).length" if t == 'eq' else "Object.keys(CHPRE).length" if t == 'chord' else \
         "Object.keys(FXPRE['%s']).filter(k=>!((FXMETA['%s']||{})[k]||{}).h).length" % (t, t)
    r = json.loads(al.run("""(()=>{const d=document.querySelector('#fxin .dev[data-id="'+S.tracks[0].fx[0].id+'"]');const s=d&&d.querySelector('%s');if(!s)return JSON.stringify({none:1});
      const o=[...s.options].filter(x=>x.value&&x.value!=='custom');return JSON.stringify({groups:[...s.querySelectorAll('optgroup')].map(x=>x.label+' '+x.children.length),n:o.length,table:%s,
      notip:o.filter(x=>!x.title).map(x=>x.value),dash:/[\\u2013\\u2014]/.test(o.map(x=>x.textContent+x.title).join('')),cur:s.value,first:%s,psy:o.filter(x=>/psy/.test(x.textContent)).length})})()"""
                          % (sel, tb, "Object.keys(EQPRE)[0]" if t == 'eq' else "Object.keys(CHPRE)[0]" if t == 'chord' else "Object.keys(FXPRE['%s'])[0]" % t)))
    if r.get('none'): bad.append(t + ': no menu'); print('%-8s NO MENU' % t); continue
    print('%-8s %3d in the menu (%3d in the table) %2d groups: %s | no tooltip %d | starts on %s (first %s)' % (t, r['n'], r['table'], len(r['groups']), ', '.join(r['groups']), len(r['notip']), r['cur'], r['first']))
    if r['n'] != r['table']: bad.append('%s: menu shows %d of %d' % (t, r['n'], r['table']))
    if r['notip']: bad.append('%s: no tooltip on %s' % (t, r['notip'][:6]))
    if r['dash']: bad.append(t + ': dash character')
    if t not in ('eq', 'chord') and r['cur'] != r['first']: bad.append('%s: a new effect shows %s, not the first preset %s' % (t, r['cur'], r['first']))
    if t in ('eq', 'chord'): continue
    # choose the 4th visible entry and check the values
    k = json.loads(al.run("JSON.stringify(Object.keys(FXPRE['%s']).filter(k=>!((FXMETA['%s']||{})[k]||{}).h)[3])" % (t, t)))
    al.run("""(()=>{const d=document.querySelector('#fxin .dev[data-id="'+S.tracks[0].fx[0].id+'"]');const s=d.querySelector('select[data-x=pre]');s.value='%s';s.dispatchEvent(new Event('change',{bubbles:true}));return 1})()""" % k)
    al.page.wait_for_timeout(200)
    ok = json.loads(al.run("""(()=>{const f=S.tracks[0].fx[0],P=FXPRE['%s']['%s'][1];let same=f.p.pre==='%s',share=false;for(const q in P){if(JSON.stringify(P[q])!==JSON.stringify(f.p[q]))same=false;if(P[q]&&typeof P[q]==='object'&&P[q]===f.p[q])share=true}return JSON.stringify({same,share})})()""" % (t, k, k)))
    if not ok['same'] or ok['share']: bad.append('%s: choosing %s gave %s' % (t, k, ok))
# pictures of three opened menus
for t in ('comp', 'reverb', 'side'):
    al.build({'bpm': 145, 'tracks': [{'name': 'T', 'preset': 'keys', 'fx': [{'type': t}], 'clips': [{'start': 0, 'len': 4, 'notes': [{'p': 60, 's': 0, 'l': 1, 'v': .8}]}]}]})
    al.run("(()=>{S.tracks[0].fx[0]=mkFx('%s');selT=S.tracks[0].id;renderFx();return 1})()" % t); al.page.wait_for_timeout(300)
    al.run("""(()=>{const s=document.querySelector('#fxin select[data-x=pre]');s.size=34;s.style.height='auto';s.style.position='fixed';s.style.left='20px';s.style.top='20px';s.style.zIndex=99999;s.style.width='330px';s.style.fontSize='12px';s.style.background='#15171d';s.style.color='#e8e8e8';return 1})()""")
    al.page.wait_for_timeout(300); al.page.screenshot(path=os.path.join(out, 'fx_presets_menu_%s.png' % t), clip={'x': 10, 'y': 10, 'width': 360, 'height': 600})
    tip = al.run("(()=>{const s=document.querySelector('#fxin select[data-x=pre]');return [...s.options].slice(0,3).map(o=>o.textContent+': '+o.title).join(' | ')})()")
    print('tooltips of', t, ':', tip)
print('page errors', al.errors)
print('PROBLEMS', bad if bad else 'none')
al.stop()
