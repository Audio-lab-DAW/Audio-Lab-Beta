import sys,json
from playwright.sync_api import sync_playwright
SP='/tmp/'
def boot(p,scale=1,w=1600,h=1000,ui='{splash:false,lat3:1}',f=(sys.argv[1] if len(sys.argv)>1 else 'index.html')):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch();pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=scale);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%ui)
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs
def run(pg,code):
    return pg.evaluate("c=>window.AudioLab.run(c)",code)
# track controls editor test (v0.178, replaces the v0.164 list editor test): python3 tools/ui-tests/hdrlayout.py index.html
# part 1: every setting must give the same controls at the same places on all tracks; part 2: dragging, keys, Settings row
import collections
# visible controls per header, clipping-aware
SIG2="""(()=>{const out=[];for(const h of hdrin.querySelectorAll('.hdr')){const t=trkById(h.dataset.id);const zw=h.querySelector('.zw');const ks=[];if(zw){const zr=zw.getBoundingClientRect();for(const e of zw.children){const r=e.getBoundingClientRect();const k=e.dataset.z||e.dataset.a||(e.dataset.c||'').split(':')[0];const v=r.width>0&&r.bottom<=zr.bottom+1;ks.push(k+'@'+Math.round(r.left-zr.left)+','+Math.round(r.top-zr.top)+','+Math.round(r.width)+(v?'':'!')+(e.classList.contains('kn')?'kn':e.classList.contains('hpd')?'hp':''))}}
const pic=h.querySelector('.pic'),vm=h.querySelector('.vm');const pv=pic&&pic.getBoundingClientRect().width>0&&getComputedStyle(pic.parentNode).display!=='none';
out.push({n:t.name,kind:t.kind,hid:h.getBoundingClientRect().height<2,zw:!!zw,ks:ks.join(' '),pic:pv?Math.round(pic.getBoundingClientRect().width):0,vm:vm&&getComputedStyle(vm).display!=='none'?1:0})}return JSON.stringify(out)})()"""
def chk(pg,label,show=False):
    rs=json.loads(run(pg,SIG2));custom=json.loads(run(pg,"JSON.stringify(!!UI.hcz)"))
    vis=[r for r in rs if not r['hid']];sig={(r['ks'],r['pic'],r['vm']) for r in vis} if custom else {(r['pic'],r['vm']) for r in vis}
    bad=[r['n'] for r in rs if custom and not r['zw']]
    print(label,len(rs),'visible',len(vis),'UNIFORM' if len(sig)==1 and not bad else 'DIFFERENT %d %s'%(len(sig),bad))
    if show or len(sig)>1:
        for s in list(sig)[:3]:print('   ',s)
with sync_playwright() as p:
    b,pg,errs=boot(p,scale=1,w=1400,h=1000)
    run(pg,"(()=>{const c=document.getElementById('liteNote');if(c)c.remove()})()")
    run(pg,"hczOpen()");pg.wait_for_timeout(400)
    for pk in ('min','mix','all','std'):
        pg.locator('#hczEd [data-zp="%s"]'%pk).click();pg.wait_for_timeout(300);chk(pg,'preset '+pk,pk=='all')
        pg.screenshot(path=SP+'lay_%s.png'%pk,clip={'x':0,'y':40,'width':580,'height':500})
    pg.locator('#hczEd [data-zp="all"]').click();pg.wait_for_timeout(200)
    for sel,l in [('[data-zo=icon] [data-v=big]','icon big'),('[data-zo=icon] [data-v=hidden]','icon hidden'),('[data-zo=pan] [data-v=half]','pan half'),('[data-zo=pan] [data-v=round]','pan round'),('[data-zo=ms] [data-v=large]','ms large'),('[data-zo=meter] [data-v="0"]','meter hidden')]:
        pg.locator('#hczEd '+sel).click();pg.wait_for_timeout(250);chk(pg,l)
    for th in (140,64,44,26,20,96):
        run(pg,"V.th=%d;clampV();layoutRows();renderHeaders();dirty=true"%th);pg.wait_for_timeout(250);chk(pg,'height %d'%th)
    for l,c in [("fold group","hdrin.querySelector('.gfold').click()"),("unfold","hdrin.querySelector('.gfold').click()"),("add audio","hdrin.querySelector('[data-add=audio]').click()"),("add return","hdrin.querySelector('[data-add=return]').click()"),("undo","undo()"),("redo","redo()"),("scroll","V.y=1500;clampV();dirty=true"),("scroll back","V.y=0;clampV();dirty=true"),("lanes on one track","pushUndo();S.tracks[2].lanes=['vol','pan'];changed(true)"),("no lanes","undo()")]:
        run(pg,c);pg.wait_for_timeout(300);chk(pg,l)
    pg.screenshot(path=SP+'all_big.png',clip={'x':0,'y':40,'width':580,'height':500})
    # remove each / add each via click
    for k in ['vol','mute','solo','arm','edit','read','pan','write','lanes','freeze','byp','out','sends','color']:
        pg.locator('#hczEd .zmain [data-zk="%s"]'%k).hover();pg.wait_for_timeout(60);pg.locator('#hczEd .zqx').click();pg.wait_for_timeout(120)
        rs=json.loads(run(pg,SIG2));n=sum(1 for r in rs if (' '+r['ks']).find(' '+{'vol':'hd','pan':'hp','write':'aar'}.get(k,k)+'@')>=0)
        pg.locator('#hczEd .zt[data-za="%s"]'%k).click();pg.wait_for_timeout(120)
        rs=json.loads(run(pg,SIG2));m=sum(1 for r in rs if (' '+r['ks']).find(' '+{'vol':'hd','pan':'hp','write':'aar'}.get(k,k)+'@')>=0)
        print('remove/add',k,'tracks with it after remove:',n,'after add:',m,'of',len(rs))
    chk(pg,'after remove/add all')
    run(pg,"saveUINow()");pg.reload();pg.wait_for_timeout(9000);chk(pg,'after reload');print(run(pg,"JSON.stringify(UI.hcz)"))
    run(pg,"hczOpen()");pg.wait_for_timeout(300);pg.locator('#hczEd [data-ze="reset"]').click();pg.wait_for_timeout(300);chk(pg,'reset');print('stored',run(pg,"JSON.stringify(UI.hcz===undefined)"))
    print(errs)

with sync_playwright() as p:
    b,pg,errs=boot(p,scale=2,w=1300,h=1000)
    run(pg,"(()=>{const c=document.getElementById('liteNote');if(c)c.remove()})()")
    O=lambda:json.loads(run(pg,"JSON.stringify(hczGet().order)"))
    real=lambda:pg.evaluate("()=>{const zw=hdrin.querySelectorAll('.hdr')[3].querySelector('.zw');return zw?[...zw.children].map(e=>e.dataset.z||e.dataset.a||(e.dataset.c||'').split(':')[0]).join(','):'legacy'}")
    run(pg,"hczOpen()");pg.wait_for_timeout(400)
    def ctr(sel):
        r=pg.locator(sel).bounding_box();return r['x']+r['width']/2,r['y']+r['height']/2,r
    # 1 drag solo before volume (inside mini)
    x,y,_=ctr('#hczEd .zmain [data-zk=solo]');vx,vy,vr=ctr('#hczEd .zmain [data-zk=vol]')
    pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x-10,y,steps=3);pg.mouse.move(vr['x']+6,vy,steps=6);pg.wait_for_timeout(150)
    print('mid-drag order',O(),'real',real(),'marker',pg.evaluate("()=>[...document.querySelectorAll('#hczEd .zmkL,#hczEd .zmkR')].map(e=>e.dataset.zk+':'+e.className)"),'ghost',pg.evaluate("()=>!!document.querySelector('.zghost')"))
    pg.screenshot(path=SP+'drag1.png',clip={'x':0,'y':40,'width':600,'height':560});pg.mouse.up();pg.wait_for_timeout(200)
    print('1 solo first',O(),'ghost left',pg.evaluate("()=>!!document.querySelector('.zghost')"),'focus',pg.evaluate("()=>document.activeElement.dataset.zk"))
    # 2 drag volume to the end of the last row
    x,y,_=ctr('#hczEd .zmain [data-zk=vol]');lx,ly,lr=ctr('#hczEd .zmain [data-zk=lanes]')
    pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+10,y+5,steps=3);pg.mouse.move(lr['x']+lr['width']+30,ly,steps=8);pg.wait_for_timeout(100);pg.mouse.up();pg.wait_for_timeout(200);print('2 vol last',O())
    # 3 drag from tray into the mini, before mute
    x,y,_=ctr('#hczEd .zt[data-za=freeze]');mx,my,mr=ctr('#hczEd .zmain [data-zk=mute]')
    pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x,y-10,steps=3);pg.mouse.move(mr['x']+3,my,steps=8);pg.wait_for_timeout(150);print('  mid',O(),real())
    pg.screenshot(path=SP+'drag2.png',clip={'x':0,'y':40,'width':600,'height':800});pg.mouse.up();pg.wait_for_timeout(200);print('3 freeze before mute',O(),real())
    # 4 drag a control out of the mini onto the tray = remove
    x,y,_=ctr('#hczEd .zmain [data-zk=read]');tb=pg.locator('#hczEd .ztray').bounding_box()
    pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x,y+10,steps=3);pg.mouse.move(tb['x']+tb['width']-40,tb['y']+tb['height']-10,steps=8);pg.wait_for_timeout(150);print('  mid',O(),'tray marked',pg.evaluate("()=>document.querySelector('#hczEd .ztray').className"))
    pg.screenshot(path=SP+'drag3.png',clip={'x':0,'y':40,'width':600,'height':800});pg.mouse.up();pg.wait_for_timeout(200);print('4 read removed',O(),'in tray',pg.locator('#hczEd .zt[data-za=read]').count())
    # 5 Esc cancels a drag
    o0=O();x,y,_=ctr('#hczEd .zmain [data-zk=mute]');pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+200,y+300,steps=5);pg.wait_for_timeout(100);o1=O();pg.keyboard.press('Escape');pg.wait_for_timeout(150);pg.mouse.up();pg.wait_for_timeout(150)
    print('5 esc cancel',o0==O(),'was changed mid',o1!=o0,'editor open',pg.evaluate("()=>!document.getElementById('hczEd').hidden"))
    # 6 a plain click on a mini control changes nothing
    pg.locator('#hczEd .zmain [data-zk=mute]').click();print('6 click no change',o0==O())
    # 7 keyboard
    pg.locator('#hczEd .zmain [data-zk=mute]').focus();pg.keyboard.press('ArrowRight');pg.keyboard.press('ArrowRight');a=O();pg.keyboard.press('ArrowLeft');bb=O();print('7 keys',a,bb,'focus kept',pg.evaluate("()=>document.activeElement.dataset.zk"))
    pg.keyboard.press('Delete');print('  delete',O(),'focus',pg.evaluate("()=>document.activeElement.dataset.zk||document.activeElement.dataset.za"))
    pg.locator('#hczEd .zt[data-za=mute]').focus();pg.keyboard.press('Enter');pg.wait_for_timeout(100);print('  enter adds',O(),'focus',pg.evaluate("()=>document.activeElement.dataset.zk"))
    pg.locator('#hczEd [data-zp=mix]').focus();pg.keyboard.press(' ');pg.wait_for_timeout(150);print('  space on preset',O(),pg.evaluate("()=>document.activeElement.dataset.zp"))
    # tab order reaches mini items
    print('focusable mini items',pg.evaluate("()=>[...document.querySelectorAll('#hczEd .zmain [data-zk]')].map(e=>e.tabIndex).join()"))
    # 8 panel scrolled to bottom
    pg.evaluate("()=>{const p=document.getElementById('hczEd');p.scrollTop=9999}");pg.wait_for_timeout(200);pg.screenshot(path=SP+'bottom.png',clip={'x':220,'y':40,'width':360,'height':960})
    # 9 settings card
    run(pg,"hczClose();openSettings('layout')");pg.wait_for_timeout(600)
    info=pg.evaluate("()=>{const e=document.getElementById('hczSetB');e.scrollIntoView({block:'center'});const pv=[...document.querySelectorAll('.hczprev')].map(x=>x.outerHTML.length+':'+x.getBoundingClientRect().width+'x'+x.getBoundingClientRect().height+':'+(x.closest('[id]')||{}).id);return pv}");print('previews',info)
    pg.wait_for_timeout(300);pg.screenshot(path=SP+"set.png",clip={"x":480,"y":440,"width":560,"height":120})
    pg.locator('#hczSetB').click();pg.wait_for_timeout(400);print('from settings',pg.evaluate("()=>[document.getElementById('set').hidden,!document.getElementById('hczEd').hidden]"))
    print(errs)

