import sys,json
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1600,'height':1000})
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(40000)
    r=pg.evaluate("""async()=>{const A=window.AudioLab;A.run("(()=>{UI.lite=false;document.body.classList.remove('lite');applyTrans()})()");await new Promise(r=>setTimeout(r,800));
     const run=async()=>{const iv=[];let last=performance.now(),t0=last;await new Promise(res=>{const f=()=>{const n=performance.now();iv.push(n-last);last=n;if(n-t0<3000)requestAnimationFrame(f);else res()};requestAnimationFrame(f)});return +(iv.reduce((a,b)=>a+b,0)/iv.length).toFixed(1)};
     const o={};o.glassOn=await run();
     // which canvases are drawn at idle
     const cnt=new Map(),P=CanvasRenderingContext2D.prototype,names=['clearRect','fillRect','drawImage','stroke','fill','putImageData'],orig={};for(const m of names){orig[m]=P[m];P[m]=function(){const c=this.canvas,k=(c.id||c.className||'?')+' '+c.width+'x'+c.height;cnt.set(k,(cnt.get(k)||0)+1);return orig[m].apply(this,arguments)}}
     await new Promise(r=>setTimeout(r,2000));for(const m of names)P[m]=orig[m];o.canvasOpsIn2s=[...cnt.entries()].sort((a,b)=>b[1]-a[1]).slice(0,8);
     const st=document.createElement('style');st.textContent='*{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}';document.head.appendChild(st);for(const el of document.querySelectorAll('[style*=backdrop]'))el.style.backdropFilter='none';await new Promise(r=>setTimeout(r,500));o.glassOff=await run();return o}""")
    print(json.dumps(r));b.close()
