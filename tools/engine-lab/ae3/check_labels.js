// Checks the AE3 pick page: 27 options, each with a label kind, and every card (Fn) or idea (In)
// named in an "improves" or "covered" label was picked by the user (RF1: all F1-F40; RF2: the picks line).
// Run from the repository root: node tools/engine-lab/ae3/check_labels.js
const fs=require('fs');
const html=fs.readFileSync('tools/engine-lab/ae3/mixing-picks.html','utf8');
const src=html.slice(html.indexOf('const C=['),html.indexOf('];',html.indexOf('const C=['))+2);
const C=eval('('+src.slice(src.indexOf('['),src.lastIndexOf(']')+1)+')');
const rf2=fs.readFileSync('docs/research-features-new.md','utf8').match(/`RF2 picks: ([^`]+)`\s*$/m);
const ideas=new Set(rf2[1].split(/\s+/));
let bad=0;
if(C.length!==27){console.log('expected 27 options, got',C.length);bad++}
C.forEach((c,i)=>{const [id,,t,,,,kind,label]=c;
  if(id!=='X'+(i+1)){console.log('numbering',id);bad++}
  if(!['new','improves','covered'].includes(kind)){console.log(id,'bad kind',kind);bad++}
  if(kind!=='new'){const refs=label.match(/\b[FI]\d+\b/g)||[];if(!refs.length){console.log(id,'names no card or idea');bad++}
    refs.forEach(r=>{if(r[0]==='F'&&!(+r.slice(1)>=1&&+r.slice(1)<=40)){console.log(id,'unknown card',r);bad++}
      if(r[0]==='I'&&!ideas.has(r)){console.log(id,'idea not picked',r);bad++}})}});
console.log(bad?bad+' problem(s)':'ok: '+C.length+' options, labels point at picked cards and ideas');
process.exit(bad?1:0);
