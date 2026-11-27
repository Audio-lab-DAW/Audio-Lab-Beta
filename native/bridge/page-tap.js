// The page's side of the native engine (task NB-N2b). Written as one function that does not depend on the rest
// of the app, so that stage N2c can copy it into index.html unchanged, and the test in
// tools/native-lab/electron-bridge/ runs exactly this code.
//
//   const tap = await alNativeTap(ctx, masterNode);   // masterNode: what would otherwise go to ctx.destination
//   tap.info  -> { path: 'worklet thread straight to the shell' | 'through the page thread (...)' }
//   tap.detach()
//
// An AudioWorklet copies every 128-frame block of the master (stereo, interleaved Float32Array) and posts it
// through its own end of a MessageChannel. The other end goes to the desktop shell (preload.js listens for
// { alNativePort: true }). The worklet's own output is silence: the page keeps playing into a real device only
// so that its audio clock runs (task NB-N2a: with no device at all Chromium ran the page at 0.59 of real time).
// When nothing is connected to its input it sends silent blocks, so the stream never stops while it is attached.
async function alNativeTap(ctx, src) {
  const code = 'class ALNativeTap extends AudioWorkletProcessor {' +
    'constructor() { super(); this.out = null; this.on = true;' +
    ' this.port.onmessage = e => { const d = e.data || {}; if (d.port) this.out = d.port; else if (d.fallback) this.out = this.port; if (d.on !== undefined) this.on = !!d.on; }; }' +
    'process(inputs) {' +
    ' if (!this.out || !this.on) return true;' +
    ' const i = inputs[0] || [], L = i[0], R = i[1] || i[0], n = L ? L.length : 128, f = new Float32Array(n * 2);' +
    ' if (L) for (let k = 0; k < n; k++) { f[2 * k] = L[k]; f[2 * k + 1] = R[k]; }' +
    ' this.out.postMessage(f); return true; } }' +
    'registerProcessor("al-native-tap", ALNativeTap);';
  const url = URL.createObjectURL(new Blob([code], { type: 'application/javascript' }));
  try { await ctx.audioWorklet.addModule(url); } finally { URL.revokeObjectURL(url); }
  const node = new AudioWorkletNode(ctx, 'al-native-tap', { numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [2], channelCount: 2, channelCountMode: 'explicit', channelInterpretation: 'speakers' });
  const ch = new MessageChannel();
  const info = {};
  try { node.port.postMessage({ port: ch.port1 }, [ch.port1]); info.path = 'worklet thread straight to the shell'; }
  catch (e) { info.path = 'through the page thread (' + e.message + ')'; node.port.onmessage = m => ch.port1.postMessage(m.data); node.port.postMessage({ fallback: true }); }
  window.postMessage({ alNativePort: true }, '*', [ch.port2]);
  if (src) src.connect(node);
  node.connect(ctx.destination);
  return {
    node, info,
    pause(on) { node.port.postMessage({ on: !on }); },
    detach() { try { if (src) src.disconnect(node); } catch (e) { /* not connected */ } try { node.disconnect(); } catch (e) { /* ignore */ } node.port.postMessage({ on: false }); try { ch.port2.close(); } catch (e) { /* moved */ } }
  };
}

// task NB-R2, the rate contract (review A1). The page's AudioContext must render at the rate the engine's device runs
// (the page's own clock device may run at anything, eqMac's Bose copy ran at 16 kHz: Chromium resamples on its side,
// which is harmless because that device only plays silence). The engine refuses any other rate, and when the device
// changes rate while sound plays it goes silent and sends { ev: 'rate', value, soundPaused: true }.
//   const ctx = alNativeContext(status.rate);                 // status from nativeEngine.cmd('status')
//   const stop = alNativeWatchRate(nativeEngine, async rate => { /* make the context again at rate, tap it, sound({ pageRate: rate }) */ });
function alNativeContext(rate, latencyHint) { return new AudioContext({ sampleRate: rate, latencyHint: latencyHint || 'interactive' }); }
function alNativeWatchRate(nativeEngine, onNewRate) {
  return nativeEngine.on(e => { if (e && e.ev === 'rate' && e.soundPaused) onNewRate(e.value, e); });
}
if (typeof module !== 'undefined') module.exports = { alNativeTap, alNativeContext, alNativeWatchRate };
