"""v0.181: Bouncy Notes pages and Bounce Delay in the page. python3 tools/ui-tests/bounce.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.build({'tracks':[{'name':'B','preset':'pluck','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':6,'v':.9},{'p':67,'s':6,'l':6,'v':.8}]}]}]})
al.run("(()=>{const t=S.tracks[0];t.fx.unshift(mkFx('bnotes'));t.fx.push(mkFx('bdelay'));selT=t.id;changed(true);renderFx();return 1})()");al.page.wait_for_timeout(900)
def box(D):return json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:Math.max(0,r.left),y:r.top,width:Math.min(r.width,1600-Math.max(0,r.left)),height:r.height})})()"%D))
def shot(n,D):al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.mouse.move(5,5);al.page.wait_for_timeout(700);al.page.screenshot(path=os.path.join(out,n),clip=box(D))
def inside(tag,D):
    print('%-14s %s'%(tag,al.run("(()=>{const d=document.querySelector('%s'),R=d.getBoundingClientRect(),bad=[];for(const el of d.querySelectorAll('[data-c],.ndtb label,.ndtb button,.devh>*')){const r=el.getBoundingClientRect();if(!r.width)continue;if(r.left<R.left-1||r.right>R.right+1||r.top<R.top-1||r.bottom>R.bottom+1)bad.push((el.textContent||'').trim().slice(0,16))}return 'device '+Math.round(R.width)+'x'+Math.round(R.height)+' controls '+d.querySelectorAll('[data-c]').length+' choices '+d.querySelectorAll('.ndtb label').length+' outside: '+(bad.join(' | ')||'none')})()"%D)))
B='.dev.pbx-bnotes';D='.dev.pbx-bdelay'
inside('Bouncy: Balls',B);shot('bn_balls.png',B)
al.page.click(B+' [data-nact=tn]');al.page.wait_for_timeout(300);inside('Bouncy: Notes',B);shot('bn_notes.png',B)
al.page.click(B+' [data-nact=tb]');al.page.wait_for_timeout(300);al.page.select_option(B+' select[data-x=sync]','1/4');al.page.select_option(B+' select[data-x=bmode]','half');al.page.wait_for_timeout(300)
print('rhythm chosen in the page',al.run("JSON.stringify([S.tracks[0].fx[0].p.sync,S.tracks[0].fx[0].p.bmode])"),'notes',al.run("(()=>{const t=S.tracks[0];return mfxNotes(t,t.clips[0].notes).slice(0,5).map(n=>Math.round(n.s*1000)/1000).join(' ')})()"))
print('tooltip of Rhythm:',al.run("(document.querySelector('%s select[data-x=sync]').closest('label')||{}).title"%B)[:80])
al.run("pos=0;1");al.page.keyboard.press('Space');al.page.wait_for_timeout(1400);shot('bn_playing.png',B);shot('bd_playing.png',D);al.page.keyboard.press('Space');al.page.wait_for_timeout(300)
inside('Bounce Delay',D);shot('bd.png',D)
al.page.select_option(D+' select[data-x=pre]','rise');al.page.wait_for_timeout(300);shot('bd_rise.png',D)
print('tooltip of Bounciness:',al.run("(document.querySelector('%s [data-c$=\":bounce\"]')||{}).title"%D)[:70])
al.page.click(D+' [data-kt]');shot('bd_hidden.png',D)
print('errors',al.errors);al.stop()
