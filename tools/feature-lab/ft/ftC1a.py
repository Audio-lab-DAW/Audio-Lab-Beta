#!/usr/bin/env python3
"""Task FT-C1a (lane C): the controller layer. Anchored edits; re-run on a fresh index.html after a rebase.
   python3 tools/feature-lab/ft/ftC1a.py [index.html]"""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
if 'task FT-C1a' in s: sys.exit('already applied')
def rep(a, b):
    global s
    assert s.count(a) == 1, ('anchor count %d' % s.count(a), a[:120]); s = s.replace(a, b)
# 1. initMidi starts the controller service
a0 = s.index('let midiTried=false;function initMidi(){'); a1 = s.index('\n', a0)
old = s[a0:a1]; assert 'onmidimessage' in old and old.endswith('.catch(()=>{})}')
rep(old, "let midiTried=false;/* v0.233 (task FT-C1a): the controller layer (CTL, ctlStart) owns MIDI now */function initMidi(){midiTried=true;ctlStart()}")
# 2. mlMark, midiCC and the learn click use the mappings
rep("function mlMark(){const M=UI.midiMap||{},ids=new Set(Object.values(M));for(const el of document.querySelectorAll('[data-c]')){el.classList.toggle('mmap',ids.has(el.dataset.c));el.classList.toggle('msel',ML.sel===el.dataset.c)}}",
    "function mlMark(){const ids=new Set(ctlIndex().byT.keys());for(const el of document.querySelectorAll('[data-c]')){const b=ctlBid(el.dataset.c);el.classList.toggle('mmap',ids.has(b));el.classList.toggle('msel',ML.sel===b)}}")
b0 = s.index('function midiCC(ch,cc,val){const key=ch+'); b1 = s.index('\n', s.index("const id=UI.midiMap[key];if(!id)return;", b0))
old = s[b0:b1]; assert old.count('\n') == 2, old.count('\n')
rep(old, "function midiCC(ch,cc,val,d){return ctlIn(d||null,'cc',ch,cc,val)}")
rep("document.addEventListener('pointerdown',e=>{const el=e.target.closest&&e.target.closest('[data-c]');if(!el)return;ML.last=el.dataset.c;if(!ML.on)return;e.preventDefault();e.stopImmediatePropagation();if(e.altKey){const M=UI.midiMap||{};for(const k in M)if(M[k]===el.dataset.c)delete M[k];saveUI();mlMark();toast('Mapping removed');return}ML.sel=el.dataset.c;mlMark()},true);",
    "document.addEventListener('pointerdown',e=>{const el=e.target.closest&&e.target.closest('[data-c]');if(!el)return;ML.last=ctlBid(el.dataset.c);if(!ML.on)return;e.preventDefault();e.stopImmediatePropagation();if(e.altKey){toast(ctlUnmap(ML.last)?'Mapping removed':'This control has no mapping.');return}ML.sel=ML.last;ML.scope=e.shiftKey?'project':null;mlMark()},true);")
rep("toast('MIDI learn: click any knob or slider, then move a knob or fader on your controller. Alt-click removes a mapping. Press ⌘L or Esc to finish.')",
    "toast('MIDI learn: click any knob or slider, then move a knob, fader or button on your controller. Shift-click keeps the link in this project only, Alt-click removes it. Press ⌘L or Esc to finish.')")
# the learn banner without an em dash
rep("content:'MIDI LEARN — click a control, then move a knob on your controller'", "content:'MIDI LEARN: click a control, then move a knob on your controller'")
# 3. the menu gets "Controllers"
rep("act:()=>midiLearn()},\n   {label:'Undo'",
    "act:()=>midiLearn()},\n   {label:'Controllers…',sub:'MIDI devices and every mapping',ic:I('M3 6h14v8H3zM6 9v2M10 9v2M14 9v2','#b583ff'),act:()=>ctlPage()},\n   {label:'Undo'")
# 4. commands: ctl.learn (the old id 'learn' stays as an alias), ctl.mappings
rep(" {id:'learn',g:'help',l:'MIDI learn',d:'Mod+L',lock:1,ic:'M3 10h3l2-5 3 10 2-5h4',run:()=>{}},",
    " {id:'ctl.learn',g:'help',l:'MIDI learn',d:'Mod+L',lock:1,alias:['learn'],ic:'M3 10h3l2-5 3 10 2-5h4',run:()=>midiLearn()},\n {id:'ctl.mappings',g:'help',l:'Controllers and MIDI mappings',d:'',ic:'M3 6h14v8H3zM6 9v2M10 9v2M14 9v2',run:()=>ctlPage()},")
# 5. the controller layer itself, right after the commands map
blk = open(os.path.join(H, 'ftC1a_block.js'), encoding='utf-8').read().rstrip('\n')
rep("const SCM=new Map(SCA.map(a=>[a.id,a]));\n", "const SCM=new Map(SCA.map(a=>[a.id,a]));\n" + blk + "\n")
open(F, 'w', encoding='utf-8').write(s); print('FT-C1a applied')
