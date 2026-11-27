/* Loaded before desktop/main.js by taskAH_electron.js (electron -r): records every icon the app sets.
   With AH_PLATFORM=darwin it also says the computer is a Mac and gives the app a Dock that only records.
   With AH_DARWIN_REL=25 as well it is macOS 26 with the Icon Composer icon in the bundle (task IC1): the kernel version reads 25.x and
   Resources/Assets.car counts as present. A Dock picture of null (back to the bundle icon) is recorded as { reset: true }. */
const { app, BrowserWindow, nativeImage } = require('electron');
const crypto = require('crypto');
const sig = (im) => { try { const s = im.getSize(); return { w: s.width, h: s.height, sha: crypto.createHash('sha256').update(im.toBitmap()).digest('hex') }; } catch (e) { return { err: String(e) }; } };
global.__AH = { dock: [], win: [], sig, nativeImage };
if (process.env.AH_PLATFORM) {
  Object.defineProperty(process, 'platform', { value: process.env.AH_PLATFORM });
  if (process.env.AH_PLATFORM === 'darwin') {
    const dock = { setIcon: (im) => { global.__AH.dock.push(im === null ? { reset: true } : sig(im)); }, setMenu() {}, setBadge() {}, getBadge: () => '', bounce: () => 0, cancelBounce() {}, hide() {}, show: () => Promise.resolve(), isVisible: () => true, downloadFinished() {} };
    Object.defineProperty(app, 'dock', { value: dock, configurable: true });
    if (process.env.AH_DARWIN_REL) {
      const os = require('os'), fs = require('fs'), ex = fs.existsSync;
      os.release = () => process.env.AH_DARWIN_REL + '.1.0';
      fs.existsSync = (f) => (/[\\/]Assets\.car$/.test(String(f)) ? true : ex(f));
    }
  }
}
const real = BrowserWindow.prototype.setIcon;
BrowserWindow.prototype.setIcon = function (im) { global.__AH.win.push(sig(im)); try { return real.call(this, im); } catch (e) { /* the record is what counts */ } };
