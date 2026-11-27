"""Task ST-S1 (settings rebuild, step S1): remove the copies inside Settings.
- Interface: the Mixer block's second Level meters list (4 selects) goes; the Level meters block right below it is the one home.
  The mixer's gear popover keeps its short list for now (task S14 turns it into a link).
- Interface and DAC: the always-hidden old 'Profile' select (dacSel) and its hidden card go, with the dead DACS table and dacCard().
  The value UI.dac stays: 'Device profile' on the same page uses it.
- Interface and DAC: the second 'Audio devices' button becomes a link to Audio system, where the output device and the one Audio devices button live.
- Export audio: the second Save, Save as, Open row goes; a link line points to Project file, the home of the three buttons.
Not touched: the Refraction slider and switch inside Glass & light (the glass chain's task G4 removes them with the old glass keys).
  python3 tools/edits/taskST_S1.py [index.html]"""
import sys
P=sys.argv[1] if len(sys.argv)>1 else 'index.html'
s=open(P,encoding='utf-8').read()
def rep(old,new,count=1):
    global s
    n=s.count(old)
    assert n==count,(n,old[:120])
    s=s.replace(old,new)

# 1. Mixer block in Settings: no second Level meters list
rep("""<h5>Level meters</h5><div class="mxsm">${Object.entries(MXSM)""","""${adv?'':`<h5>Level meters</h5><div class="mxsm">${Object.entries(MXSM)""")
rep("""<option value="${v}">${t}</option>`).join('')}</select></label>`).join('')}</div>
<h5>Fader and meter design</h5>""","""<option value="${v}">${t}</option>`).join('')}</select></label>`).join('')}</div>`}
<h5>Fader and meter design</h5>""")

# 2. the hidden old DAC profile select and card
rep("""          <div hidden><h4>Device profile</h4>
          <div class="cprow"><span>Profile</span><select id="dacSel"><option value="">None</option><option value="gryphon">iFi xDSD Gryphon</option><option value="ams24">Zoom AMS-24</option></select></div>
          <div id="dacCard"></div></div>
""","")
a=s.index("const DACS={gryphon:");b=s.index("function cpSync(){",a)
assert s.count("const DACS={")==1 and 'dacApply' in s[a:b] and s[a:b].count('function ')==1
s=s[:a]+s[b:]
rep("$('#dacSel').value=UI.dac||'';","")
rep("${ctx.state}`:'–';dacCard()}","${ctx.state}`:'–'}")
rep(";$('#dacSel').onchange=e=>{UI.dac=e.target.value;saveUI();dacCard()};",";")
assert 'dacCard' not in s and 'dacSel' not in s and 'DACS' not in s

# 3. the second Audio devices button: a link to the page that holds the output device and the one button
rep("""<button type="button" id="ifdDevs" title="Every input and output at a glance: pick, test, see rates and channels">Audio devices</button>""",
    """<button type="button" id="ifdDevs" data-pmgo="audio" title="The output device and the Audio devices window are on Audio system. This opens that page.">Change output</button>""")
rep("""  $i('ifdDevs').onclick=()=>audDevOpen();""","""  /* ifdDevs is a link to Audio system (data-pmgo), task ST-S1 */""")

# 4. Export audio: no second Save, Save as, Open
rep("""        <h4>Save project</h4><div class="pfbtns"><button class="pri" data-pf="save">Save <kbd>⌘S</kbd></button><button data-pf="as">Save as .audiolab… <kbd>⇧⌘S</kbd></button><button data-pf="open">Open… <kbd>⌘O</kbd></button></div>
""","""        <p class="pmlink" title="Save, Save as and Open have one home in Settings: the Project file page. They are also in the logo menu and on ⌘S, ⇧⌘S and ⌘O.">Save the project as a .audiolab file: <button type="button" data-pmgo="files" title="Open the Project file page with Save, Save as and Open">Project file</button></p>
""")
rep("""document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('[data-pf]');if(!b)return;const k=b.dataset.pf;if(k==='open')openProjectFile();else writeProject(curP(),k==='as')});""","")
assert 'data-pf=' not in s

# 5. search: the old names stay findable (page words)
rep("""dac:'bit perfect dac interface mode rate balance""","""dac:'audio devices change output bit perfect dac interface mode rate balance""")
rep("files:'save autosave file folder'","files:'save save as open audiolab project autosave file folder'")
open(P,'w',encoding='utf-8').write(s);print('ok')
