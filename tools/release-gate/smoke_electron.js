/* Release gate, start-up smoke test (task HF1). The real desktop app (Electron with desktop/main.js and desktop/app/index.html),
   at the user's size (2194 x 1139 CSS px at 1.75x), the Fractals song open, left alone for a while. Records every change of
   track state nobody asked for (solo, mute, arm, the selected track, clip and master), every synthetic (untrusted) click, key or
   pointer event, every change() call with where it came from, every MIDI message the app sends, and every console error.
   MIDI scenarios: Web MIDI is replaced in the page by a fake with the ports of the scenario (none, a plain keyboard, a Push 1 on
   both ports, an IAC-like loop-back pair that echoes what AudioLab sends straight back, ports named like the user's Mac).
     xvfb-run -a -s "-screen 0 4000x2200x24" node tools/release-gate/smoke_electron.js [--desktop dir] [--secs 60] [--scen a,b] [--json out.json]
   Exit code 0 when every scenario is clean. */
const { _electron } = require('playwright');
const path = require('path'), os = require('os'), fs = require('fs');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const DIR = path.resolve(arg('desktop', path.join(__dirname, '..', '..', 'desktop')));
const SECS = +arg('secs', 60);
const WANDER = arg('wander', '1') !== '0';
const WINS = arg('windows', '0') === '1';
const FAST = arg('fast', '0') === '1';  /* no frame-rate limit (a 240 Hz display runs requestAnimationFrame 4 times as often) */
const ALL = ['real', 'none', 'keyboard', 'push1', 'push1-loop', 'push1-loop-on', 'loopback', 'macnames', 'mackie-loop', 'mackie-loop-on', 'noise', 'loopback-maps', 'iac-push', 'iac-push-short'];
const SCEN = arg('scen', ALL.join(',')).split(',').filter(Boolean);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* the ports of each scenario: [name, manufacturer, kind]; kind 'loop' pairs an output with the input of the same name: whatever
   AudioLab sends to it comes straight back (what the IAC driver, a DAW's virtual port or a MIDI-thru on a cable does) */
const PORTS = {
  none: { ins: [], outs: [] },
  keyboard: { ins: [['Arturia KeyStep 37', 'Arturia']], outs: [['Arturia KeyStep 37', 'Arturia']] },
  push1: { ins: [['Ableton Push Live Port', 'Ableton'], ['Ableton Push User Port', 'Ableton']], outs: [['Ableton Push Live Port', 'Ableton'], ['Ableton Push User Port', 'Ableton']] },
  'push1-loop': { ins: [['Ableton Push Live Port', 'Ableton'], ['Ableton Push User Port', 'Ableton']], outs: [['Ableton Push Live Port', 'Ableton'], ['Ableton Push User Port', 'Ableton']], loop: true },
  'push1-loop-on': { ins: [['Ableton Push Live Port', 'Ableton'], ['Ableton Push User Port', 'Ableton']], outs: [['Ableton Push Live Port', 'Ableton'], ['Ableton Push User Port', 'Ableton']], loop: true, surf: ['Ableton Push Live Port'] },
  'mackie-loop-on': { ins: [['X-Touch', 'Behringer']], outs: [['X-Touch', 'Behringer']], loop: true, surf: ['X-Touch'] },
  /* a port that sends random messages (a USB DAC whose MIDI pins float, a broken cable): every channel message kind */
  noise: { ins: [['iFi (by AMR) HD USB Audio', 'iFi']], outs: [['iFi (by AMR) HD USB Audio', 'iFi']], noise: true },
  /* the IAC loop with mappings an older MIDI learn left for "any device" (they send feedback): what a long-time user may have */
  'loopback-maps': { ins: [['IAC Driver Bus 1', 'Apple Inc.']], outs: [['IAC Driver Bus 1', 'Apple Inc.']], loop: true, maps: true },
  /* the user's Mac (27 Nov 2026, the v0.250 glitch): IAC Driver online with two ports made for Cubase; a port named "Ableton Push..." loops back */
  'iac-push': { ins: [['IAC Driver Ableton Push to Cubase', 'Apple Inc.'], ['IAC Driver nanoKey2 to Cubase', 'Apple Inc.']], outs: [['IAC Driver Ableton Push to Cubase', 'Apple Inc.'], ['IAC Driver nanoKey2 to Cubase', 'Apple Inc.']], loop: true },
  'iac-push-short': { ins: [['Ableton Push to Cubase', 'Apple Inc.'], ['nanoKey2 to Cubase', 'Apple Inc.']], outs: [['Ableton Push to Cubase', 'Apple Inc.'], ['nanoKey2 to Cubase', 'Apple Inc.']], loop: true },
  loopback: { ins: [['IAC Driver Bus 1', 'Apple Inc.']], outs: [['IAC Driver Bus 1', 'Apple Inc.']], loop: true },
  macnames: { ins: [['IAC Driver Bus 1', 'Apple Inc.'], ['Network Session 1', 'Apple Inc.'], ['eqMac', 'eqMac'], ['BlackHole 2ch', 'Existential Audio Inc.'], ['Cubase System Sound Link', 'Steinberg']], outs: [['IAC Driver Bus 1', 'Apple Inc.'], ['Network Session 1', 'Apple Inc.'], ['Cubase System Sound Link', 'Steinberg']], loop: true },
  'mackie-loop': { ins: [['X-Touch', 'Behringer'], ['IAC Driver Bus 1', 'Apple Inc.']], outs: [['X-Touch', 'Behringer'], ['IAC Driver Bus 1', 'Apple Inc.']], loop: true },
};

/* the page side: fake Web MIDI (unless 'real') and the recorders. Runs before the app's own script. */
const initScript = (scen) => `(()=>{const SC=${JSON.stringify(scen)},P=${JSON.stringify(PORTS[scen] || null)};
window.__HF={scen:SC,ev:[],sent:[],recv:0,errs:[],chg:[],cmd:[]};const H=window.__HF,now=()=>Math.round(performance.now());
const log=(k,x)=>{if(H.ev.length<4000)H.ev.push([now(),k,x])};
for(const t of['click','pointerdown','pointerup','mousedown','keydown','dblclick','contextmenu','wheel'])addEventListener(t,e=>{if(!e.isTrusted)log('synthetic '+t,(e.target&&(e.target.id||e.target.className||e.target.tagName))+'')},true);
addEventListener('error',e=>H.errs.push(String(e.message).slice(0,300)));addEventListener('unhandledrejection',e=>H.errs.push('rejection '+String(e.reason).slice(0,300)));
const ce=console.error;console.error=function(){try{H.errs.push([...arguments].map(a=>a&&a.stack?String(a.stack).slice(0,300):String(a).slice(0,300)).join(' '))}catch(e){}return ce.apply(this,arguments)};
if(P){class Port extends EventTarget{constructor(n,m,t,i){super();this.id=t+i+':'+n;this.name=n;this.manufacturer=m;this.type=t;this.state='connected';this.connection='open';this.version='1'}open(){return Promise.resolve(this)}close(){return Promise.resolve(this)}}
 class In extends Port{constructor(n,m,i){super(n,m,'input',i);this._h=null}set onmidimessage(f){this._h=f}get onmidimessage(){return this._h}_recv(d){H.recv++;const ev={data:new Uint8Array(d),timeStamp:performance.now()};if(this._h)try{this._h(ev)}catch(e){H.errs.push('onmidimessage '+e)}}}
 const ins=new Map(),outs=new Map();P.ins.forEach(([n,m],i)=>{const p=new In(n,m,i);ins.set(p.id,p)});
 class Out extends Port{constructor(n,m,i){super(n,m,'output',i)}send(d){const a=Array.from(d);if(H.sent.length<20000)H.sent.push([now(),this.name,a.slice(0,12)]);if(P.loop){const back=[...ins.values()].find(x=>x.name===this.name);if(back&&H.recv<${+(process.env.HF_ECHO_MAX||20000)})setTimeout(()=>back._recv(a),${+(process.env.HF_ECHO_MS||3)})}}clear(){}}
 P.outs.forEach(([n,m],i)=>{const p=new Out(n,m,i);outs.set(p.id,p)});
 const acc={inputs:ins,outputs:outs,sysexEnabled:true,onstatechange:null,addEventListener(){},removeEventListener(){}};
 Object.defineProperty(navigator,'requestMIDIAccess',{value:()=>Promise.resolve(acc),configurable:true});
 if(P.noise){let sd=7;const rnd=n=>{sd=(sd*16807)%2147483647;return sd%n};setTimeout(()=>{setInterval(()=>{const p=[...ins.values()][0];if(!p)return;const st=[0x80,0x90,0xA0,0xB0,0xC0,0xD0,0xE0][rnd(7)]|rnd(16);p._recv(st>=0xC0&&st<0xE0?[st,rnd(128)]:[st,rnd(128),rnd(128)])},25)},12000)}
 window.__HF.midiIn=(name,d)=>{const p=[...ins.values()].find(x=>x.name===name);if(p)p._recv(d)}}
})()`;

/* a snapshot of everything the user would see change by itself */
const SNAP = `(()=>{const T=(typeof S!=='undefined'&&S&&S.tracks)||[];return JSON.stringify({tr:T.map(t=>[t.name,t.solo?1:0,t.mute?1:0,t.arm?1:0,t.rec?1:0].join(':')),selT:typeof selT!=='undefined'?selT:null,selC:typeof selC!=='undefined'?selC:null,
  sels:typeof SELCS!=='undefined'?SELCS.size:0,selM:typeof selMaster!=='undefined'?!!selMaster:null,play:typeof play!=='undefined'&&play.on?1:0,master:typeof S!=='undefined'?S.master:null})})()`;

const WINLIST = [['Settings', "openSettings()"], ['Mixer', "SCM.get('mixer').run()"], ['Devices off and on', "SCM.get('devs').run()"], ['Keyboard shortcuts', "SCM.get('keys').run()"],
  ['Controllers', "SCM.get('ctl.mappings').run()"], ['Instrument browser', "SCM.get('browser').run()"], ['Effects browser', "SCM.get('fxbrowser').run()"], ['Time Machine', "SCM.get('tm').run()"],
  ['Frequency map', "SCM.get('ni.freqMap').run()"], ['Kick and bass lab', "SCM.get('ni.kickBass').run()"], ['Clip explainer', "SCM.get('ni.clipExplain').run()"], ['Export', "SCM.get('export').run()"], ['About', "showAbout()"]];
async function windows(app, page) {
  const out = { fail: [], ok: [] }, R = (c) => page.evaluate((c) => { try { return AudioLab.run(c); } catch (e) { return 'ERR ' + String(e).slice(0, 200); } }, c);
  const errsN = async () => page.evaluate(() => window.__HF.errs.length);
  const closeAll = async () => { for (let i = 0; i < 3; i++) { await page.keyboard.press('Escape'); await sleep(150); } await R("try{SCM.get('closewins').run()}catch(e){};for(const m of document.querySelectorAll('.modal'))if(!m.hidden&&m.id!=='uywM')m.hidden=true;0"); await sleep(300); };
  for (const [name, code] of WINLIST) {
    const e0 = await errsN(); const r = await R(code + ';0'); await sleep(1200);
    const vis = await page.evaluate(() => document.querySelectorAll('.fwin:not([hidden]),.modal:not([hidden]),.abxw,.spov,#uywM').length);
    await closeAll(); if (name === 'Devices off and on') { await R(WINLIST[2][1]); await sleep(400); }
    const errs = (await page.evaluate((n) => window.__HF.errs.slice(n), e0));
    if (typeof r === 'string' && r.startsWith('ERR')) out.fail.push(name + ': ' + r); else if (errs.length) out.fail.push(name + ': ' + errs.join(' | ').slice(0, 300)); else out.ok.push(name + (vis ? '' : ' (nothing visible)'));
  }
  /* the update window with 40 long lines of notes, at the user's size and in a small window */
  const long = Array.from({ length: 40 }, (_, i) => 'Line ' + (i + 1) + ': ' + 'a long release note that goes on and on about what changed in this version, '.repeat(4)).join('\n');
  for (const [w, h] of [[2194, 1139], [1280, 720], [900, 560]]) {
    await app.evaluate(({ BrowserWindow }, a) => { BrowserWindow.getAllWindows()[0].setContentSize(a[0], a[1]); }, [w, h]); await sleep(800);
    const e0 = await errsN();
    await R("localStorage.removeItem('al-upd-later');UYW.closed='';uywShow({kind:'ota',to:'9.999',notes:" + JSON.stringify(long) + "});0"); await sleep(900);
    const chk = await page.evaluate(() => { const m = document.getElementById('uywM'); if (!m) return { open: false };
      const bs = [...m.querySelectorAll('.uywb button')].map((b) => { const r = b.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, hit = document.elementFromPoint(cx, cy);
        return { t: b.textContent, inView: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth && r.height > 10, hit: !!hit && (hit === b || b.contains(hit)) }; });
      const items = m.querySelectorAll('.uywnl li').length, sc = m.querySelector('.uywsc'); return { open: true, bs, items, first: (m.querySelector('.uywnl li') || {}).textContent || '', scrolls: !!sc && sc.scrollHeight > sc.clientHeight }; });
    const good = chk.open && chk.bs.length >= 2 && chk.bs.every((b) => b.inView && b.hit) && chk.items <= 9 && /^Line 1:/.test(chk.first);
    (good ? out.ok : out.fail).push('update window ' + w + 'x' + h + ': ' + JSON.stringify(chk).slice(0, 400));
    const later = await page.evaluate(() => { const b = [...document.querySelectorAll('#uywM .uywb button')].find((x) => x.dataset.uy === 'later'); return b ? (b.getBoundingClientRect().x + b.getBoundingClientRect().width / 2) + ',' + (b.getBoundingClientRect().y + b.getBoundingClientRect().height / 2) : null; });
    if (later) { const [x, y] = later.split(',').map(Number); await page.mouse.click(x, y); await sleep(400); }
    const closed = await page.evaluate(() => !document.getElementById('uywM'));
    (closed ? out.ok : out.fail).push('update window ' + w + 'x' + h + ': Later closes it' + (closed ? '' : ' FAILED'));
    const errs = await page.evaluate((n) => window.__HF.errs.slice(n), e0); if (errs.length) out.fail.push('update window errors: ' + errs.join(' | ').slice(0, 300));
  }
  await R("localStorage.removeItem('al-upd-later');0");
  await app.evaluate(({ BrowserWindow }) => { BrowserWindow.getAllWindows()[0].setContentSize(2194, 1139); });
  return out;
}

async function run(scen) {
  const ud = fs.mkdtempSync(path.join(os.tmpdir(), 'alhf-'));
  const exe = process.env.ELECTRON || require(path.join(DIR, 'node_modules', 'electron'));
  const app = await _electron.launch({ executablePath: exe, args: ['--no-sandbox', '--force-device-scale-factor=1.75'].concat(FAST ? ['--disable-frame-rate-limit', '--disable-gpu-vsync'] : [], [DIR]), env: { ...process.env, XDG_CONFIG_HOME: ud, HOME: ud } });
  const res = { scen, errs: [], pageerr: [], changes: [], ev: [], sent: 0, sentEcho: 0, chg: [], frames: null, toasts: [] };
  try {
    const page = await app.firstWindow();
    page.on('pageerror', (e) => res.pageerr.push(String(e).slice(0, 300)));
    if (scen !== 'real') await app.context().addInitScript(initScript(scen));
    else await app.context().addInitScript(initScript('real'));
    await app.evaluate(({ BrowserWindow }) => { const w = BrowserWindow.getAllWindows()[0]; w.unmaximize(); w.setFullScreen(false); w.setContentSize(2194, 1139); });
    await page.reload();
    await page.waitForFunction(() => window.AudioLab && window.AudioLab.version && window.audiolabHost && window.audiolabHost.ready && window.audiolabHost.ready(), null, { timeout: 120000 });
    res.version = await page.evaluate(() => window.AudioLab.version);
    await page.evaluate(() => { const r = document.getElementById('liteNote'); if (r) r.remove(); return AudioLab.run('openDemoFractals()'); });
    await sleep(9000);
    /* a scenario where the user turned a device on as a control surface (from v0.261, task HF1; older builds take surfaces by name anyway) */
    if (PORTS[scen] && PORTS[scen].surf) { await page.evaluate((n) => AudioLab.run("typeof ctlSurfSet==='function'&&" + JSON.stringify(n) + ".forEach(x=>ctlSurfSet(x,true))"), PORTS[scen].surf); await sleep(3000); }
    if (PORTS[scen] && PORTS[scen].maps) { await page.evaluate(() => AudioLab.run(`{const T=S.tracks.filter(t=>t.kind!=='group'),mk=(num,target,type)=>({id:'mx'+num,dev:'*',type:type||'cc',ch:0,num,target,min:0,max:1,take:'jump',enc:'abs',fb:true,scope:'global'});
      const st=ctlG();st.maps.push(mk(7,'ms'),mk(10,'hp:'+T[1].id),mk(11,'hd:'+T[2].id),mk(12,'hd:'+T[3].id),mk(60,'hp:'+T[2].id,'note'),mk(13,'hp:'+T[3].id));ctlDirty();for(const d of CTL.devs.values())ctlFbDev(d);JSON.stringify(st.maps.length)}`)); await sleep(3000); }
    res.halted = await page.evaluate(() => AudioLab.run("typeof CTL!=='undefined'?[...CTL.devs.values()].filter(d=>d.halt).map(d=>d.name+':'+d.halt):[]"));
    // the recorders that need the app's functions: who calls changed() and which commands run
    await page.evaluate(() => {
      const H = window.__HF; const where = () => { const s = (new Error().stack || '').split('\n').slice(3, 7).map((x) => x.trim().replace(/\(.*index\.html:/, '(:')).join(' < '); return s; };
      window.__HFwhere = where; AudioLab.run('{const _c=changed;changed=function(){const H=window.__HF;if(H.chg.length<400)H.chg.push([Math.round(performance.now()),window.__HFwhere()]);return _c.apply(this,arguments)}}');
      const SCM = AudioLab.run('SCM'); if (SCM) for (const [id, a] of SCM) { if (typeof a.run !== 'function' || a.__hf) continue; const r = a.run; a.run = function () { H.cmd.push([Math.round(performance.now()), id]); return r.apply(this, arguments); }; a.__hf = 1; }
      const tt = document.getElementById('toast'); if (tt) new MutationObserver(() => { if (tt.textContent) H.ev.push([Math.round(performance.now()), 'toast', tt.textContent.slice(0, 120)]); }).observe(tt, { childList: true, characterData: true, subtree: true });
      H.ev = H.ev.filter((e) => e[1] !== 'toast'); H.errs0 = H.errs.length; H.t0 = performance.now();
      H.frames = []; let last = performance.now(); const f = (t) => { H.frames.push(t - last); last = t; if (H.frames.length < 100000) requestAnimationFrame(f); }; requestAnimationFrame(f);
    });
    const base = JSON.parse(await page.evaluate((c) => AudioLab.run(c), SNAP)); res.base = base;
    let prev = base; const t0 = Date.now();
    while (Date.now() - t0 < SECS * 1000) {
      await sleep(250);
      const s = JSON.parse(await page.evaluate((c) => AudioLab.run(c), SNAP));
      if (JSON.stringify(s) !== JSON.stringify(prev)) {
        const d = {}; for (const k of Object.keys(s)) if (JSON.stringify(s[k]) !== JSON.stringify(prev[k])) d[k] = k === 'tr' ? s.tr.filter((x, i) => x !== prev.tr[i]) : s[k];
        res.changes.push([((Date.now() - t0) / 1000).toFixed(2), d]);
      }
      prev = s;
    }
    /* phase 2: the mouse wanders over the whole window without a click (hover only); nothing the user would see as state may change */
    if (WANDER) {
      const t1 = Date.now(); res.wander = [];
      for (let y = 8; y < 1132; y += 37) {
        for (let x = 6; x < 2190; x += 45) await page.mouse.move(x, (Math.floor(x / 45) % 2) ? y : y + 12, { steps: 2 });
        const s = JSON.parse(await page.evaluate((c) => AudioLab.run(c), SNAP));
        if (JSON.stringify(s) !== JSON.stringify(prev)) { const d = {}; for (const k of Object.keys(s)) if (JSON.stringify(s[k]) !== JSON.stringify(prev[k])) d[k] = k === 'tr' ? s.tr.filter((x, i) => x !== prev.tr[i]) : s[k]; res.changes.push(['hover y=' + y, d]); }
        prev = s;
      }
      await page.mouse.move(1100, 400); await sleep(3000);
      const s = JSON.parse(await page.evaluate((c) => AudioLab.run(c), SNAP)); if (JSON.stringify(s) !== JSON.stringify(prev)) res.changes.push(['after hover', s]);
      res.wanderSecs = (Date.now() - t1) / 1000;
    }
    const H = await page.evaluate(() => { const H = window.__HF; const fr = H.frames.slice(10).sort((a, b) => a - b); const q = (p) => fr.length ? +fr[Math.floor(p * (fr.length - 1))].toFixed(2) : null;
      return { errs: H.errs, errs0: H.errs0 || 0, ev: H.ev, sent: H.sent.length, sentHead: H.sent.slice(0, 12), recv: H.recv, chg: H.chg, cmd: H.cmd, frames: { n: fr.length, p50: q(.5), p95: q(.95), p99: q(.99) }, t0: H.t0 }; });
    res.errs = H.errs; res.ev = H.ev; res.sent = H.sent; res.sentHead = H.sentHead; res.recv = H.recv; res.chg = H.chg.filter((c) => c[0] > H.t0); res.cmd = H.cmd; res.frames = H.frames; res.errsIdle = H.errs.slice(H.errs0);
    res.shot = path.join(os.tmpdir(), 'alhf-' + scen + '.png'); await page.screenshot({ path: res.shot });
    res.dupIds = await page.evaluate(() => { const c = new Map(); for (const e of document.querySelectorAll('[id]')) c.set(e.id, (c.get(e.id) || 0) + 1); return [...c].filter((x) => x[1] > 1).map((x) => x[0] + ' x' + x[1]); });
    /* phase 3 (step d of the gate): open and close every main window; the update window with very long notes keeps its buttons in view */
    if (WINS) res.wins = await windows(app, page);
  } catch (e) { res.crash = String(e).slice(0, 500); }
  try { await app.evaluate(({ app }) => app.exit(0)); } catch (e) { /* closed */ }
  try { await app.close(); } catch (e) { /* closed */ }
  /* a loop that keeps going (over 100 messages came back and no device was stopped) fails even when nothing visible changed yet */
  res.loopOn = !!(PORTS[scen] && PORTS[scen].loop && res.recv >= 100 && !(res.halted && res.halted.length));
  res.clean = !res.loopOn && !(res.wins && res.wins.fail.length) && !(res.dupIds && res.dupIds.length) && !res.crash && !res.changes.length && !res.errs.length && !res.pageerr.length && !res.ev.some((e) => /^synthetic/.test(e[1])) && !(res.cmd || []).length && !(res.chg || []).length;
  return res;
}

(async () => {
  const out = [];
  for (const s of SCEN) {
    const r = await run(s); out.push(r);
    console.log((r.clean ? 'ok   ' : 'FAIL ') + s.padEnd(12) + ' v' + r.version + '  state changes ' + r.changes.length + ', errors ' + (r.errs.length + r.pageerr.length) + ', change() ' + (r.chg || []).length + ', commands ' + (r.cmd || []).length + ', MIDI sent ' + r.sent + ' recv ' + r.recv + ', frames ' + JSON.stringify(r.frames) + (r.loopOn ? ' A MIDI LOOP KEEPS GOING' : '') + (r.halted && r.halted.length ? ' stopped devices ' + r.halted.join(', ') : '') + (r.crash ? ' CRASH ' + r.crash : ''));
    for (const c of r.changes.slice(0, 6)) console.log('       change at ' + c[0] + ' s: ' + JSON.stringify(c[1]).slice(0, 300));
    for (const c of (r.chg || []).slice(0, 4)) console.log('       change() from ' + c[1].slice(0, 300));
    for (const c of (r.cmd || []).slice(0, 4)) console.log('       command ' + c[1]);
    for (const e of r.errs.concat(r.pageerr).slice(0, 5)) console.log('       error ' + e.slice(0, 300));
    for (const e of r.ev.filter((e) => /^synthetic/.test(e[1])).slice(0, 4)) console.log('       ' + e[1] + ' on ' + e[2]);
    if (r.dupIds && r.dupIds.length) console.log('       duplicate ids in the page: ' + r.dupIds.join(', '));
    if (r.wins) { console.log('       windows: ' + r.wins.ok.length + ' ok' + (r.wins.fail.length ? ', ' + r.wins.fail.length + ' failed' : '')); for (const f of r.wins.fail) console.log('       window FAIL ' + f.slice(0, 400)); }
    if (r.sentHead && r.sentHead.length) console.log('       first MIDI out ' + JSON.stringify(r.sentHead.slice(0, 6)));
  }
  const j = arg('json'); if (j) fs.writeFileSync(j, JSON.stringify(out, null, 1));
  const bad = out.filter((r) => !r.clean).map((r) => r.scen);
  console.log(bad.length ? 'FAILED: ' + bad.join(', ') : 'all scenarios clean'); process.exit(bad.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
