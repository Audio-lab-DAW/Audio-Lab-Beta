// Runs the app's worklet bundle (WLSRC in index.html) in Node, outside the browser, for the native engine core's
// tests (task NB-N3c): the same processors fed in 128-frame blocks, so a difference between the native port and
// the browser can be traced statement by statement. Not part of the app.
//   node tools/native-lab/wl_node.js <cases.json> <in.wav> <outdir> [case-name-filter]
// Node's V8 is not the browser's: its Math.sin, cos, exp, pow and log10 may differ in the last bit.
'use strict';
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
function wlsrc() {
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  const line = html.split('\n').find(l => l.startsWith('const WLSRC='));
  return JSON.parse(line.slice('const WLSRC='.length).replace(/;\s*$/, ''));
}
function readWav(f) {
  const b = fs.readFileSync(f); let p = 12;
  while (p + 8 <= b.length) {
    const id = b.toString('ascii', p, p + 4), n = b.readUInt32LE(p + 4);
    if (id === 'data') { const N = n / 8, L = new Float32Array(N), R = new Float32Array(N); for (let i = 0; i < N; i++) { L[i] = b.readFloatLE(p + 8 + 8 * i); R[i] = b.readFloatLE(p + 12 + 8 * i) } return [L, R] }
    p += 8 + n + (n & 1);
  }
}
function writeWav(f, L, R, sr) {
  const N = L.length, b = Buffer.alloc(44 + N * 8); b.write('RIFF', 0); b.writeUInt32LE(36 + N * 8, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(3, 20); b.writeUInt16LE(2, 22); b.writeUInt32LE(sr, 24); b.writeUInt32LE(sr * 8, 28); b.writeUInt16LE(8, 32); b.writeUInt16LE(32, 34); b.write('data', 36); b.writeUInt32LE(N * 8, 40);
  for (let i = 0; i < N; i++) { b.writeFloatLE(L[i], 44 + 8 * i); b.writeFloatLE(R[i], 48 + 8 * i) }
  fs.writeFileSync(f, b);
}
const TYPE2PROC = { limit: 'al-limit', gate: 'al-gate', trans: 'al-trans', deess: 'al-deess', crush: 'al-crush', chorus: 'al-chorus', imager: 'al-imager', fshift: 'al-fshift', vocoder: 'al-voc', tstop: 'al-tstop', pshift: 'al-pshift', reson: 'al-reson' };
function makeScope(sr) {
  // one AudioWorkletGlobalScope: the bundle's seeded Math.random (as wlLoad installs it), sampleRate, currentTime
  const reg = {}, scope = { currentTime: 0 };
  const rnd = '(()=>{let a=0x9e3779b9,b=0x243f6a88,c=0xb7e15162,d=0x7f4a7c15;Math.random=()=>{a>>>=0;b>>>=0;c>>>=0;d>>>=0;let t=(a+b)|0;a=b^(b>>>9);b=(c+(c<<3))|0;c=(c<<21)|(c>>>11);d=(d+1)|0;t=(t+d)|0;c=(c+t)|0;return(t>>>0)/4294967296}})();\n';
  class AudioWorkletProcessor { constructor() { this.port = { postMessage() {}, onmessage: null } } }
  const fn = new Function('sampleRate', 'registerProcessor', 'AudioWorkletProcessor', '__scope', 'with(__scope){' + rnd + wlsrc() + '\n}');
  fn(sr, (n, C) => { reg[n] = C }, AudioWorkletProcessor, scope);
  return { reg, scope };
}
function main() {
  const [casesF, inF, outD, filt] = process.argv.slice(2);
  const cases = JSON.parse(fs.readFileSync(casesF, 'utf8')).cases, [IL, IR] = readWav(inF), sr = 48000, N = IL.length, Q = 128;
  fs.mkdirSync(outD, { recursive: true });
  const savedRandom = Math.random;
  for (const c of cases) {
    if (filt && !c.name.includes(filt)) continue;
    const { reg, scope } = makeScope(sr);
    const procs = c.chain.map(d => { const C = reg[TYPE2PROC[d.type]]; if (!C) throw new Error('no processor for ' + d.type); return new C({ processorOptions: { p: d.p } }) });
    const OL = new Float32Array(N), OR = new Float32Array(N);
    let a = [new Float32Array(Q), new Float32Array(Q)], o = [new Float32Array(Q), new Float32Array(Q)];
    for (let pos = 0; pos < N; pos += Q) {
      scope.currentTime = pos / sr;
      for (let i = 0; i < Q; i++) { a[0][i] = pos + i < N ? IL[pos + i] : 0; a[1][i] = pos + i < N ? IR[pos + i] : 0 }
      for (const pr of procs) { o[0].fill(0); o[1].fill(0); pr.process([a], [o]); const t = a; a = o; o = t }
      for (let i = 0; i < Q && pos + i < N; i++) { OL[pos + i] = a[0][i]; OR[pos + i] = a[1][i] }
    }
    writeWav(path.join(outD, c.name + '.wav'), OL, OR, sr);
  }
  Math.random = savedRandom;
}
main();
