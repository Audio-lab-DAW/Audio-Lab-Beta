"""Task WS-F (lane Q): the song data out of index.html (the user's decision, 28 Nov 2026 14:55 Brussels: the Fractals song is only
for testing; D6: the app ships no song).
Takes out DEMO_FRACTALS (the project file), DEMO_VOX (where the vocal samples go) and DEMO_VOX_FLAC (the ten vocal samples cut from
Electric Universe's recording); they are now tools/test-songs/Fractals_remake.audiolab, fractals.json and vox/*.flac.
frxProject / openDemoFractals / frxBoot keep their names (the release gate and the tests call them) and read the files from
window.AL_TEST_SONGS (the Electron tests) or from tools/test-songs/ next to the page (the browser tests, tools/test-songs/alsong.py).
Every anchor is asserted unique. Run on a fresh index.html:  python3 tools/design-lab/ws/wsf_edit.py [index.html]"""
import sys, re
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
n0 = len(s)

def one(pat, rep, flags=re.S):
    global s
    m = list(re.finditer(pat, s, flags))
    assert len(m) == 1, (pat[:80], len(m))
    s = s[:m[0].start()] + (rep(m[0]) if callable(rep) else rep) + s[m[0].end():]

def lit(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)

# 1) the project file and the vocal positions
one(r"/\* demo: Fractals remake \(embedded\) \*/\nconst DEMO_FRACTALS='[A-Za-z0-9+/=]+';\nconst DEMO_VOX=\[[\[\]0-9,]+\];\n/\* the Fractals song is opened by frxBoot at every start and by openDemoFractals from the menu \(task AI, v0\.220\): see before askChoice \*/",
    "/* task WS-F (lane Q): the Fractals song is a test song and is not part of the app any more; it lives in tools/test-songs/ (see frxProject) */")

# 2) the vocal samples and the functions that read them
one(r"const DEMO_VOX_FLAC=\[[^\n]*\];\nasync function frxVoxBuf\(k\)\{.*?\nasync function frxProject\(\)\{[^\n]*\}\n",
    lambda m: '''/* task WS-F (lane Q): the app ships no song (D6; the user, 28 Nov: "The fractal song is only for testing"). The song is in
   tools/test-songs/: fractals.json names the project file (Fractals_remake.audiolab) and where each vocal sample goes (vox/*.flac, the
   same samples as before, decoded the same way, so the song sounds bit for bit as it did). The functions keep their names for the
   release gate and the tests, which give the files as window.AL_TEST_SONGS (path -> base64 or bytes; the Electron tests) or serve
   them next to the page (tools/test-songs/alsong.py; the browser tests). Without the files the song is simply not there. */
const WSF_DIR='tools/test-songs/';
async function wsfGet(p){const T=window.AL_TEST_SONGS;if(T&&T[p]!=null){const v=T[p];return typeof v==='string'?Uint8Array.from(atob(v),c=>c.charCodeAt(0)):new Uint8Array(v)}
  const r=await fetch(WSF_DIR+p);if(!r.ok)throw new Error('the test song file '+p+' is not here');return new Uint8Array(await r.arrayBuffer())}
async function wsfSong(){return JSON.parse(new TextDecoder().decode(await wsfGet('fractals.json')))}
async function frxVoxBuf(k,p){const id='frxvox'+String(k).padStart(2,'0');if(BUFS.has(id))return id;ensureCtx();
  const u=await wsfGet(p),buf=await ctx.decodeAudioData(u.buffer.slice(u.byteOffset,u.byteOffset+u.byteLength));
  if(!BUFS.has(id)){BUFS.set(id,{buf,peaks:peaks(buf)});try{const db=await idbOpen();if(!(await idbReq(db.transaction('audio').objectStore('audio').count(id))))bufStore(id,buf)}catch(e){}}
  return id}
async function frxVox(P,M){if(P.tracks.some(t=>t.name==='Vocals (original)'))return;const V=(M&&M.vox)||[];const ids=await Promise.all(V.map(([b,p],i)=>frxVoxBuf(i+1,p)));
  const t=mkTrack('audio',null,'Vocals (original)','#ffd166');t.vol=.8;t.icon='i:mic-vocal';const rv=P.tracks.find(x=>x.kind==='return'&&/[Rr]everb/.test(x.name));if(rv)t.sends={[rv.id]:.15};
  V.forEach(([b],i)=>{const buf=BUFS.get(ids[i]).buf;t.clips.push(mkClip({start:b,len:buf.duration*P.bpm/60,name:'Vocal '+(b/4+1),buf:ids[i],dur:buf.duration,gain:0,fi:0,fo:.25}))});P.tracks.push(t)}
async function frxProject(){const M=await wsfSong(),J=await unpackProject(new File([await wsfGet(M.file)],FRX_FILE));try{await frxVox(J.project,M)}catch(e){console.error('AudioLab Fractals vocals',e)}return J}
''')

# 3) the menu function (no menu shows it since WS-1; the tests call it): a plain message without the files
lit("const J=await frxProject(),id='p'+rid();PJ.list.push({openedAt:Date.now(),id,name:FRX_NAME,S:J.project,view:J.view,file:FRX_FILE,dirty:false});saveProjects();withSplash(",
    "let J=null;try{J=await frxProject()}catch(e){toast('The Fractals song is a test song and is not part of the app.');return}const id='p'+rid();PJ.list.push({openedAt:Date.now(),id,name:FRX_NAME,S:J.project,view:J.view,file:FRX_FILE,dirty:false});saveProjects();withSplash(")

# 4) the start under automation: without the files, an empty project, no error and no toast
lit("try{J=await frxProject()}catch(e){console.error('AudioLab Fractals song',e)}",
    "try{J=await frxProject()}catch(e){console.warn('AudioLab: the Fractals test song is not here (tools/test-songs), an empty project instead')}")
lit("else{if(hold){hold.name='Untitled';delete hold.frxHold}toast('Could not open the Fractals song.')}",
    "else{if(hold){hold.name='Untitled';delete hold.frxHold}}")

# 5) the comments that said the song ships inside the app
lit("/* ===================== task AI (v0.220): the Fractals song ships inside the app and is the only open song at every start =====================\n   The project is DEMO_FRACTALS (master -10 dB from v0.220). Its vocal samples are inside this file too (FLAC, the same samples as vox/*.wav,\n   which stay as a fallback), so the audio track is there in the desktop app and offline.",
    "/* ===================== task AI (v0.220): the Fractals song opens at every start under automation (the tests; since WS-1 the app opens the start screen) =====================\n   The project is tools/test-songs/Fractals_remake.audiolab (master -10 dB from v0.220) with its vocal samples (task WS-F: out of this file).")
lit("A pulled-out project window (CHILD) starts as before. Under automation (navigator.webdriver, the UI tests and the release\n     gate's engine tests) the start is the one before this step (task AI's Fractals song)",
    "A pulled-out project window (CHILD) starts as before. Under automation (navigator.webdriver, the UI tests and the release\n     gate's engine tests) the start is the one before this step (task AI's Fractals song, read from tools/test-songs since WS-F)")

assert 'DEMO_FRACTALS' not in s and 'DEMO_VOX' not in s and 'vox/fractals_vox_' not in s
open(P, 'w', encoding='utf-8').write(s)
print('wsf_edit: %s %d -> %d bytes (%.2f MB smaller)' % (P, n0, len(s), (n0 - len(s)) / 1e6))
