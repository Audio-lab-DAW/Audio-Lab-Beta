"""Task ST-S10 (settings rebuild, step S10): the Audio page with one copy of device, buffer and rate, the Control Panel folded in, a Running
now read-out, and "Keep?" for device, rate and buffer (D1b). taskST_S10_block.js before askChoice, taskST_S10_css.txt before .dacv, the
output select's handler reports a switch (ST_HOOKS.outChanged) and names the system's sound settings on a Mac and on Windows, the output list
leaves out Windows' 'communications' entry (as the Audio devices window does), the version line.
  python3 tools/edits/taskST_S10.py [index.html] [version]"""
import sys,os,re
H=os.path.dirname(os.path.abspath(__file__));P=sys.argv[1] if len(sys.argv)>1 else 'index.html';V=sys.argv[2] if len(sys.argv)>2 else '0.288'
B=open(os.path.join(H,'taskST_S10_block.js'),encoding='utf-8').read().replace("v0.288","v"+V).replace("{v:'0.288'}","{v:'"+V+"'}")
C=open(os.path.join(H,'taskST_S10_css.txt'),encoding='utf-8').read().replace("v0.288","v"+V)
s=open(P,encoding='utf-8').read()
assert 'const STS10=' not in s and 'const STS9=' in s
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
rep('function askChoice(title,text,btns,icon){',B.rstrip('\n')+'\nfunction askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;',C.rstrip('\n')+'\n.dacv{display:flex;')
rep("""  ensureCtx();const help='Pick the Zoom AMS-24 or the Gryphon in the macOS Sound menu (menu bar); this app follows the system output.';
  if(!ctx.setSinkId){toast('This browser cannot switch outputs itself. '+help);outSel.value='';return}
  try{await ctx.setSinkId(outSel.value);UI.sink=outSel.value;saveUI();toast('Output switched to '+outSel.selectedOptions[0].textContent+'.')}catch(e){toast('The browser blocked the switch here. '+help);outSel.value=''}""",
"""  ensureCtx();const help=typeof ST10HELP==='function'?ST10HELP():'Choose the output in the system\\'s sound settings; AudioLab then follows the system output.',prev=UI.sink||'';/* task ST-S10: both systems named, the choice before stays on a failure, a switch is reported */
  if(!ctx.setSinkId){toast('This browser cannot switch outputs itself. '+help);outSel.value=prev;return}
  try{await ctx.setSinkId(outSel.value);UI.sink=outSel.value;saveUI();toast('Output switched to '+outSel.selectedOptions[0].textContent+'.');try{if(typeof ST_HOOKS==='object'&&ST_HOOKS.outChanged)ST_HOOKS.outChanged(prev,UI.sink||'')}catch(err){}}catch(e){toast('The browser blocked the switch here. '+help);outSel.value=prev}""")
rep("const outs=ds.filter(d=>d.kind==='audiooutput'&&d.deviceId!=='default'&&d.deviceId);","const outs=ds.filter(d=>d.kind==='audiooutput'&&d.deviceId!=='default'&&d.deviceId!=='communications'&&d.deviceId);")
rep("""Switching the device\\'s rate from here needs the newest app build. Until then, set it in Audio MIDI Setup and keep""","""Switching the device\\'s rate from here needs the newest app build. Until then, set it in the system\\'s sound settings (Audio MIDI Setup on a Mac, Sound settings on Windows) and keep""")
m=re.findall(r"const VERSION='([0-9.]+)'",s);assert len(m)==1
rep("const VERSION='"+m[0]+"'","const VERSION='"+V+"'")
open(P,'w',encoding='utf-8').write(s);print('ok',m[0],'->',V)
