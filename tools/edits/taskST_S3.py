"""Task ST-S3 (settings rebuild, step S3): fix what is out of sync. Mono and L and R swap repaint the master strip from Settings and are
exclusive there as on the strip; Settings > Zoom and playhead shows all six Follow ways and the 'Follow again 3 s' switch; the Follow command
and the menu refresh Settings; the visualizer's header and Settings stay in step. One block before askChoice, from taskST_S3_block.js.
  python3 tools/edits/taskST_S3.py [index.html]"""
import sys,os,re
P=sys.argv[1] if len(sys.argv)>1 else 'index.html'
B=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'taskST_S3_block.js'),encoding='utf-8').read()
s=open(P,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
A='function askChoice(title,text,btns,icon){'
assert s.count(A)==1 and 'const STS3=' not in s
s=s.replace(A,B.rstrip('\n')+'\n'+A)
# Mono and swap in Settings: exclusive, as on the master strip (monSet now repaints the strip)
rep("for(const[id,k] of[['#monoChk','monoChk'],['#swapChk','swapChk'],['#dcChk','dcBlock']])$(id).onchange=e=>{UI[k]=e.target.checked;saveUI();monSet()};",
    "for(const[id,k] of[['#monoChk','monoChk'],['#swapChk','swapChk'],['#dcChk','dcBlock']])$(id).onchange=e=>{UI[k]=e.target.checked;if(e.target.checked&&k==='monoChk'){UI.swapChk=false;$('#swapChk').checked=false}if(e.target.checked&&k==='swapChk'){UI.monoChk=false;$('#monoChk').checked=false}saveUI();monSet()};")
rep(" '#monoChk':'Mono check|Temporarily sums left and right so you can hear whether the mix still works in mono (clubs, phones).',\n",
    " '#monoChk':'Mono check|Temporarily sums left and right so you can hear whether the mix still works in mono (clubs, phones). The same switch as Mono on the master strip.',\n '#swapChk':'Swap left and right|Plays the left channel on the right and the right on the left, to check whether a side sounds different only because of your ears or headphones. The same switch as L↔R on the master strip. Not in the export.',\n")
# Follow: six cards in the order of the menu, plus the follow-again switch
i=s.index('<div class="zc pc" id="setFollowC">');j=s.index('</div>',i)+6;old=s[i:j]
btn={m.group(1):m.group(0) for m in re.finditer(r'<button data-fm="(\w+)">.*?</button>',old)}
assert set(btn)=={'center','page','stay','off'}
SV='<svg viewBox="0 0 160 70" aria-hidden="true"><rect x="1" y="1" width="158" height="68" rx="6" fill="#0d0e12" stroke="#2a2b33"/><g opacity=".7"><rect x="10" y="16" width="60" height="9" rx="2" fill="#4c8dff"/><rect x="24" y="32" width="100" height="9" rx="2" fill="#b583ff"/><rect x="60" y="48" width="80" height="9" rx="2" fill="#f5c84c"/></g>'
lead=('<button data-fm="lead">'+SV+'<rect x="42" y="6" width="116" height="58" fill="#3ecf8e" opacity=".07"/><rect x="40" y="6" width="2.5" height="58" fill="#3ecf8e"/>'
 '<path d="M50 10h22m0 0-5-4m5 4-5 4" stroke="#3ecf8e" stroke-width="2" fill="none" stroke-linecap="round"/></svg>'
 '<b>Look ahead</b><small>The playhead sits at a quarter of the view, so you see more of what is coming.</small></button>')
edge=('<button data-fm="edge">'+SV+'<path d="M124 6v58" stroke="#3ecf8e" stroke-width="1" stroke-dasharray="3 3" opacity=".6"/><rect x="128" y="6" width="2.5" height="58" fill="#3ecf8e"/>'
 '<path d="M136 6l5 4-5 4M144 6l5 4-5 4" stroke="#3ecf8e" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
 '<b>Push at the edge</b><small>The view moves smoothly once the playhead nears the right edge.</small></button>')
new=('<div class="zc pc" id="setFollowC">'+btn['center']+btn['stay']+lead+btn['page']+edge+btn['off']+'</div>\n'
 '        <label class="chk" style="margin-top:8px" title="After you scroll the view yourself while playing, following comes back on its own 3 seconds later. The same switch is in the Follow menu."><input type="checkbox" id="setFollowRes"> Follow again 3 s after I stop scrolling</label>')
s=s[:i]+new+s[j:]
rep('<p class="hint">Click Follow on the playhead to switch following on or off; right-click it for more ways to follow. Dragging the ruler up or down always zooms.</p>',
    '<p class="hint">Click Follow on the playhead to switch following on or off; right-click it for the same six ways and the switch above. Dragging the ruler up or down always zooms.</p>')
rep("const fm=UI.follow?UI.followMode:'off';for(const b of $('#setFollowC').children)b.classList.toggle('on',b.dataset.fm===fm);",
    "const fm=UI.follow?UI.followMode:'off';for(const b of $('#setFollowC').children)b.classList.toggle('on',b.dataset.fm===fm);{const r=$('#setFollowRes');if(r)r.checked=UI.followResume!==false}")
rep("act:()=>{UI.followResume=UI.followResume===false;saveUI()}","act:()=>{UI.followResume=UI.followResume===false;saveUI();try{syncSettings()}catch(e){}}")
rep("run:()=>{UI.follow=!UI.follow;saveUI();dirty=true;toast(","run:()=>{setFollow(!UI.follow);toast(")
rep("nav:'zoom playhead follow scroll'","nav:'zoom playhead follow scroll look ahead push at the edge follow again stay in place page by page keep centred'")
open(P,'w',encoding='utf-8').write(s);print('ok')
