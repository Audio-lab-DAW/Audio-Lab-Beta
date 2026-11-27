/* Task MG1: unit checks of desktop/native-migrate.js without Electron: which native builds a computer accepts, file names in the export.
     node tools/migrate-tests/unit_native_migrate.js */
const NM = require('../../desktop/native-migrate.js')._test;
const fail = []; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const plat = process.platform, arch = process.arch, key = (plat === 'linux' ? 'linux-' : plat === 'darwin' ? 'darwin-' : 'win32-') + arch;
if (plat === 'linux') process.env.AL_NATIVE_TEST = '1';
const kind = plat === 'win32' ? 'exe' : 'zip', ext = plat === 'win32' ? 'exe' : 'zip';
const e = (o) => ({ version: '1.0.0', platforms: { [key]: Object.assign({ url: 'https://example.com/AudioLab.' + ext, size: 10, sha256: 'a'.repeat(64), kind }, o) } });
ok(NM.pick(e({})) && NM.pick(e({})).version === '1.0.0', 'a good block for this computer is offered');
ok(!NM.pick(null) && !NM.pick({}) && !NM.pick({ version: '1.0.0' }), 'no block, or no platforms: nothing offered (what every manifest has until a native build is promoted)');
ok(!NM.pick({ version: '1.0.0', platforms: { 'sunos-sparc': e({}).platforms[key] } }), 'another platform only: nothing offered');
ok(!NM.pick(e({ minOS: '99.0' })), 'a minimum OS above this one: nothing offered');
ok(!NM.pick(e({ sha256: 'xyz' })) && !NM.pick(e({ size: 0 })), 'a bad checksum or size: nothing offered');
const save = process.env.AL_UPDATE_BASE, t = process.env.AL_NATIVE_TEST; delete process.env.AL_UPDATE_BASE; delete process.env.AL_NATIVE_TEST;
ok(!NM.pick(e({ url: 'http://127.0.0.1:8080/AudioLab.' + ext })), 'plain http is refused outside tests');
process.env.AL_UPDATE_BASE = 'http://127.0.0.1:1/'; if (plat === 'linux') process.env.AL_NATIVE_TEST = '1'; ok(!!NM.pick(e({ url: 'http://127.0.0.1:8080/AudioLab.' + ext })), 'http on 127.0.0.1 only in tests (AL_UPDATE_BASE)');
ok(!NM.pick(e({ url: 'http://example.com/AudioLab.' + ext })), 'http to another host is refused even in tests');
if (save) process.env.AL_UPDATE_BASE = save; else delete process.env.AL_UPDATE_BASE; if (t) process.env.AL_NATIVE_TEST = t;
ok(NM.cmpV('10.0.22631', '10.0.19041') > 0 && NM.cmpV('14.5.0', '13.0') > 0 && NM.cmpV('1.0.0', '1.0') === 0, 'version comparison (Windows build numbers, macOS versions)');
let bad = 0; for (const r of ['../x', '/abs', 'a/../b', 'a//b', 'c:x', 'a\u0000b', '']) { try { NM.safeRel(r); } catch (x) { bad++; } }
ok(bad === 7 && NM.safeRel('projects/open-001-Song.audiolab') === 'projects/open-001-Song.audiolab', 'export file names cannot leave the migrate folder');
console.log(fail.length ? fail.length + ' FAILED' : 'all checks passed'); process.exit(fail.length ? 1 : 0);
