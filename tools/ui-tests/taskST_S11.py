"""Task ST-S11 (settings rebuild, step S11): audio devices in the picked design B2. Settings › Audio opens with a Devices card: role cards
Listen through and Record from (the one output select and the one input select), the Listening and Recording setups, the Recording setup
filled automatically (the interface for input and output) and changeable by hand; arming an audio track switches to Recording by itself with a
quiet notice and a way back, disarming the last one goes back; a known device switches at once with a short ramp and no question; the arm
setting (audio, any, never); device lists as Chromium reports them on macOS and on Windows (fake devices); an older profile loads and its
input becomes the Recording input; search finds the rows by old and new names; dark and Light level; no console errors.
  python3 tools/ui-tests/taskST_S11.py [repo dir] [out dir]"""
import sys,os,mimetypes,json
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(OUT,exist_ok=True)
N=[0,0];FAIL=[]
def ck(name,ok,info=''):
    N[0]+=1
    if ok:N[1]+=1
    else:FAIL.append(name);print('  FAIL',name,str(info)[:700])
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html';f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type='text/html' if f.endswith('.html') else (mimetypes.guess_type(f)[0] or 'application/octet-stream'))
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
J=lambda pg,c:json.loads(R(pg,"JSON.stringify("+c+")"))
def search(pg,q):
    r=pg.evaluate("q=>{const e=document.getElementById('setQ');e.focus();e.value=q;e.dispatchEvent(new Event('input'));return[...document.querySelectorAll('#setQR button')].map(b=>(b.querySelector('b')||b).textContent)}",q)
    pg.evaluate("()=>{const e=document.getElementById('setQ');e.value='';e.dispatchEvent(new Event('input'))}");return r
MAC=[('audiooutput','default','Default - iFi xDSD Gryphon (20b1:3008)','g1'),('audiooutput','gry','iFi xDSD Gryphon (20b1:3008)','g1'),('audiooutput','mbp','MacBook Pro Speakers (Built-in)','g2'),('audiooutput','ams','Zoom AMS-24 (1686:0428)','g3'),
     ('audioinput','default','Default - MacBook Pro Microphone (Built-in)','g2'),('audioinput','mbpm','MacBook Pro Microphone (Built-in)','g2'),('audioinput','amsi','Zoom AMS-24 (1686:0428)','g3')]
WIN=[('audiooutput','default','Default - Speakers (Realtek(R) Audio)','w1'),('audiooutput','communications','Communications - Speakers (Realtek(R) Audio)','w1'),('audiooutput','rtk','Speakers (Realtek(R) Audio)','w1'),
     ('audiooutput','zout','Speakers (Zoom AMS-24)',''),('audiooutput','ifi','Speakers (iFi (by AMR) HD USB Audio)','w3'),
     ('audioinput','default','Default - Microphone (Realtek(R) Audio)','w1'),('audioinput','communications','Communications - Microphone (Realtek(R) Audio)','w1'),('audioinput','rtkm','Microphone (Realtek(R) Audio)','w1'),('audioinput','zin','Microphone (Zoom AMS-24)','')]
def fake(devs):
    return """(()=>{const D=%s;window.__sinks=[];window.__ramps=[];
 const md=navigator.mediaDevices;md.enumerateDevices=async()=>D.map(([kind,deviceId,label,groupId])=>({kind,deviceId,label,groupId,toJSON(){return this}}));
 AudioContext.prototype.setSinkId=async function(id){window.__sinks.push(id);Object.defineProperty(this,'sinkId',{value:id,configurable:true})};
 })();"""%json.dumps(devs)
SPY="(()=>{const lr=AudioParam.prototype.linearRampToValueAtTime;AudioParam.prototype.linearRampToValueAtTime=function(v,t){try{if(MON&&MON.out&&this===MON.out.gain)window.__ramps.push([+v.toFixed(3),+(t-MON.out.context.currentTime).toFixed(3)])}catch(e){}return lr.apply(this,arguments)};return 1})()"
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream','--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c=b.new_context(viewport={'width':1600,'height':1000},permissions=['microphone']);pg=c.new_page();errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and 'icons.json' not in m.text and errs.append('console '+m.text[:200]))
        pg.route('https://app.test/**',serve)
        u=dict(order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite,recOff=7,sink='gry',inDev='amsi',st10Seen=['gry','ams','mbp'])
        pg.add_init_script(fake(MAC)+"if(!sessionStorage.getItem('t11')){sessionStorage.setItem('t11','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
        pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(2500)
        pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.315)
        st=J(pg,"{s:UI.sink,i:UI.inDev,o:UI.recOff,st:UI.st11}")
        ck(f'{L}: an older profile loads: output, input and offset kept, the input becomes the Recording input',st['s']=='gry' and st['i']=='amsi' and st['o']==7 and st['st']['on']=='listen' and st['st']['L']['o']=='gry' and st['st']['R']['i']=='amsi',st)
        R(pg,"(ensureCtx(),openSettings('audio'))");pg.wait_for_timeout(1200)
        cards=J(pg,"[...document.querySelectorAll('#setBody>section[data-page=\"audio\"] .sbox>h4')].map(h=>h.childNodes[0].textContent.trim())")
        ck(f'{L}: Devices is the first card on Audio',cards[:3]==['Devices','Audio driver','Running now'],cards)
        ck(f'{L}: the one output select sits in Listen through, the one input select in Record from',R(pg,"!!document.querySelector('#st11L #outSel')&&!!document.querySelector('#st11R #ifdIn')&&document.querySelectorAll('#outSel').length===1&&document.querySelectorAll('#ifdIn').length===1"))
        rn=J(pg,"['st11LN','st11RN','st11Why','st11Oth'].map(i=>document.getElementById(i).textContent)")
        ck(f'{L}: Listen through shows the Gryphon, Record from the AMS-24',rn[0]=='iFi xDSD Gryphon (20b1:3008)' and rn[1]=='Zoom AMS-24 (1686:0428)',rn)
        ck(f'{L}: the output list shows the device that plays, not System default',R(pg,"document.getElementById('outSel').value")=='gry')
        ck(f'{L}: the sentence explains Listening and the switch on arming',rn[2].startswith('Listening: AudioLab plays through iFi xDSD Gryphon') and 'switches to the Recording setup by itself' in rn[2],rn[2])
        ck(f'{L}: the Recording setup is filled with the AMS-24 for both (one device)',rn[3].startswith('Recording setup: Zoom AMS-24 (1686:0428) records and plays'),rn[3])
        ck(f'{L}: the chips show what kind of device it is',R(pg,"/Gryphon/.test(document.getElementById('st11LC').textContent)&&/kHz/.test(document.getElementById('st11LC').textContent)"),R(pg,"document.getElementById('st11LC').textContent"))
        ck(f'{L}: every control in the card has a tooltip',R(pg,"[...document.querySelectorAll('#st11Dev button,#st11Dev select')].every(e=>(e.title||'').length>10||e.closest('[title]'))"))
        ck(f'{L}: no em dashes in the card',R(pg,"!/\\u2014/.test(document.getElementById('st11Dev').textContent)"))
        pg.locator('#set .setw').screenshot(path=f'{OUT}/s11_audio_{L}.png')
        R(pg,"ST5.show('dac')");pg.wait_for_timeout(500)
        ck(f'{L}: DAC and audio interface shows Record from as a read-out with Change on Audio (Interface mode)',R(pg,"(e=>!!e&&!!e.closest('#setBody>section[data-page=\"dac\"]')&&/AMS-24/.test(e.textContent))(document.getElementById('st11DIn'))") and R(pg,"!!document.querySelector('[data-st10go=\"#ifdIn\"]')"))
        R(pg,"document.querySelector('[data-st10go=\"#ifdIn\"]').click()");pg.wait_for_timeout(400)
        ck(f'{L}: Change on Audio opens Audio at Record from',R(pg,"ST5.cur")=='audio')
        miss=J(pg,"STT.filter(r=>['audio','dac'].includes(r.pg)).filter(r=>{const e=SETT.ctl(r.id);return !e||!e.closest('#setBody>section[data-page=\"'+r.pg+'\"]')}).map(r=>r.id)")
        ck(f'{L}: every Audio and DAC row of the table points at a control on its own page',miss==[],miss)
        # fresh: the Recording setup fills itself even without an input chosen before
        R(pg,"(UI.st11.R={o:null,i:null},ST11.paint())");pg.wait_for_timeout(600)
        ck(f'{L}: with nothing chosen, the interface is picked over the built-in microphone',J(pg,"ST11.rec()")=={'o':'ams','i':'amsi','oa':True,'ia':True},J(pg,"ST11.rec()"))
        # arming switches, a notice, back
        R(pg,"(()=>{const t=mkTrack('audio',null,'Vocal');S.tracks.push(t);window.__t=t;window.__sinks.length=0;window.__ramps.length=0})()")
        R(pg,SPY);R(pg,"(play.on||start(),0)");pg.wait_for_timeout(500)
        R(pg,"armTrack(window.__t)");pg.wait_for_timeout(1500)
        s=J(pg,"{s:UI.sink,i:UI.inDev,on:UI.st11.on,auto:UI.st11.auto,arm:window.__t.arm,mic:!!window.__t._mic,sinks:window.__sinks,ramps:window.__ramps}")
        ck(f'{L}: arming an audio track switches to Recording by itself (AMS-24 out and in), the track is armed with its input',s['s']=='ams' and s['i']=='amsi' and s['on']=='rec' and s['auto']==1 and s['arm'] and s['mic'] and 'ams' in s['sinks'],s)
        ck(f'{L}: the switch ramps down and up in a few tens of ms (no click)',any(r[0]==0 and 0<r[1]<=0.04 for r in s['ramps']) and any(r[0]==1 and 0<r[1]<=0.05 for r in s['ramps']),s['ramps'])
        pg.wait_for_timeout(200);ck(f'{L}: the output gain is back at 1 after the ramp',abs(R(pg,"MON.out.gain.value")-1)<1e-6,R(pg,"MON.out.gain.value"))
        nt=J(pg,"(n=>n?{on:!n.hidden,t:n.textContent}:null)(document.getElementById('st11Note'))")
        ck(f'{L}: a quiet notice says it switched, with Back to Listening',nt and nt['on'] and 'Switched to the Recording setup: Zoom AMS-24 (1686:0428) records and plays.' in nt['t'] and 'Back to Listening' in nt['t'],nt)
        ck(f'{L}: no Keep? question for a known device',R(pg,"(k=>!k||k.hidden)(document.getElementById('st10Keep'))"))
        ck(f'{L}: the segment and the sentence follow',R(pg,"document.querySelector('#st11Seg [data-st11m=rec]').classList.contains('on')") and 'records and plays, so input and output share one clock' in R(pg,"document.getElementById('st11Why').textContent"))
        pg.locator('#set .setw').screenshot(path=f'{OUT}/s11_rec_{L}.png');pg.screenshot(path=f'{OUT}/s11_note_{L}.png')
        pg.click('#st11Note [data-st11n="back"]');pg.wait_for_timeout(900)
        s=J(pg,"{s:UI.sink,i:UI.inDev,on:UI.st11.on,arm:window.__t.arm}")
        ck(f'{L}: Back to Listening goes back at once, the track stays armed',s=={'s':'gry','i':'amsi','on':'listen','arm':True},s)
        # disarm and arm again: back by itself on disarm
        R(pg,"armTrack(window.__t)");pg.wait_for_timeout(600);R(pg,"armTrack(window.__t)");pg.wait_for_timeout(1200)
        ck(f'{L}: arming again switches again',J(pg,"[UI.sink,UI.st11.on]")==['ams','rec'])
        R(pg,"armTrack(window.__t)");pg.wait_for_timeout(1200)
        nt=J(pg,"(n=>({on:!n.hidden,t:n.textContent}))(document.getElementById('st11Note'))")
        ck(f'{L}: disarming the last audio track goes back to Listening by itself and says so',J(pg,"[UI.sink,UI.st11.on]")==['gry','listen'] and 'Back on the Listening setup: iFi xDSD Gryphon' in nt['t'],[J(pg,"[UI.sink,UI.st11.on]"),nt])
        # by hand: Recording with another output, kept; Listening; Recording again; fill automatically again
        pg.click('#st11Seg [data-st11m="rec"]');pg.wait_for_timeout(900)
        ck(f'{L}: the Recording button switches by hand, no automatic flag',J(pg,"[UI.sink,UI.st11.on,UI.st11.auto]")==['ams','rec',0])
        pg.select_option('#outSel','mbp');pg.wait_for_timeout(1200)
        ck(f'{L}: an output chosen by hand in Recording is kept in that setup',J(pg,"[UI.sink,UI.st11.R.o]")==['mbp','mbp'] and R(pg,"document.getElementById('st11LB').textContent")=='chosen by you',[J(pg,"[UI.sink,UI.st11.R]"),R(pg,"document.getElementById('st11LB').textContent")])
        ck(f'{L}: two devices are explained honestly (two clocks)','two devices with their own clocks' in R(pg,"document.getElementById('st11Why').textContent"),R(pg,"document.getElementById('st11Why').textContent"))
        pg.click('#st11Seg [data-st11m="listen"]');pg.wait_for_timeout(900);pg.click('#st11Seg [data-st11m="rec"]');pg.wait_for_timeout(900)
        ck(f'{L}: Listening and Recording each keep their own output',J(pg,"UI.sink")=='mbp')
        pg.click('#st11Auto');pg.wait_for_timeout(1200)
        ck(f'{L}: Fill automatically again goes back to the AMS-24',J(pg,"[UI.sink,UI.st11.R.o]")==['ams',None],J(pg,"[UI.sink,UI.st11.R.o]"))
        pg.click('#st11Seg [data-st11m="listen"]');pg.wait_for_timeout(900)
        # the input chosen by hand: armed tracks follow
        R(pg,"(window.__t.arm||armTrack(window.__t),0)");pg.wait_for_timeout(1500);old=R(pg,"window.__t._micRaw&&window.__t._micRaw.id")
        pg.select_option('#ifdIn','mbpm');pg.wait_for_timeout(1200)
        ck(f'{L}: a new input is kept in the setup and armed tracks reopen on it',J(pg,"[UI.inDev,UI.st11.R.i]")==['mbpm','mbpm'] and R(pg,"window.__t._micRaw&&window.__t._micRaw.id")!=old,J(pg,"[UI.inDev,UI.st11]"))
        R(pg,"(armTrack(window.__t),0)");pg.wait_for_timeout(1000);R(pg,"(UI.st11.R={o:null,i:null},0)")
        R(pg,"ST11.go('listen',{})");pg.wait_for_timeout(800)
        # the arm setting
        pg.select_option('#st11Arm','off');pg.wait_for_timeout(200);R(pg,"armTrack(window.__t)");pg.wait_for_timeout(1000)
        ck(f'{L}: "never" leaves the setup alone',J(pg,"[UI.sink,UI.st11.on,UI.st11arm]")==['gry','listen','off'])
        R(pg,"armTrack(window.__t)");pg.wait_for_timeout(600)
        pg.select_option('#st11Arm','any');R(pg,"(()=>{const t=mkTrack('inst',Object.keys(PRESETS)[0],'Keys');S.tracks.push(t);window.__k=t})()");R(pg,"armTrack(window.__k)");pg.wait_for_timeout(1200)
        ck(f'{L}: "any track" switches for an instrument too',J(pg,"[UI.sink,UI.st11.on]")==['ams','rec'])
        R(pg,"armTrack(window.__k)");pg.wait_for_timeout(1200)
        ck(f'{L}: and back when it is disarmed',J(pg,"[UI.sink,UI.st11.on]")==['gry','listen'])
        pg.select_option('#st11Arm','audio');R(pg,"armTrack(window.__k)");pg.wait_for_timeout(900)
        ck(f'{L}: "an audio track" (recommended) leaves instruments alone',J(pg,"[UI.sink,UI.st11.on]")==['gry','listen']);R(pg,"armTrack(window.__k)")
        # table, reset, search
        R(pg,"(document.getElementById('st11Arm').value='off',document.getElementById('st11Arm').onchange())");ck(f'{L}: reset puts the arm setting back to the recommended one',R(pg,"SETT.reset('armSwitch')") and R(pg,"UI.st11arm")=='audio')
        ck(f'{L}: Setup in use is a table row whose value reads from the switch',R(pg,"SETT.val('setupNow')")=='listen' and R(pg,"SETT.isDefault('setupNow')")==True)
        for q,want in (('listen through','Output device'),('record from','Record from'),('recording setup','Setup in use'),('arm','Switch to Recording when I arm'),('input device','Input device'),('microphone','Input device')):
            r=search(pg,q);ck(f'{L}: search "{q}" finds {want}',want in r,r)
        R(pg,"play.on&&stop()")
        ck(f'{L}: no console errors',errs==[],errs)
        c.close()
    # Windows: Chromium's names, the Communications entries, pairing by name
    c=b.new_context(viewport={'width':1400,'height':900},permissions=['microphone']);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]))
    pg.route('https://app.test/**',serve)
    pg.add_init_script(fake(WIN)+"Object.defineProperty(navigator,'platform',{get:()=>'Win32'});if(!sessionStorage.getItem('t11w')){sessionStorage.setItem('t11w','1');localStorage.setItem('audiolab-ui',JSON.stringify({order:['arr','fx','tr','map'],splash:false,lat3:1,sink:'ifi'}))}")
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(2500)
    R(pg,"(ensureCtx(),openSettings('audio'))");pg.wait_for_timeout(1200)
    ck('windows: the Recording setup pairs "Microphone (Zoom AMS-24)" with "Speakers (Zoom AMS-24)" and skips Realtek',J(pg,"ST11.rec()")=={'o':'zout','i':'zin','oa':True,'ia':True},J(pg,"ST11.rec()"))
    ck('windows: the Communications entries are not offered',R(pg,"![...document.querySelectorAll('#outSel option,#ifdIn option')].some(o=>o.value==='communications'||/^Communications/.test(o.textContent))"))
    ck('windows: Listen through shows the iFi',R(pg,"document.getElementById('st11LN').textContent")=='Speakers (iFi (by AMR) HD USB Audio)')
    R(pg,"(()=>{const t=mkTrack('audio',null,'Gtr');S.tracks.push(t);return armTrack(t)})()");pg.wait_for_timeout(1500)
    ck('windows: arming switches to the AMS-24 for both',J(pg,"[UI.sink,UI.inDev,UI.st11.on]")==['zout','zin','rec'])
    ck('windows: the sentence names one device and one clock',R(pg,"document.getElementById('st11Why').textContent").startswith('Recording: Zoom AMS-24 records and plays') and 'share one clock' in R(pg,"document.getElementById('st11Why').textContent"),R(pg,"document.getElementById('st11Why').textContent"))
    pg.locator('#set .setw').screenshot(path=f'{OUT}/s11_windows.png')
    ck('windows: no console errors',errs==[],errs)
    c.close();b.close()
print(f'taskST_S11: {N[1]} of {N[0]} passed')
if FAIL:print('failed:',FAIL);sys.exit(1)
