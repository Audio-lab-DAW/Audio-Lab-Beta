import sys,json
from playwright.sync_api import sync_playwright
wl=open(sys.argv[1]).read()
names=sys.argv[2].split(',')
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page()
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body='<html></html>'))
    pg.goto('https://app.test/index.html')
    for nm in names:
        r=pg.evaluate("""async([wl,nm])=>{const sr=48000,T=75,c=new OfflineAudioContext(2,sr*T,sr);await c.audioWorklet.addModule(URL.createObjectURL(new Blob([wl],{type:'text/javascript'})));
        const b=c.createBuffer(2,sr*T,sr);for(let ch=0;ch<2;ch++){const d=b.getChannelData(ch);for(let i=0;i<sr*.5;i++)d[i]=(Math.random()*2-1)*.5}
        const s=c.createBufferSource();s.buffer=b;const errs=[];
        for(let k=0;k<12;k++){const n=new AudioWorkletNode(c,nm,{numberOfInputs:1,numberOfOutputs:1,outputChannelCount:[2],processorOptions:{p:{}}});n.onprocessorerror=e=>errs.push(1);s.connect(n);n.connect(c.destination)}
        s.start();const ts=[];for(let t=3;t<T;t+=3)c.suspend(t).then(()=>{ts.push(performance.now());c.resume()});
        const t0=performance.now();await c.startRendering();ts.push(performance.now());const o=[];let q=t0;for(const t of ts){o.push(Math.round(t-q));q=t}return [o,errs.length]}""",[wl,nm])
        print(nm.ljust(10),r[1],' '.join(str(x).rjust(4) for x in r[0]),flush=True)
    b.close()
