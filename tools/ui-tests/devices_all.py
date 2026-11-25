"""Every device, one by one (task C, one design language): python3 tools/ui-tests/devices_all.py [index.html] [out dir] [only,names]
Builds a track per instrument and adds each effect to a Pluck track, checks that no control sticks out of its device,
prints the order of the title row, opens and closes the parameters where there is a button for it, and saves a screenshot of each."""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
only=sys.argv[3].split(',') if len(sys.argv)>3 else None
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.build({'tracks':[{'name':'B','preset':'pluck','clips':[{'start':0,'len':4,'notes':[{'p':60,'s':0,'l':1,'v':.9}]}]}]})
insts=json.loads(al.run("JSON.stringify(IBG.flatMap(g=>g[2]))"));fxs=json.loads(al.run("JSON.stringify(FBG.flatMap(g=>g[2]))"))
INFO="""(()=>{const out=[];for(const d of fxin.querySelectorAll('.dev')){if(d.classList.contains('add')||d.classList.contains('tdev')||d.classList.contains('macdev')||d.classList.contains('modcol'))continue;if(!d.dataset.d)continue;
 const R=d.getBoundingClientRect(),bad=[];for(const el of d.querySelectorAll('.kn,.vb,.hb,.ndtb label,.ndtb button,.devh>*,canvas,select,button')){const r=el.getBoundingClientRect();if(!r.width||!el.offsetParent)continue;const sc=el.closest('.kscroll,.gridwrap,.pzscroll,[data-scroll]');if(sc)continue;if(r.left<R.left-1||r.right>R.right+1||r.top<R.top-1||r.bottom>R.bottom+1)bad.push((el.textContent||el.className||el.tagName).trim().slice(0,16)+' '+Math.round(Math.max(r.right-R.right,R.left-r.left))+','+Math.round(Math.max(r.bottom-R.bottom,R.top-r.top)))}
 const H=d.querySelector('.devh'),row=H?[...H.children].filter(e=>e.offsetParent&&e.getBoundingClientRect().width).sort((a,b)=>{const x=a.getBoundingClientRect(),y=b.getBoundingClientRect();return Math.abs(x.top-y.top)>12?x.top-y.top:x.left-y.left}).map(e=>e.dataset.dl||(e.classList.contains('pw')?'onoff':e.classList.contains('x')?'remove':e.classList.contains('duar')?'arrow':e.classList.contains('dusp')?'':e.classList.contains('duchg')?'change':e.classList.contains('dpre')||e.classList.contains('kpre')?'preset':e.classList.contains('dchg')||e.dataset.s==='browse'?'change':e.tagName==='SPAN'?'name':e.tagName==='svg'?'logo':(e.className||e.tagName).toString().slice(0,10))):[];
 const hr=H?H.getBoundingClientRect():{height:0},g=d.querySelector('.dug'),gr=g&&g.getBoundingClientRect(),cv=[...d.querySelectorAll('canvas')].filter(c=>c.offsetParent&&c.getBoundingClientRect().width>40)[0];
 const vis=e=>e.offsetParent&&e.getBoundingClientRect().width>0,U=a=>[...new Set(a)].join('/'),kn=U([...d.querySelectorAll('.kn svg')].filter(e=>e.getBoundingClientRect().width>0).map(e=>Math.round(e.getBoundingClientRect().width))),hbs=U([...d.querySelectorAll('.hb')].filter(vis).map(e=>Math.round(e.getBoundingClientRect().height))),vbs=U([...d.querySelectorAll('.vb')].filter(vis).map(e=>Math.round(e.getBoundingClientRect().width)+'x'+Math.round(e.querySelector('.vt').getBoundingClientRect().width)));
 const B=d.querySelector(':scope>.devb'),HH=d.querySelector(':scope>.devh');let slack=0;if(B){const k=[...B.children].filter(vis);if(k.length){const last=k[k.length-1].getBoundingClientRect();slack=Math.round(B.getBoundingClientRect().right-last.right-parseFloat(getComputedStyle(B).paddingRight))}}
 out.push({kn,hbs,vbs,slack,w:Math.round(R.width),h:Math.round(R.height),hh:Math.round(hr.height),row:row.filter(x=>x).join(' '),pic:!!cv,arrow:!!d.querySelector('.duar'),pre:d.querySelectorAll('.devh select[data-x=pre] option,.devh select[data-s=ipre] option,.devh .kpre option').length,gain:gr?Math.round(R.right-gr.right)+','+Math.round(R.bottom-gr.bottom):'none',bad:bad.join(' | ')||'none',cls:d.className.replace(/\\s+/g,' ').slice(0,60)})}return JSON.stringify(out)})()"""
def shot(n,kind='inst'):
    al.run("(()=>{const d=[...fxin.querySelectorAll('.dev[data-d=inst],.dev[data-d=fx]')].filter(d=>!d.parentElement.closest('.dev'));const e=d[%s];if(e)e.scrollIntoView({inline:'start'});return 1})()"%('d.length-1' if kind=='fx' else '0'))
    al.page.mouse.move(5,5);al.page.wait_for_timeout(450)
    b=json.loads(al.run("(()=>{const d=[...fxin.querySelectorAll('.dev[data-d=inst],.dev[data-d=fx]')].filter(d=>!d.parentElement.closest('.dev'));const e=d[%s],r=e.getBoundingClientRect(),x=Math.max(0,r.left-6),y=Math.max(0,r.top-6);return JSON.stringify({x,y,width:Math.min(1600-x,r.right+6-x),height:Math.min(1000-y,r.height+12)})})()"%('d.length-1' if kind=='fx' else '0')))
    al.page.screenshot(path=os.path.join(out,n+'.png'),clip=b)
def report(kind,k):
    for i,d in enumerate(json.loads(al.run(INFO))):
        if kind=='fx' and i==0:continue
        print('%-5s %-8s %4dx%-3d title %2d | %s | picture %s arrow %s presets %d gain %s | knob %s slider %s bar %s unused %d | outside: %s'%(kind,k,d['w'],d['h'],d['hh'],d['row'],'yes' if d['pic'] else 'no','yes' if d['arrow'] else 'no',d['pre'],d['gain'],d['kn'] or '-',d['hbs'] or '-',d['vbs'] or '-',d['slack'],d['bad']))
def toggle(kind,k):
    Q="[...fxin.querySelectorAll('.dev[data-d=inst],.dev[data-d=fx]')].filter(d=>!d.parentElement.closest('.dev'))[%s]"%('1' if kind=='fx' else '0')
    W=lambda:al.run("(()=>{const d=%s;return JSON.stringify([Math.round(d.getBoundingClientRect().width),!!d.querySelector('.duar'),d.querySelectorAll('.dfs [data-c]').length,[...d.querySelectorAll('.dfs [data-c],.dug [data-c]')].filter(e=>e.offsetParent).length])})()"%Q)
    w0=json.loads(W())
    if not w0[1]:print('      no arrow (no picture)');return
    al.run("%s.querySelector('.duar').click();1"%Q);al.page.wait_for_timeout(450);w1=json.loads(W())
    if only:shot(('f_' if kind=='fx' else 'i_')+k+'_shut',kind)
    al.run("%s.querySelector('.duar').click();1"%Q);al.page.wait_for_timeout(450);w2=json.loads(W())
    ok=w1[3]==0 and w2[0]==w0[0] and w2[3]==w0[3]
    print('      parameters shut and open again: width %d > %d > %d, controls shown %d > %d > %d %s'%(w0[0],w1[0],w2[0],w0[3],w1[3],w2[3],'ok' if ok else 'CHECK'))
for k in insts:
    if only and k not in only:continue
    al.run("(()=>{const t=S.tracks[0];t.fx=[];for(const key of Object.keys(t.inst))delete t.inst[key];Object.assign(t.inst,JSON.parse(JSON.stringify(PRESETS['%s'])),{preset:'%s'});selT=t.id;changed(true);renderFx();return 1})()"%(k,k));al.page.wait_for_timeout(700)
    report('inst',k);toggle('inst',k);shot('i_'+k)
al.run("(()=>{const t=S.tracks[0];for(const key of Object.keys(t.inst))delete t.inst[key];Object.assign(t.inst,JSON.parse(JSON.stringify(PRESETS.pluck)),{preset:'pluck'});changed(true);renderFx();return 1})()")
for k in fxs:
    if only and k not in only:continue
    al.run("(()=>{const t=S.tracks[0];t.fx=[mkFx('%s')];selT=t.id;changed(true);renderFx();return 1})()"%k);al.page.wait_for_timeout(700)
    report('fx',k);toggle('fx',k);shot('f_'+k,'fx')
print('errors',al.errors);al.stop()
