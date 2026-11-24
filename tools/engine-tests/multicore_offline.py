from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page()
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body='<html></html>'))
    pg.goto('https://app.test/index.html')
    print(pg.evaluate("""async()=>{const one=()=>{const c=new OfflineAudioContext(2,48000*20,48000);const o=c.createOscillator();o.type='sawtooth';let n=o;for(let i=0;i<150;i++){const f=c.createBiquadFilter();f.frequency.value=500+i*40;n.connect(f);n=f}n.connect(c.destination);o.start();return c.startRendering()};
    const o={cores:navigator.hardwareConcurrency};for(const k of [1,2,4]){const t=performance.now();await Promise.all(Array.from({length:k},one));o['x'+k]=Math.round(performance.now()-t)}return o}"""))
    b.close()
