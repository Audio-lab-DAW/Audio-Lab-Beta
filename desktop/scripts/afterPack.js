// Ad-hoc sign the Mac app so macOS shows the normal "Open Anyway" prompt
// instead of "is damaged and can't be opened" (no Apple Developer account needed).
const { execFileSync } = require('child_process');
const path = require('path');
exports.default = async function (context) {
  if (context.electronPlatformName !== 'darwin') return;
  const app = path.join(context.appOutDir, context.packager.appInfo.productFilename + '.app');
  // The macOS 26 icon (task IC1): Assets.car (compiled from icon-assets/mac-icon/AppIcon.icon by scripts/build-mac-icon.sh) beside the
  // old icon.icns, and both named in Info.plist. A release build (CI) must not go out without it; a local build may.
  const fs = require('fs');
  const res = path.join(app, 'Contents', 'Resources'), plist = path.join(app, 'Contents', 'Info.plist');
  const key = (k) => { try { return execFileSync('/usr/libexec/PlistBuddy', ['-c', 'Print :' + k, plist], { encoding: 'utf8' }).trim(); } catch (e) { return ''; } };
  const car = fs.existsSync(path.join(res, 'Assets.car')), icns = fs.existsSync(path.join(res, 'icon.icns'));
  console.log('  • icon: CFBundleIconName=' + key('CFBundleIconName') + ' CFBundleIconFile=' + key('CFBundleIconFile') + ' Assets.car ' + (car ? 'present' : 'MISSING') + ' icon.icns ' + (icns ? 'present' : 'MISSING'));
  if (process.env.CI && !(car && icns && key('CFBundleIconName') === 'AppIcon' && /^icon(\.icns)?$/.test(key('CFBundleIconFile')))) {
    throw new Error('Mac icon incomplete: the app needs Resources/Assets.car + CFBundleIconName=AppIcon and Resources/icon.icns + CFBundleIconFile (run scripts/build-mac-icon.sh before the build)');
  }
  console.log('  • ad-hoc signing', app);
  execFileSync('codesign', ['--force', '--deep', '--sign', '-', app], { stdio: 'inherit' });
  execFileSync('codesign', ['--verify', '--deep', '--strict', app], { stdio: 'inherit' });
};
