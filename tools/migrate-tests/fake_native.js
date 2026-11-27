/* Task MG1: a stand-in native AudioLab for this computer and a local update server that offers it (AL_UPDATE_BASE).
     node tools/migrate-tests/fake_native.js <work dir> [port] [--bad-sha] [--dmg] [--sign] [--bad-sig]
   Makes, in <work dir>/srv:
     Mac:     AudioLab.zip (or AudioLab.dmg with --dmg): AudioLab.app, ad hoc signed, its executable a shell script that writes
              stand-in-started.json (its arguments) into the folder passed after --migrated-from-electron and stays alive 25 s.
              The bundle carries a quarantine mark, as a download would, so the test can check the installer removed it.
     Windows: AudioLab-Setup.exe, compiled from C# with PowerShell's Add-Type: writes the same file and exits (an installer stand-in).
     Linux:   AudioLab.zip with AudioLab/AudioLab (a shell script), installed only with AL_NATIVE_TEST=1 (tests).
   and desktop/app-version.json: version 0.250 (the program stays as it is), plus the "native" block for this platform.
   Serves <work dir>/srv on 127.0.0.1:<port> and prints READY <port>. The --sign options write an Ed25519 key pair; the public key is printed
   (PUBKEY <base64>) for AL_NATIVE_PUBKEY. */
const fs = require('fs'), path = require('path'), http = require('http'), crypto = require('crypto'), { execFileSync } = require('child_process');
const W = path.resolve(process.argv[2] || 'mg-work'); const PORT = +(process.argv[3] || 0) || 0; const has = (f) => process.argv.includes(f);
const SRV = path.join(W, 'srv'), BUILD = path.join(W, 'build');
fs.rmSync(W, { recursive: true, force: true }); fs.mkdirSync(path.join(SRV, 'desktop'), { recursive: true }); fs.mkdirSync(BUILD, { recursive: true });
const plat = process.platform, arch = process.arch;
let file, kind, key;
const SCRIPT = `#!/bin/sh
# stand-in for the native AudioLab (task MG1 test)
d=""; prev=""
for a in "$@"; do if [ "$prev" = "--migrated-from-electron" ]; then d="$a"; fi; prev="$a"; done
[ -n "$d" ] && mkdir -p "$d" && printf '{"standIn":true,"pid":%s,"args":"%s"}' "$$" "$*" > "$d/stand-in-started.json"
sleep 25
`;
if (plat === 'darwin') {
  const app = path.join(BUILD, 'AudioLab.app'), c = path.join(app, 'Contents');
  fs.mkdirSync(path.join(c, 'MacOS'), { recursive: true });
  fs.writeFileSync(path.join(c, 'Info.plist'), `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>CFBundleExecutable</key><string>AudioLab</string><key>CFBundleIdentifier</key><string>com.audiolab.native.standin</string>
<key>CFBundleName</key><string>AudioLab</string><key>CFBundlePackageType</key><string>APPL</string><key>CFBundleShortVersionString</key><string>1.0.0</string>
<key>CFBundleVersion</key><string>1</string><key>LSMinimumSystemVersion</key><string>11.0</string></dict></plist>
`);
  fs.writeFileSync(path.join(c, 'MacOS', 'AudioLab'), SCRIPT, { mode: 0o755 });
  try { execFileSync('/usr/bin/codesign', ['--force', '--deep', '-s', '-', app]); } catch (e) { console.log('codesign failed (continuing):', String(e.message).slice(0, 120)); }
  try { execFileSync('/usr/bin/xattr', ['-w', 'com.apple.quarantine', '0081;65000000;Safari;', app]); } catch (e) { /* ignore */ }
  if (has('--dmg')) { file = path.join(SRV, 'AudioLab.dmg'); kind = 'dmg'; execFileSync('/usr/bin/hdiutil', ['create', '-quiet', '-volname', 'AudioLab', '-srcfolder', app, '-ov', '-format', 'UDZO', file]); }
  else { file = path.join(SRV, 'AudioLab.zip'); kind = 'zip'; execFileSync('/usr/bin/ditto', ['-c', '-k', '--sequesterRsrc', '--keepParent', app, file]); }
  key = 'darwin-' + arch;
} else if (plat === 'win32') {
  const cs = path.join(BUILD, 'standin.cs'); file = path.join(SRV, 'AudioLab-Setup.exe'); kind = 'exe'; key = 'win32-' + arch;
  fs.writeFileSync(cs, `using System; using System.IO;
public static class P { public static int Main(string[] a) { string d = null; for (int i = 0; i + 1 < a.Length; i++) if (a[i] == "--migrated-from-electron") d = a[i + 1];
  if (d != null) { Directory.CreateDirectory(d); File.WriteAllText(Path.Combine(d, "stand-in-started.json"), "{\\"standIn\\":true,\\"args\\":\\"" + string.Join(" ", a).Replace("\\\\", "/").Replace("\\"", "'") + "\\"}"); }
  System.Threading.Thread.Sleep(3000); return 0; } }
`);
  execFileSync('powershell', ['-NoProfile', '-Command', `Add-Type -TypeDefinition (Get-Content -Raw '${cs}') -Language CSharp -OutputAssembly '${file}' -OutputType ConsoleApplication`], { stdio: 'inherit' });
} else {
  const d = path.join(BUILD, 'AudioLab'); fs.mkdirSync(d, { recursive: true }); fs.writeFileSync(path.join(d, 'AudioLab'), SCRIPT, { mode: 0o755 });
  file = path.join(SRV, 'AudioLab.zip'); kind = 'zip'; key = 'linux-' + arch;
  execFileSync('zip', ['-q', '-r', file, 'AudioLab'], { cwd: BUILD });
}
const data = fs.readFileSync(file);
let sha = crypto.createHash('sha256').update(data).digest('hex');
if (has('--bad-sha')) sha = sha.replace(/^./, (c) => (c === '0' ? '1' : '0'));
let signature = '';
if (has('--sign') || has('--bad-sig')) {
  const kp = crypto.generateKeyPairSync('ed25519');
  const raw = kp.publicKey.export({ format: 'der', type: 'spki' }).subarray(12);
  signature = crypto.sign(null, has('--bad-sig') ? Buffer.concat([data, Buffer.from('x')]) : data, kp.privateKey).toString('base64');
  console.log('PUBKEY ' + raw.toString('base64'));
}
const base = (p) => `http://127.0.0.1:${p}/`;
function manifest(p) {
  return { version: '0.250', sha256: '0'.repeat(64), size: 1, minShell: '0.147.0', notes: 'test manifest (task MG1)',
    native: { version: '1.0.0', released: '2026-11-27', notes: 'Stand-in native build for the MG1 test.',
      platforms: { [key]: { url: base(p) + path.basename(file), size: data.length, sha256: sha, signature, minOS: plat === 'darwin' ? '11.0' : plat === 'win32' ? '10.0.0' : '', kind, app: plat === 'darwin' ? 'AudioLab.app' : 'AudioLab', exec: plat === 'linux' ? 'AudioLab/AudioLab' : '' } } } };
}
const srv = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (u === '/desktop/app-version.json') { res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(manifest(srv.address().port), null, 1)); return; }
  const f = path.join(SRV, path.normalize(u).replace(/^([/\\])+/, ''));
  if (!f.startsWith(SRV) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end('not found'); return; }
  // sent in slices, so the window's progress bar has something to show
  const b = fs.readFileSync(f); res.writeHead(200, { 'Content-Type': 'application/octet-stream', 'Content-Length': b.length });
  let o = 0; const step = () => { if (o >= b.length) { res.end(); return; } const n = Math.max(1, Math.ceil(b.length / 25)); res.write(b.subarray(o, o + n)); o += n; setTimeout(step, 40); }; step();
});
srv.listen(PORT, '127.0.0.1', () => { fs.writeFileSync(path.join(W, 'manifest.json'), JSON.stringify(manifest(srv.address().port), null, 1)); console.log('READY ' + srv.address().port + ' ' + kind + ' ' + data.length + ' bytes, platform key ' + key); });
