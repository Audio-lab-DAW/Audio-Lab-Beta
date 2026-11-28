/* Task WS-F (lane Q): the test songs for the Electron tests (index.html ships no song). The page cannot fetch tools/test-songs/
   next to itself in the desktop app, so the files go in as window.AL_TEST_SONGS before the page's scripts run:
     await app.context().addInitScript(require('../test-songs/alsong.js').initScript());   */
const fs = require('fs'), path = require('path');
function songs() {
  const M = JSON.parse(fs.readFileSync(path.join(__dirname, 'fractals.json'), 'utf8'));
  const files = ['fractals.json', M.file, ...M.vox.map((v) => v[1])], o = {};
  for (const p of files) o[p] = fs.readFileSync(path.join(__dirname, p)).toString('base64');
  return o;
}
function initScript() { return 'window.AL_TEST_SONGS=' + JSON.stringify(songs()) + ';'; }
module.exports = { songs, initScript };
