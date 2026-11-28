/* Task LT-3b (lane J): fast MIDI notes for every worklet instrument and the Drum kit, recording by the MIDI time stamp, the Settings row.
   Run after `node desktop/scripts/sync-app.js` (or with desktop/app/index.html copied):
     xvfb-run -a node tools/ui-tests/taskLT_3b_electron.js [desktop dir] [--before old-index.html] [--json out.json]
   In the real desktop app (AL_LT_TEST=1: notes injected in the shell's listening window as a MIDI keyboard would send them):
   each instrument kind armed alone on a new track: played by the worklet or left to the page (Acid, Venom, Bouncing ball, the classic
   Sampler, a track with a chord device); the fast note's level against the page's own note (same key, same velocity); the Drum kit's
   pads the same way, its open hat choked by a closed hat; note to first sample during a 200 ms long task (a kit and an Orbit) before
   (the page's path) and after. In the browser: recording places a MIDI note by its Web MIDI time stamp while the page is busy (with
   --before, the same on the old build), the Settings row is not there. */
const { _electron, chromium } = require('playwright');
const path = require('path'), os = require('os'), fs = require('fs');
const argv = process.argv.slice(2);
const opt = (k) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : null);
const DIR = path.resolve(argv.find((a, i) => !a.startsWith('--') && !['--json', '--before'].includes(argv[i - 1])) || path.join(__dirname, '..', '..', 'desktop'));
const JS = opt('--json'), BEFORE = opt('--before');
const fail = []; const ok = (c, m, i) => { console.log((c ? 'ok   ' : 'FAIL ') + m + (i !== undefined ? ' ' + JSON.stringify(i) : '')); if (!c) fail.push(m); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const med = (a) => { const b = a.filter((x) => x != null).sort((x, y) => x - y); return b.length ? +b[Math.floor(b.length / 2)].toFixed(1) : null; };
const dB = (a, b) => +(20 * Math.log10(Math.max(a, 1e-9) / Math.max(b, 1e-9))).toFixed(2);
const OUT = { kinds: {}, pads: {}, lat: {}, rec: {} };
const HELP = `(()=>{window.__tapN=null;window.__A=null;
  window.__tap=(n)=>{if(window.__A)try{__tapN.disconnect(__A)}catch(e){}window.__A=ctx.createAnalyser();__A.fftSize=2048;n.connect(__A);window.__tapN=n;return 1};
  window.__pkFor=async(ms)=>{let m=0;const b=new Float32Array(2048),e=performance.now()+ms;while(performance.now()<e){__A.getFloatTimeDomainData(b);for(const x of b)m=Math.max(m,Math.abs(x));await new Promise(r=>setTimeout(r,12))}return m};
  window.__OT=()=>{const o=ctx.getOutputTimestamp();return{ct:o.contextTime,pt:o.performanceTime,to:performance.timeOrigin}};window.__VS=[];
  const _v=voiceOn;voiceOn=function(t,p,v){const r=_v.apply(this,arguments);if(r)__VS.push(ctx.currentTime+.002);return r};return 1})()`;
(async () => {
  const ud = fs.mkdtempSync(path.join(os.tmpdir(), 'allt3b-'));
  const exe = process.env.ELECTRON || require(path.join(DIR, 'node_modules', 'electron'));
  const app = await _electron.launch({ executablePath: exe, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required', DIR], env: { ...process.env, XDG_CONFIG_HOME: ud, AL_LT_TEST: '1' } });
  const page = await app.firstWindow(); const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 300)));
  page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource|fetching the script/.test(m.text())) errs.push('console: ' + m.text().slice(0, 300)); });
  await page.waitForFunction(() => window.AudioLab && window.AudioLab.version, null, { timeout: 90000 }); await sleep(3000);
  const R = (c) => page.evaluate((c) => AudioLab.run(c), c);
  const LTM = path.join(DIR, 'lt-midi.js'); const inject = (b) => app.evaluate((x, [f, b]) => process.mainModule.require(f).inject(b), [LTM, b]);
  ok(await R("!!document.getElementById('ltFmChk')&&STX.has('fastMidi')&&document.getElementById('ltFmChk').checked&&!!document.getElementById('ltFmChk').closest('label').title"), 'the Settings row "Fast MIDI notes" is there in the desktop app, on, with a tooltip');
  await R(`(async()=>{const r=document.getElementById('liteNote');if(r)r.remove();await openDemoFractals();return 1})()`); await sleep(2500);
  await R(`(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));ensureCtx();await ctx.resume();UI.kbPiano=false;CAPS=false;for(const t of S.tracks)t.arm=false;changed(true);
    ctlStart();await w(300);const g=CTL.profs.find(p=>p.id==='generic');window.__D={id:'lt-test',name:'LT Test Keys',man:'',inp:{name:'LT Test Keys'},out:null,prof:g,base:'LT Test Keys'};CTL.devs.set('lt-test',window.__D);return 1})()`);
  await R(HELP);
  /* one new track per instrument kind, armed alone */
  const arm = async (preset, extra) => {
    const r = await R(`(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));for(const t of S.tracks)t.arm=false;S.tracks=S.tracks.filter(t=>!t._lt3b);
      const t=mkTrack('inst','${preset}');t._lt3b=1;${extra || ''};S.tracks.push(t);t.arm=true;changed(true);syncGraph();await w(300);
      try{const h=voiceOn(t,48,.01);if(h)h.off(true)}catch(e){}await w(700);LTF.ins=new Set(['LT Test Keys']);ltFastEval();await w(900);ltFastEval();await w(900);ltFastEval();await w(400);
      const N=NODES.get(t.id);if(N&&N.in)__tap(N.in);window.__T=t;const f=LT_HOOKS.fastNotes();return JSON.stringify({id:t.id,f})})()`);
    return JSON.parse(r);
  };
  const fastNote = async (n, ms) => { const n0 = await R('LTF.n'); await inject([0x90, n, 100]); const pk = await R(`__pkFor(${ms || 450})`); await inject([0x80, n, 0]); await sleep(1300); return { played: (await R('LTF.n')) - n0, pk }; };
  const pageNote = async (n, ms) => { await R('UI.ltFast=false;ltFastEval();1'); await sleep(200); const s0 = await R('LTF.skip');
    await R(`ctlMsg(__D,new Uint8Array([0x90,${n},100]));1`); const pk = await R(`__pkFor(${ms || 450})`); await R(`ctlMsg(__D,new Uint8Array([0x80,${n},0]));1`); await sleep(1300);
    const sk = (await R('LTF.skip')) - s0; await R('UI.ltFast=undefined;ltFastEval();1'); await sleep(900); await R('ltFastEval();1'); await sleep(300); return { pk, sk }; };
  /* the page does not play a fast note again (it still gets it through its own Web MIDI) */
  const both = async (n) => { const s0 = await R("LTF.ins=new Set(['LT Test Keys']);LTF.skip"); await inject([0x90, n, 100]); await R(`ctlMsg(__D,new Uint8Array([0x90,${n},100]));1`); await sleep(120);
    const sk = (await R('LTF.skip')) - s0; await inject([0x80, n, 0]); await R(`ctlMsg(__D,new Uint8Array([0x80,${n},0]));1`); await sleep(900); return sk; };
  const KINDS = [['plant', '', 'al-poly'], ['saw', '', 'al-poly'], ['wtab', '', 'al-poly'], ['sampler', "t.inst.mode='grain'", 'al-grain'], ['emit', '', 'al-emit'], ['vgrain', '', 'al-vgrain'], ['vfm', '', 'al-vfm'],
    ['orb', '', 'al-orb'], ['sbass', '', 'al-sbs'], ['psyb', '', 'al-psb'], ['crk', '', 'al-crki']];
  for (const [pr, ex, proc] of KINDS) {
    const a = await arm(pr, ex); const tg = a.f.tracks.find((x) => x.id === a.id);
    const isFast = !!(tg && tg.ready && tg.kind === proc);
    let F = null, P = null, sk = null;
    if (isFast) { F = await fastNote(64); P = await pageNote(64); sk = await both(65); }
    OUT.kinds[pr + (ex ? ' grains' : '')] = { fast: isFast, kind: tg && tg.kind, fastPk: F && +F.pk.toFixed(4), pagePk: P && +P.pk.toFixed(4), dB: F && P ? dB(F.pk, P.pk) : null, played: F && F.played, pageSkipped: P && P.sk, twice: sk, why: (a.f.page.find((x) => x.id === a.id) || {}).why };
    ok(isFast && F.played === 1 && F.pk > 0.005 && P.pk > 0.005 && Math.abs(dB(F.pk, P.pk)) < 3 && sk === 1,
      `${pr}${ex ? ' (grains)' : ''}: played by the worklet (${proc}), as loud as the page's own note (${F ? dB(F.pk, P.pk) : '?'} dB), not played twice`, OUT.kinds[pr + (ex ? ' grains' : '')]);
  }
  /* left to the page */
  for (const [pr, ex, lbl] of [['acid', '', 'Acid'], ['venom', '', 'Venom'], ['bball', '', 'Bouncing ball'], ['sampler', '', 'the classic Sampler'], ['plant', "t.fx.push(mkFx('chord'));t.fx[t.fx.length-1].on=true", 'a Plant with a chord device']]) {
    let a; try { a = await arm(pr, ex); } catch (e) { a = { f: { tracks: [{ id: 0 }] }, id: -1, err: String(e) }; }
    const tg = a.f.tracks.find((x) => x.id === a.id);
    const s0 = await R('LTF.skip'); const n0 = await R('LTF.n'); await inject([0x90, 66, 100]); await R('ctlMsg(__D,new Uint8Array([0x90,66,100]));1'); const pk = await R('__pkFor(400)');
    await inject([0x80, 66, 0]); await R('ctlMsg(__D,new Uint8Array([0x80,66,0]));1'); await sleep(900);
    ok(!tg && (await R('LTF.n')) === n0 && (await R('LTF.skip')) === s0 && pk > 0.003, `${lbl}: left to the page, which plays it as before`, { pk, err: a.err });
  }
  /* the Drum kit */
  const k = await arm('drums');
  const kt = k.f.tracks.find((x) => x.id === k.id);
  ok(kt && kt.ready && kt.kind === 'kit' && kt.pads.length >= 14, 'the Drum kit is played by the worklet drum player (its pads)', kt);
  /* the page picks one of three takes of each pad at random (so does the worklet): for the comparison both get the same take */
  await R("for(const[k,v] of PADBUF)if(Array.isArray(v))PADBUF.set(k,[v[0],v[0],v[0]]);for(const o of LTF.tgt.values())o.sig='x';ltFastEval();1"); await sleep(800);
  for (const [n, nm] of [[60, 'kick'], [62, 'snare'], [63, 'clap'], [66, 'closed hat'], [70, 'open hat'], [73, 'crash']]) {
    const F = await fastNote(n, 350), P = await pageNote(n, 350); OUT.pads[nm] = { fastPk: +F.pk.toFixed(4), pagePk: +P.pk.toFixed(4), dB: dB(F.pk, P.pk) };
    ok(F.played === 1 && F.pk > 0.01 && Math.abs(dB(F.pk, P.pk)) < 1.5, `Drum kit ${nm} (key ${n}): as loud as the page's own hit (${dB(F.pk, P.pk)} dB)`, OUT.pads[nm]);
  }
  ok((await both(62)) === 1, 'a fast drum hit is not played again by the page');
  { const n0 = await R('LTF.n'), s0 = await R('LTF.skip'); await inject([0x90, 50, 100]); await R('ctlMsg(__D,new Uint8Array([0x90,50,100]));1'); await sleep(200); await inject([0x80, 50, 0]); await R('ctlMsg(__D,new Uint8Array([0x80,50,0]));1');
    ok((await R('LTF.n')) === n0 && (await R('LTF.skip')) === s0, 'a key outside the 16 pads is left to the page'); await sleep(600); }
  /* the open hat is choked by a closed hat: its sound 150 ms on, with and without the closed hat (the closed hat itself is short) */
  { await R('__tap(__T&&NODES.get(__T.id).in)'); const rms = `(async(ms)=>{await new Promise(r=>setTimeout(r,ms));const b=new Float32Array(2048);__A.getFloatTimeDomainData(b);let s=0;for(const x of b)s+=x*x;return Math.sqrt(s/b.length)})`;
    await R("__T.inst.pads[10].dec=3;changed(true);ltFastEval();1"); await sleep(1500); await R('ltFastEval();1'); await sleep(1200);
    await inject([0x90, 70, 100]); const a1 = await R(rms + '(250)'); await inject([0x80, 70, 0]); await sleep(1800);
    await inject([0x90, 70, 100]); await sleep(40); await inject([0x90, 66, 100]); const a2 = await R(rms + '(210)'); await inject([0x80, 70, 0]); await inject([0x80, 66, 0]); await sleep(1200);
    ok(a1 > 0.003 && a2 < a1 / 4, 'the open hat is cut by a closed hat (as the page does it)', { open: a1, choked: a2 }); }
  /* note to first sample during a 200 ms long task, before (the page) and after (fast): the Drum kit and an Orbit */
  const conv = `((ct)=>{const o=__OT();return o.to+o.pt+(ct-o.ct)*1000})`;
  const one = async (fast, busy, note) => {
    await R(`UI.ltFast=${fast ? 'undefined' : 'false'};ltFastEval();1`); await sleep(fast ? 900 : 300); if (fast) { await R('ltFastEval();1'); await sleep(300); }
    await R('__VS.length=0;1'); const nr = await R('LTF.rep.length');
    if (busy) await page.evaluate(() => { setTimeout(() => { const e = performance.now() + 200; while (performance.now() < e); }, 0); }); await sleep(busy ? 60 : 5);
    const t0 = Date.now();
    if (fast) await inject([0x90, note, 100]); else page.evaluate((n) => AudioLab.run('ctlMsg(__D,new Uint8Array([0x90,' + n + ',100]))'), note);
    await sleep(400);
    let ct = null;
    if (fast) { const r = JSON.parse(await R('JSON.stringify(LTF.rep.slice(' + nr + '))')); if (r.length) ct = r[0][2]; } else ct = await R('__VS[0]||null');
    const ms = ct == null ? null : (await R(conv + '(' + ct + ')')) - t0;
    if (fast) await inject([0x80, note, 0]); await R(`ctlMsg(__D,new Uint8Array([0x80,${note},0]));1`); await sleep(300);
    return ms;
  };
  for (const [pr, notes] of [['drums', [60, 62, 66, 63]], ['orb', [60, 62, 64, 65]]]) {
    if (pr !== 'drums') await arm(pr);
    const res = { before: [], after: [] };
    for (let i = 0; i < 6; i++) for (const fast of [false, true]) res[fast ? 'after' : 'before'].push(await one(fast, true, notes[i % notes.length]));
    const M = { before: med(res.before), after: med(res.after) }; OUT.lat[pr] = { ...M, all: res };
    console.log(pr, 'note to first sample during a 200 ms long task (ms, median of 6):', JSON.stringify(M));
    ok(res.after.every((x) => x != null) && M.before - M.after > 100, `${pr}: during a 200 ms long task the fast note does not wait for the page (${M.before} to ${M.after} ms)`);
  }
  await R('UI.ltFast=undefined;1');
  /* the Settings row turns it off */
  await R("document.getElementById('ltFmChk').click();1"); await sleep(300);
  ok((await R('UI.ltFast===false&&LTF.tgt.size===0')), 'unticking "Fast MIDI notes" stops the fast path');
  await R("document.getElementById('ltFmChk').click();1"); await sleep(300);
  ok(await R('UI.ltFast===true'), 'ticking it again turns it back on');
  await R("for(const t of S.tracks)t.arm=false;S.tracks=S.tracks.filter(t=>!t._lt3b);changed(true);syncGraph();ltFastEval();1"); await sleep(500);
  ok(errs.length === 0, 'no page errors in the desktop app', errs);
  try { await app.evaluate(({ app }) => app.exit(0)); } catch (e) { /* gone */ }

  /* the browser: recording by the MIDI time stamp, the Settings row absent */
  const REC = `(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const r=document.getElementById('liteNote');if(r)r.remove();await openDemoFractals();await w(2000);ensureCtx();await ctx.resume();
   const g=CTL.profs.find(p=>p.id==='generic');const D={id:'lt-rec',name:'LT Rec Keys',man:'',inp:{name:'LT Rec Keys'},out:null,prof:g,base:'LT Rec Keys'};CTL.devs.set('lt-rec',D);
   const X=new EventTarget();let bytes=null;X.addEventListener('midimessage',()=>ctlMsg(D,bytes));
   for(const t of S.tracks)t.arm=false;const lead=S.tracks.find(t=>t.name==='Lead');lead.arm=true;changed(true);syncGraph();await w(400);
   S.loop=false;UI.recOff=0;UI.countIn=0;UI.metro=false;const n0=lead.clips.length;pos=(81-1)*4;recStart();await w(2500);const P=[];
   for(let i=0;i<8;i++){await w(220+Math.random()*120);const ev=new Event('midimessage'),pn=ev.timeStamp,o=ctx.getOutputTimestamp(),spk=o.contextTime+(pn-o.performanceTime)/1000,tgt=CPU.pdc||0;
    const h=beatOf(secOf(play.b0)+(spk-tgt-play.t0));const e=performance.now()+150;while(performance.now()<e);bytes=new Uint8Array([0x90,60+i%5,100]);X.dispatchEvent(ev);P.push(h);
    await w(90);bytes=new Uint8Array([0x80,60+i%5,0]);X.dispatchEvent(new Event('midimessage'))}
   await w(300);stop();await w(400);const c=lead.clips.slice(n0).find(c=>/take/.test(c.name));if(!c)return{err:'no take'};
   const got=c.notes.map(n=>c.start+n.s).sort((a,b)=>a-b),spb=60/S.bpm;const e=got.map((g,i)=>+((g-P[i])*spb*1000).toFixed(2));lead.clips.splice(n0);changed(true);return{e,n:got.length}})()`;
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  for (const [lbl, file] of [['after', path.join(DIR, 'app', 'index.html')]].concat(BEFORE ? [['before', path.resolve(BEFORE)]] : [])) {
    const pg = await b.newPage(); const we = []; pg.on('pageerror', (e) => we.push(String(e).slice(0, 200)));
    await pg.goto('file://' + file); await pg.waitForFunction(() => window.AudioLab && window.AudioLab.version, null, { timeout: 90000 }); await sleep(2500);
    const r = await pg.evaluate((c) => AudioLab.run(c), REC); const m = r.e ? med(r.e.map(Math.abs)) : null;
    OUT.rec[lbl] = { ...r, medAbs: m, worst: r.e ? Math.max(...r.e.map(Math.abs)) : null };
    console.log('recording, ' + lbl + ': notes land (ms from what was heard at the press; the page busy for 150 ms after each press):', JSON.stringify(OUT.rec[lbl]));
    if (lbl === 'after') {
      ok(r.n === 8 && m < 1 && OUT.rec.after.worst < 2, `recording: a MIDI note is placed by its time stamp while the page is busy (median ${m} ms, worst ${OUT.rec.after.worst} ms)`, r);
      ok(await pg.evaluate(() => AudioLab.run("!document.getElementById('ltFmChk')&&!STX.has('fastMidi')&&!LT_HOOKS.fastNotes().on")), 'in the browser there is no "Fast MIDI notes" row and the fast path is off');
      ok(we.length === 0, 'no page errors in the browser', we);
    }
    await pg.close();
  }
  await b.close();
  if (JS) fs.writeFileSync(JS, JSON.stringify({ OUT, fail }, null, 1));
  console.log(fail.length ? 'FAILED ' + fail.length : 'all passed'); process.exit(fail.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
