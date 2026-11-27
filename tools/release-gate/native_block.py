#!/usr/bin/env python3
"""Release gate, the native block (task MG1). The update manifest (desktop/app-version.json) may carry a "native" block: the native AudioLab
that Electron apps from MG1 on offer in their centred window (desktop/native-migrate.js, docs/native-migration.md). Only the gate writes it.

  python3 tools/release-gate/native_block.py check BLOCK.json [--download] [--pubkey BASE64]
      validates the block; --download fetches every platform's file and checks its size, sha256 and (with --pubkey, or AL_NATIVE_PUBKEY)
      its Ed25519 signature. Exit 0 when good.
  python3 tools/release-gate/native_block.py write BLOCK.json MANIFEST.json
      puts the (checked) block into MANIFEST.json and changes nothing else in it (a native release does not move the program version).
  python3 tools/release-gate/native_block.py remove MANIFEST.json
      takes the block out again (installed Electron apps stop offering it).

The block:
  { "version": "1.0.0", "released": "2026-12-..", "notes": "one line per change",
    "platforms": {
      "darwin-arm64": { "url": "https://.../AudioLab-1.0.0-mac-arm64.zip", "size": 123, "sha256": "64 hex", "signature": "base64 Ed25519 of the file, or empty",
                        "minOS": "13.0", "kind": "zip" | "dmg", "app": "AudioLab.app" },
      "win32-x64":    { "url": "https://.../AudioLab-1.0.0-Setup.exe", "size": 123, "sha256": "...", "signature": "", "minOS": "10.0.19041",
                        "kind": "exe", "args": [] } } }
Platform keys: darwin-arm64, darwin-x64, darwin (both), win32-x64, win32-arm64, win32. Shells before MG1 ignore the block."""
import sys, json, re, hashlib, base64, os, urllib.request

KEYS = {'darwin-arm64', 'darwin-x64', 'darwin', 'win32-x64', 'win32-arm64', 'win32'}
HEX = re.compile(r'^[0-9a-f]{64}$'); VER = re.compile(r'^\d+\.\d+\.\d+$')

def problems(b):
    p = []
    if not isinstance(b, dict): return ['the block is not an object']
    if not VER.match(str(b.get('version', ''))): p.append('version must be like 1.0.0')
    P = b.get('platforms')
    if not isinstance(P, dict) or not P: return p + ['platforms is missing or empty']
    for k, e in P.items():
        if k not in KEYS: p.append('%s: unknown platform key' % k); continue
        if not isinstance(e, dict): p.append('%s: not an object' % k); continue
        if not str(e.get('url', '')).startswith('https://'): p.append('%s: url must be https' % k)
        if not HEX.match(str(e.get('sha256', ''))): p.append('%s: sha256 must be 64 lower-case hex digits' % k)
        if not isinstance(e.get('size'), int) or e['size'] <= 0: p.append('%s: size must be a whole number of bytes' % k)
        kind = e.get('kind') or ('dmg' if e.get('url', '').endswith('.dmg') else 'zip' if e.get('url', '').endswith('.zip') else 'exe' if e.get('url', '').endswith('.exe') else '')
        if k.startswith('darwin') and kind not in ('zip', 'dmg'): p.append('%s: kind must be zip or dmg' % k)
        if k.startswith('win32') and kind != 'exe': p.append('%s: kind must be exe (a per-user installer)' % k)
        if e.get('signature') and len(base64.b64decode(e['signature'] + '==')) != 64: p.append('%s: signature must be 64 bytes in base64' % k)
        if k.startswith('darwin') and not str(e.get('app', 'AudioLab.app')).endswith('.app'): p.append('%s: app must name the .app bundle' % k)
        if k.startswith('darwin') and str(e.get('app', '')) == 'AudioLab Pro.app': p.append('%s: the native app must not be called AudioLab Pro.app (that is the Electron app, which stays)' % k)
    return p

def verify_sig(data, sig_b64, pub_b64):
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        raise SystemExit('the signature check needs: pip install cryptography')
    try: Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64)).verify(base64.b64decode(sig_b64), data); return True
    except Exception: return False

def download_check(b, pub):
    bad = []
    for k, e in b['platforms'].items():
        with urllib.request.urlopen(urllib.request.Request(e['url'], headers={'User-Agent': 'audiolab-release-gate'}), timeout=600) as r: data = r.read()
        sha = hashlib.sha256(data).hexdigest()
        if len(data) != e['size']: bad.append('%s: %d bytes, the block says %d' % (k, len(data), e['size']))
        if sha != e['sha256']: bad.append('%s: sha256 %s, the block says %s' % (k, sha[:12], e['sha256'][:12]))
        if pub:
            if not e.get('signature'): bad.append('%s: no signature (the shell has a key, so it would refuse)' % k)
            elif not verify_sig(data, e['signature'], pub): bad.append('%s: the signature does not match' % k)
        print('     %s: %d bytes, sha256 %s%s' % (k, len(data), 'ok' if sha == e['sha256'] else 'WRONG', (', signature ' + ('ok' if e.get('signature') and verify_sig(data, e['signature'], pub) else 'WRONG')) if pub else ''))
    return bad

def main(a):
    if len(a) >= 2 and a[0] == 'check':
        b = json.load(open(a[1])); p = problems(b)
        if not p and '--download' in a:
            pub = a[a.index('--pubkey') + 1] if '--pubkey' in a else os.environ.get('AL_NATIVE_PUBKEY', '')
            p = download_check(b, pub)
        print('native block: ' + ('good (%s, %s)' % (b.get('version'), ', '.join(sorted(b['platforms']))) if not p else 'BAD: ' + '; '.join(p)))
        return 0 if not p else 1
    if len(a) == 3 and a[0] == 'write':
        b = json.load(open(a[1])); p = problems(b)
        if p: print('native block: BAD: ' + '; '.join(p)); return 1
        m = json.load(open(a[2])); m['native'] = b
        open(a[2], 'w').write(json.dumps(m, indent=2, ensure_ascii=False) + '\n'); print('native block %s written into %s' % (b['version'], a[2])); return 0
    if len(a) == 2 and a[0] == 'remove':
        m = json.load(open(a[1])); m.pop('native', None); open(a[1], 'w').write(json.dumps(m, indent=2, ensure_ascii=False) + '\n'); print('native block removed from ' + a[1]); return 0
    print(__doc__); return 2

if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
