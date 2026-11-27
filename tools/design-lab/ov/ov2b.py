#!/usr/bin/env python3
"""Task OV2b (lane F, overlays; docs/design-round-5-overlays.md section 5, step OV2, part b): the other long menus in the picked R2.
   python3 tools/design-lab/ov/ov2b.py index.html
Needs OV2a (the engine: crow, g, kids). Adds only crow/kids keys to existing entries, so every entry keeps its command:
  - the project tab menu: Save, Rename, Duplicate, Close on the command row (Close greyed with one tab, as before);
  - the Quick actions menu (right-click the logo): Save, Open, Undo, Settings on the command row; Restart audio engine and Restart
    AudioLab in one submenu 'Restart' (Stop all sound stays in the list, one click away);
  - the device menu (right-click a device): Turn on/off, Copy, Paste, Duplicate, Delete on the command row.
Left as they are, on purpose: the mixer's menus are choosers (pan style, fader design, what each strip shows) and its channel menu
is the track menu (OV2a); the multi-track menu (lane C's tests click its entries by their text); the section menu (lane C).
New icons close and pow join OV_IC. Fixed: a menu opened during the previous menu's 60 ms fade-out (a right-click on another object
while a menu is open) was still inert when it took focus, so focus was lost and the keyboard did nothing; a press on
the menu's background (head, gaps) also moved focus out of the menu. Every anchor is asserted. Re-run on a fresh file after a rebase."""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
assert 'task OV2b' not in s, 'already applied'
assert 'task OV2a' in s, 'needs OV2a'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

# the tab menu
rep("{label:'Save',key:'⌘S',act:()=>writeProject(p,false)}", "{label:'Save',key:'⌘S',crow:'save',crowL:'Save',act:()=>writeProject(p,false)}")
rep("{label:'Rename…',act:async()=>{const n=await askText('Project name',p.name);", "{label:'Rename…',crow:'ren',crowL:'Rename',act:async()=>{const n=await askText('Project name',p.name);")
rep("{label:'Duplicate',act:()=>{const src=id===PJ.cur?S:p.S,", "{label:'Duplicate',crow:'dup',crowL:'Duplicate',act:()=>{const src=id===PJ.cur?S:p.S,")
rep("{label:'Close',act:()=>askCloseProject(id),dis:PJ.list.length<2}", "{label:'Close',crow:'close',crowL:'Close',act:()=>askCloseProject(id),dis:PJ.list.length<2}")
# the Quick actions menu
rep("{label:'Save',key:'⌘S',ic:I('M4 3h10l3 3v11H4zM7 3v5h6V3M7 17v-5h7v5','#4c8dff'),act:()=>writeProject(p,false)}",
    "{label:'Save',key:'⌘S',crow:'save',crowL:'Save',ic:I('M4 3h10l3 3v11H4zM7 3v5h6V3M7 17v-5h7v5','#4c8dff'),act:()=>writeProject(p,false)}")
rep("{label:'Open project…',key:'⌘O',ic:I('M2 6h6l2 2h8v9H2zM2 6V4h6','#4c8dff'),act:()=>openProjectFile()}",
    "{label:'Open project…',key:'⌘O',crow:'open',crowL:'Open',ic:I('M2 6h6l2 2h8v9H2zM2 6V4h6','#4c8dff'),act:()=>openProjectFile()}")
rep("{label:'Undo',key:'⌘Z',dis:!UNDO.length,ic:", "{label:'Undo',key:'⌘Z',crow:'undo',crowL:'Undo',dis:!UNDO.length,ic:")
rep("{label:'Settings…',ic:I('M10 7a3 3 0 1 0 0 6", "{label:'Settings…',crow:'set',crowL:'Settings',ic:I('M10 7a3 3 0 1 0 0 6")
rep("""   {label:'Restart audio engine',ic:I('M16 10a6 6 0 1 1-2-4.5M16 3v3.5h-3.5','#3ecf8e'),act:()=>restartAudio()},
   {label:'Restart AudioLab',sub:'reload everything, back to the splash',ic:I('M16 10a6 6 0 1 1-2-4.5M16 3v3.5h-3.5M10 8v3','#ff9a3c'),act:()=>restartApp()},""",
"""   {label:'Restart',sub:'the audio engine, or the whole app',ic:I('M16 10a6 6 0 1 1-2-4.5M16 3v3.5h-3.5','#3ecf8e'),kids:[
   {label:'Restart audio engine',ic:I('M16 10a6 6 0 1 1-2-4.5M16 3v3.5h-3.5','#3ecf8e'),act:()=>restartAudio()},
   {label:'Restart AudioLab',sub:'reload everything, back to the splash',ic:I('M16 10a6 6 0 1 1-2-4.5M16 3v3.5h-3.5M10 8v3','#ff9a3c'),act:()=>restartApp()}]},""")
# the device menu
rep("{label:f.on?'Turn off':'Turn on',act:()=>{pushUndo();f.on=!f.on;", "{label:f.on?'Turn off':'Turn on',crow:'pow',crowL:f.on?'Turn off':'Turn on',on:!!f.on,act:()=>{pushUndo();f.on=!f.on;")
rep("{label:'Copy device',sub:'With all its settings',act:", "{label:'Copy device',crow:'copy',crowL:'Copy',sub:'With all its settings',act:")
rep("{label:'Paste after this',dis:!DEVCLIP,act:", "{label:'Paste after this',crow:'paste',crowL:'Paste',dis:!DEVCLIP,act:")
rep("{label:'Duplicate',act:()=>{pushUndo();t.fx.splice(i+1,0,cloneFx(f));", "{label:'Duplicate',crow:'dup',crowL:'Duplicate',act:()=>{pushUndo();t.fx.splice(i+1,0,cloneFx(f));")
rep("{label:'Delete',danger:1,act:()=>{pushUndo();t.fx.splice(i,1);", "{label:'Delete',danger:1,crow:'del',crowL:'Delete',act:()=>{pushUndo();t.fx.splice(i,1);")

# a menu opened during the previous one's 60 ms fade-out (OV1) was still inert when it took focus: focus got lost, the keyboard did nothing
rep("""  ctxm.style.left='100px';ctxm.style.top='100px';
  ctxm.hidden=false;""", """  ctxm.style.left='100px';ctxm.style.top='100px';
  if(ctxm.inert||ctxm.classList.contains('ovout')){ctxm.inert=false;ctxm.classList.remove('ovout')}/* task OV2b: not inert while the last menu fades */
  ctxm.hidden=false;""")

JS = r"""/* task OV2b (lane F, overlays, pick R2): two more command-row icons (the tab menu's Close, the device menu's on/off). */
/* a press on the menu's background (head, gaps, separators) keeps keyboard focus in the menu */
ctxm.addEventListener('mousedown',e=>{if(!(e.target.closest&&e.target.closest('button,input,select,textarea')))e.preventDefault()});
Object.assign(OV_IC,{close:'M5 5l10 10M15 5 5 15',pow:'M10 3v7M6.2 5.6a6 6 0 1 0 7.6 0'});
"""
rep('function askChoice(title,text,btns,icon){', JS + 'function askChoice(title,text,btns,icon){')
open(F, 'w', encoding='utf-8').write(s)
print('OV2b applied')
