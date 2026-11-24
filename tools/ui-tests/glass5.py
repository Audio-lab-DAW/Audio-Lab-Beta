import sys,json
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1600,'height':1000})
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(40000)
    r=pg.evaluate("""async()=>{window.AudioLab.run("(()=>{UI.lite=false;document.body.classList.remove('lite');applyTrans()})()");await new Promise(r=>setTimeout(r,800));
     const fx=document.getElementById('fx'),dot=document.createElement('div');dot.style.cssText='position:absolute;left:40px;top:60px;width:30px;height:30px;background:#f55;z-index:5';fx.appendChild(dot);
     const run=async()=>{const iv=[];let last=performance.now(),t0=last;await new Promise(res=>{const f=()=>{const n=performance.now();iv.push(n-last);last=n;dot.style.left=(40+((n-t0)/10)%%300)+'px';if(n-t0<3000)requestAnimationFrame(f);else res()};requestAnimationFrame(f)});return +(iv.reduce((a,b)=>a+b,0)/iv.length).toFixed(1)};
     const o={};o.lensBlur=await run();const keep=fx.style.backdropFilter;
     fx.style.backdropFilter='blur(9px) saturate(1.72)';o.blurOnly=await run();
     fx.style.backdropFilter='blur(18px) saturate(1.72)';o.blur18=await run();
     fx.style.backdropFilter='none';o.none=await run();
     fx.style.backdropFilter=keep;for(const id of ['hglass','tr']){document.getElementById(id).style.backdropFilter='none'}o.lensBlur_onlyFx=await run();
     return o}""".replace('%%','%'))
    print(json.dumps(r));b.close()
