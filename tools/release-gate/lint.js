/* Release gate, step (a): the lint (task HF1).
   index.html is one big page whose scripts share one scope, so two functions with the same name do not fail: the later one silently replaces
   the first (v0.255 had two lkSel functions: the look colour and the linked clips; every selection drawing got an array instead of a colour).
   Fails on:
   - a top-level function name declared twice in the same scope (each classic <script> body; module scripts on their own),
   - a top-level function declared with the same name as a top-level const/let/class (a SyntaxError that stops the whole page),
   - an element id written twice in the static HTML, or twice in the same template string or literal in the scripts
     (ids made by code at run time are checked in the page by smoke_electron.js and windows.js).
   Known, harmless duplicate ids can be listed in lint-allow.json with the reason; the gate prints them.
     node tools/release-gate/lint.js [index.html]        exit 0 when clean */
const fs = require('fs'), path = require('path');
const dep = (m) => { for (const p of [path.join(__dirname, '.deps', 'node_modules', m), m]) { try { return require(p); } catch (e) { /* next */ } } throw new Error('missing ' + m + ': npm install --prefix tools/release-gate/.deps acorn@8.14.0'); };
const acorn = dep('acorn');
const FILE = path.resolve(process.argv[2] || path.join(__dirname, '..', '..', 'index.html'));
const html = fs.readFileSync(FILE, 'utf8');
let allow = {}; try { allow = JSON.parse(fs.readFileSync(path.join(__dirname, 'lint-allow.json'), 'utf8')); } catch (e) { /* none */ }
const fail = [], note = [];
const lineOf = (i) => html.slice(0, i).split('\n').length;

/* the scripts: inline <script> bodies (not src=, not JSON or other types) */
const scripts = []; const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi; let m;
while ((m = re.exec(html))) {
  const attrs = m[1]; if (/\bsrc=/.test(attrs)) continue; const ty = (/\btype=["']?([^"'\s>]+)/i.exec(attrs) || [])[1] || '';
  if (ty && !/^(module|text\/javascript|application\/javascript)$/i.test(ty)) continue;
  scripts.push({ code: m[2], at: m.index + m[0].indexOf('>') + 1, module: /^module$/i.test(ty) });
}
/* classic scripts share the global scope: their top-level functions are one namespace */
const seen = new Map(), lex = new Map();
for (const s of scripts) {
  let ast; try { ast = acorn.parse(s.code, { ecmaVersion: 'latest', sourceType: s.module ? 'module' : 'script', allowHashBang: true, allowReturnOutsideFunction: true }); }
  catch (e) { fail.push('script at line ' + lineOf(s.at) + ' does not parse: ' + e.message + ' (line ' + (lineOf(s.at) + (e.loc ? e.loc.line - 1 : 0)) + ')'); continue; }
  const ns = s.module ? new Map() : seen, nl = s.module ? new Map() : lex;
  /* the app's main script is one block { ... }: its direct statements are the page's top level */
  const body = []; for (const n of ast.body) { if (n.type === 'BlockStatement') body.push(...n.body); else body.push(n); }
  for (const n of body) {
    if (n.type === 'FunctionDeclaration' && n.id) { const k = n.id.name, ln = lineOf(s.at + n.start); if (ns.has(k)) fail.push('function ' + k + ' is declared twice (lines ' + ns.get(k) + ' and ' + ln + '): the later one replaces the first everywhere'); else ns.set(k, ln); }
    if (n.type === 'VariableDeclaration' && n.kind !== 'var') for (const d of n.declarations) if (d.id && d.id.type === 'Identifier') nl.set(d.id.name, lineOf(s.at + n.start));
    if (n.type === 'ClassDeclaration' && n.id) nl.set(n.id.name, lineOf(s.at + n.start));
  }
  for (const [k, ln] of ns) if (nl.has(k)) fail.push('function ' + k + ' (line ' + ln + ') has the same name as a const/let/class (line ' + nl.get(k) + ')');
}
/* static ids: the HTML outside the scripts */
let stat = html; for (const s of scripts.slice().reverse()) stat = stat.slice(0, s.at) + ' '.repeat(s.code.length) + stat.slice(s.at + s.code.length);
const ids = new Map(); const ire = /\sid\s*=\s*["']([^"'${}]+)["']/g;
while ((m = ire.exec(stat))) { const k = m[1]; (ids.get(k) || ids.set(k, []).get(k)).push(lineOf(m.index)); }
/* ids inside one string or template in the scripts (a piece of markup written twice the same id) */
for (const s of scripts) {
  const sre = /`(?:[^`\\]|\\.)*`|'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*"/g; let q;
  while ((q = sre.exec(s.code))) { const t = q[0]; if (t.length < 20 || !/\sid=/.test(t)) continue; const c = new Map(); let r; const re2 = /\sid=\\?["']([A-Za-z][\w-]*)\\?["']/g;
    while ((r = re2.exec(t))) c.set(r[1], (c.get(r[1]) || 0) + 1);
    for (const [k, n] of c) if (n > 1) (ids.get(k) || ids.set(k, []).get(k)).push(lineOf(s.at + q.index), lineOf(s.at + q.index)); }
}
for (const [k, ls] of ids) if (ls.length > 1) { if (allow[k]) note.push('id "' + k + '" twice (lines ' + ls.join(', ') + '), allowed: ' + allow[k]); else fail.push('element id "' + k + '" is written twice (lines ' + ls.join(', ') + ')'); }

for (const n of note) console.log('note ' + n);
for (const f of fail) console.log('FAIL ' + f);
console.log(fail.length ? 'lint: ' + fail.length + ' problem' + (fail.length > 1 ? 's' : '') : 'lint: clean (' + seen.size + ' top-level functions, ' + scripts.length + ' scripts)');
process.exit(fail.length ? 1 : 0);
