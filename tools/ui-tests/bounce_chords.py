"""Bouncy Notes (v0.189): the chord steps row and the rhythm per ball row in the page. python3 tools/ui-tests/bounce_chords.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.build({'bpm':120,'tracks':[{'name':'P','preset':'pluck','fx':[{'type':'bnotes'}],'clips':[{'start':0,'len':8,'notes':[{'p':60,'s':0,'l':8,'v':.9}]}]}]})
al.run("selT=S.tracks[0].id;renderFx();1");al.page.wait_for_timeout(800)
D='.dev.pbx-bnotes'
def box():return json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:Math.max(0,r.left),y:r.top,width:r.width,height:r.height})})()"%D))
def shot(n):al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.mouse.move(5,5);al.page.wait_for_timeout(400);al.page.screenshot(path=os.path.join(out,n),clip=box())
def inside(tag):
    print('%-8s %s'%(tag,al.run("(()=>{const d=document.querySelector('%s'),R=d.getBoundingClientRect(),bad=[];for(const el of d.querySelectorAll('[data-c],button,select')){const r=el.getBoundingClientRect();if(!r.width)continue;if(r.left<R.left-1||r.right>R.right+1||r.top<R.top-1||r.bottom>R.bottom+1)bad.push((el.textContent||el.dataset.c||el.dataset.x||'').trim().slice(0,16))}return 'device '+Math.round(R.width)+' x '+Math.round(R.height)+', outside: '+JSON.stringify(bad)})()"%D)))
P=lambda k:al.run("JSON.stringify(S.tracks[0].fx[0].p.%s??null)"%k)
inside('Balls');shot('bn_balls_rows.png')
for k,v in (('r2','1/8 triplet'),('r3','1/8')):al.page.select_option(D+' select[data-x=%s]'%k,v);al.page.wait_for_timeout(200)
print('rhythm per ball set by the page: 2nd',P('r2'),'3rd',P('r3'),'4th',P('r4'))
al.page.click(D+' [data-a=tn]') if al.run("!!document.querySelector('%s [data-a=tn]')"%D) else al.run("NACT.bnotes(S.tracks[0].fx[0],'tn');1")
al.page.wait_for_timeout(500);inside('Notes')
for i,v in enumerate(['1','5','6','4']):al.page.select_option(D+' select[data-x=pg%d]'%i,v);al.page.wait_for_timeout(150)
al.page.select_option(D+' select[data-x=prate]','1/2');al.page.wait_for_timeout(200)
print('chord steps set by the page:',[json.loads(P('pg%d'%i)) for i in range(8)],'every',P('prate'))
print('shown as',al.run("JSON.stringify([...document.querySelectorAll('%s select.bnpgs')].map(s=>s.selectedOptions[0].textContent))"%D))
shot('bn_notes_rows.png')
al.run("undo();undo();undo();undo();undo();1");al.page.wait_for_timeout(300);print('after five undos:',[json.loads(P('pg%d'%i)) for i in range(4)],'every',P('prate'))
print('tooltips on the rows:',al.run("JSON.stringify([...document.querySelectorAll('%s .bnpg select')].every(s=>s.title&&!/—|–/.test(s.title)))"%D))
al.run("(()=>{const s=document.querySelector('%s select[data-x=pre]');if(s){s.value='popc';s.dispatchEvent(new Event('change',{bubbles:true}))}})()"%D);al.page.wait_for_timeout(400)
print('preset Chords I V VI IV: steps',[json.loads(P('pg%d'%i)) for i in range(4)],'harmony',P('harm'))
print('errors',al.errors);al.stop()
