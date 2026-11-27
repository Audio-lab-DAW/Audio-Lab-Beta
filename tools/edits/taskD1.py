import sys
f=sys.argv[1];s=open(f,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
rep("pkr:0,gband:0,fd:22,panst:'auto'","pkr:0,gband:0,fd:7,panst:'auto'")
rep("{id:'audiolab',n:'AudioLab',d:'Dark blue glass, see-through clips',bgL:40,tintH:215,tintA:25,gridB:50,clipA:36,fd:22,","{id:'audiolab',n:'AudioLab',d:'Dark blue glass, see-through clips',bgL:40,tintH:215,tintA:25,gridB:50,clipA:36,fd:7,")
rep("""/* once: the old default (Classic) and the old Flat bars move to Flat bars 2 */
if(!UI.fd22){UI.fd22=1;if(UI.mxs&&(UI.mxs.fd===1||UI.mxs.fd===7)){UI.mxs.fd=22}try{saveUI()}catch(e){}}
""","""/* v0.222 (task D1): the one-time move of Classic and Flat bars to Flat bars 2 (UI.fd22) is gone; it is undone in the block "v0.222 (task D1)" */
""")
rep("   Flat bars 2 (design 22) is the default fader and meter design. Master pin.","   Flat bars 2 (design 22) was the default fader and meter design until v0.222 (task D1), now Flat bars (design 7) again. Master pin.")
rep("/* Flat bars 2: the default fader and meter design (from","/* Flat bars 2: the default fader and meter design until v0.222, since then a choice like the others (from")
rep("const VERSION='0.221',BUILD='27 November 2026'","const VERSION='0.222',BUILD='27 November 2026'")
new="""/* ===================== v0.222 (task D1): Flat bars (design 7) is the standard fader and meter design again =====================
   MXSD.fd and the AudioLab theme are 7. The one-time move to Flat bars 2 (UI.fd22, v0.19x) is undone once per profile (UI.fd7):
   a profile that went through that move (UI.fd22 set) and has Flat bars 2 saved goes back to Flat bars. The app saved nothing that tells
   "moved by the migration" from "picked Flat bars 2 by hand" (no flag per choice, no time), so every such profile goes back, as the user asked.
   A profile that never ran the old move keeps what it saved. Flat bars 2 picked after this step stays (UI.fd7 is set). UI.fd7: 1 nothing to do, 2 moved back. */
if(!UI.fd7){const back=!!UI.fd22&&!!UI.mxs&&UI.mxs.fd===22;if(back)UI.mxs=Object.assign({},UI.mxs,{fd:7});UI.fd7=back?2:1;UI.fd22=1;try{saveUI()}catch(e){}
  if(back){try{fdCssUp(true);mxsApply();mxsSync();hfdCss()}catch(e){}}}
"""
a="function askChoice(title,text,btns,icon){"
assert s.count(a)==1;s=s.replace(a,new+a)
open(f,'w',encoding='utf-8').write(s)
