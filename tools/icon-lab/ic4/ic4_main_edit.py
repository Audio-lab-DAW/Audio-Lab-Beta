#!/usr/bin/env python3
"""Task IC4: the app icon block of desktop/main.js. Unique, asserted anchors; safe to re-run on a fresh file (it skips when applied)."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'desktop/main.js'
s = open(p, encoding='utf8').read()
if 'IC4_ICON' in s: print('already applied'); sys.exit(0)
def rep(old, new, count=1):
    global s
    n = s.count(old); assert n == count, (n, old[:80]); s = s.replace(old, new)
rep("""/* ---------- app icon: Ocean Yellow by default, any picker icon by choice (v0.203) ----------""",
"""/* ---------- app icon: J3 Dipole Field by default (task IC4; Ocean Yellow before), any picker icon by choice (v0.203) ----------""")
rep("""  try { iconList = JSON.parse(fs.readFileSync(path.join(ICON_DIR, 'icons.json'), 'utf8')); } catch (e) { iconList = { default: 'ocean-yellow', groups: [] }; }
  return iconList;
}""", """  try { iconList = JSON.parse(fs.readFileSync(path.join(ICON_DIR, 'icons.json'), 'utf8')); } catch (e) { iconList = { default: IC4_ICON.def, groups: [] }; }
  return iconList;
}
// IC4_ICON (task IC4, 27 Nov 2026): the default became J3 "Dipole Field". A choice saved before IC4 carries no version; if it is the
// old default (Ocean Yellow) it meant "the default", so it now gives J3. Choices saved from IC4 on carry v: 2 and are kept as they are.
const IC4_ICON = { def: 'dipole-field' };
function icDef() { return readIcons().default || IC4_ICON.def; }""")
rep("""function savedIcon() { try { const id = JSON.parse(fs.readFileSync(iconPrefFile(), 'utf8')).id; if (findIcon(id)) return id; } catch (e) { /* none saved */ } return readIcons().default || 'ocean-yellow'; }""",
"""function savedIcon() {
  try { const j = JSON.parse(fs.readFileSync(iconPrefFile(), 'utf8')), id = j.id; if (!j.v && id === readIcons().previous_default) return icDef(); if (findIcon(id)) return id; } catch (e) { /* none saved */ }
  return icDef();
}""")
rep("""  const def = id === (readIcons().default || 'ocean-yellow');
  if (def && isMac) {""", """  const def = id === icDef();
  if (def && isMac) {""")
rep("""function winIcon() { return !isMac && curIcon && curIcon !== (readIcons().default || 'ocean-yellow') ? iconImage(curIcon, true) : null; }""",
"""function winIcon() { if (isMac || !curIcon || curIcon === icDef()) return null; return icoImage(curIcon) || iconImage(curIcon, true); }
// Windows: a picker choice as a multi-size .ico (its own small pictures at 16, 32 and 48 px, task IC4), so the title bar and the
// taskbar show the small versions drawn for those sizes instead of the 512 px picture shrunk. Written once per icon in user data.
function icoFor(id) {
  try {
    const im = iconImage(id, true); if (!im) return null;
    const f = path.join(app.getPath('userData'), 'app-icon-' + id + '.ico');
    if (!fs.existsSync(f)) fs.writeFileSync(f, makeIco(im, findIcon(id)));
    return f;
  } catch (e) { return null; }
}
function icoImage(id) {
  if (process.platform !== 'win32') return null;
  try { const f = icoFor(id); if (!f) return null; const im = nativeImage.createFromPath(f); return im.isEmpty() ? null : im; } catch (e) { return null; }
}""")
rep("""      if (id === (readIcons().default || 'ocean-yellow') && macBundleIcon()) {""", """      if (id === icDef() && macBundleIcon()) {""")
rep("""    if (startup && id === (readIcons().default || 'ocean-yellow')) return;
    const im = (id === (readIcons().default || 'ocean-yellow') && defaultIcon()) || iconImage(id, true);""",
"""    if (startup && id === icDef()) return;
    const im = (id === icDef() && defaultIcon()) || icoImage(id) || iconImage(id, true);""")
rep("""// A PNG-in-ICO file (Windows Vista and later read these): 256, 48, 32 and 16 px.
function makeIco(im) {
  const pngs = [256, 48, 32, 16].map((n) => ({ n, b: im.resize({ width: n, height: n, quality: 'best' }).toPNG() }));""",
"""// A PNG-in-ICO file (Windows Vista and later read these): 256, 48, 32 and 16 px. The icon's own small pictures (icons.json 'small',
// task IC4) are used at 16, 32 and 48 px when it has them; otherwise the big picture is shrunk.
function smallPng(ic, n) {
  try { const f = ic && ic.small && ic.small[String(n)]; if (!f) return null; const im = nativeImage.createFromPath(path.join(ICON_DIR, f)); const s = im.getSize(); return !im.isEmpty() && s.width === n ? im.toPNG() : null; } catch (e) { return null; }
}
function makeIco(im, ic) {
  const pngs = [256, 48, 32, 16].map((n) => ({ n, b: smallPng(ic, n) || im.resize({ width: n, height: n, quality: 'best' }).toPNG() }));""")
rep("""    const def = id === (readIcons().default || 'ocean-yellow');
    const ud = app.getPath('userData');
    let ico = process.execPath;
    if (!def) {
      const im = iconImage(id, true); if (!im) return;
      ico = path.join(ud, 'app-icon-' + id + '.ico');   // a new name per icon, so Windows does not show a cached picture
      if (!fs.existsSync(ico)) fs.writeFileSync(ico, makeIco(im));
    }""", """    const def = id === icDef();
    const ud = app.getPath('userData');
    let ico = process.execPath;
    if (!def) {
      ico = icoFor(id); if (!ico) return;   // a new name per icon, so Windows does not show a cached picture
    }""")
rep("""  return { default: L.default || 'ocean-yellow', current: curIcon || savedIcon(),""", """  return { default: icDef(), current: curIcon || savedIcon(),""")
rep("""  try { fs.writeFileSync(iconPrefFile(), JSON.stringify({ id })); } catch (x) { /* still applied for this run */ }""",
"""  try { fs.writeFileSync(iconPrefFile(), JSON.stringify({ id, v: 2 })); } catch (x) { /* still applied for this run */ }""")
rep("""    if (curIcon !== (readIcons().default || 'ocean-yellow')) setTimeout(() => updateShortcuts(curIcon), 4000);""", """    if (curIcon !== icDef()) setTimeout(() => updateShortcuts(curIcon), 4000);""")
rep("    // The chosen icon (Ocean Yellow unless another was picked) in the Dock,", "    // The chosen icon (J3 Dipole Field unless another was picked, task IC4) in the Dock,")
assert "'ocean-yellow'" not in s, 'an ocean-yellow default left'
assert "'ocean-yellow'" not in s.split('/* ---------- app icon')[1].split("ipcMain.handle('al:set-app-icon'")[0], 'an ocean-yellow default left'
open(p, 'w', encoding='utf8').write(s); print('main.js: IC4 icon block applied')
