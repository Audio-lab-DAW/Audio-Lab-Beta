import sys,json
from playwright.sync_api import sync_playwright
src=open(sys.argv[1],encoding='utf-8').read()
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1600,'height':1000});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1,lite:false,liteAuto:false}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(12000)
    r=pg.evaluate("""async()=>{const A=window.AudioLab;const info=A.run("JSON.stringify({v:VERSION,lite:UI.lite,rf:typeof RFX==='object'?[...RFX.entries()].map(([el,o])=>[el.id||el.className,el.offsetWidth,el.offsetHeight,(o.img.getAttribute('href')||'').length]):'gone (v0.228, glass step 3)'})");
     A.run("(()=>{UI.lite=false;document.body.classList.remove('lite');applyTrans();openSettings()})()");await new Promise(r=>setTimeout(r,1500));
     const w=document.querySelector('.sheet.setw');const run=async(move)=>{const iv=[];let last=performance.now(),t0=last;await new Promise(res=>{const f=()=>{const n=performance.now();iv.push(n-last);last=n;if(move&&w){const t=(n-t0)/1000;w.style.translate=(Math.sin(t*3)*300).toFixed(1)+'px '+(Math.cos(t*2)*120).toFixed(1)+'px'}if(n-t0<4000)requestAnimationFrame(f);else res()};requestAnimationFrame(f)});iv.sort((a,b)=>a-b);const m=iv.reduce((a,b)=>a+b,0)/iv.length;return {frames:iv.length,mean:+m.toFixed(2),p95:+iv[Math.floor(iv.length*.95)].toFixed(1)}};
     const idle=await run(false),drag=await run(true);const bf=getComputedStyle(document.getElementById('fx')).backdropFilter;if(w)w.style.translate='';return {v:JSON.parse(info).v,win:!!w,bf,idle,drag}}""")
    print(json.dumps(r));
    if len(sys.argv)>2: pg.screenshot(path=sys.argv[2])
    print(errs[:3]);b.close()
