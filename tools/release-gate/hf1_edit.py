"""Task HF1 edit script: the v0.250 start-up glitch (controller echo loop), lkSel, peakOf, the update window.
Every anchor must occur exactly once; a second run is refused (the marker HF1 is checked first).
  python3 tools/release-gate/hf1_edit.py [index.html]"""
import sys, re
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
assert 'task HF1' not in s, 'HF1 is already in this file'

def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, old[:120])
    s = s.replace(old, new)

# ---------- 1. lkSel: the linked-clips one (FT-F1) becomes ftLinkSel; the look colour (LK) keeps lkSel ----------
rep("function lkSel(){const ids=SELCS.size?[...SELCS]:selC?[selC]:[],out=[];",
    "/* v0.261 (task HF1): was a second lkSel, which replaced task LK's lkSel(a) (the selection colour) everywhere: every selection outline got an array */\nfunction ftLinkSel(){const ids=SELCS.size?[...SELCS]:selC?[selC]:[],out=[];")
rep("run:()=>lkUnique(lkSel())}", "run:()=>lkUnique(ftLinkSel())}")
rep("function lkDupSel(){const f=lkSel()[0];", "function lkDupSel(){const f=ftLinkSel()[0];")
assert not re.search(r'lkSel\(\)', s), 'a caller of the linked-clips lkSel() is left'

# ---------- 2. peakOf twice (the same body): keep the first ----------
i1 = s.find('function peakOf(an){return mtrPeak(an)}'); i2 = s.find('function peakOf(an){return mtrPeak(an)}', i1 + 10)
assert i1 > 0 and i2 > 0 and s.count('function peakOf(') == 2
s = s[:i2] + '/* peakOf: declared once, above (task HF1) */' + s[i2 + len('function peakOf(an){return mtrPeak(an)}'):]

# ---------- 3. the controller layer: echoes, loops, surfaces only when turned on, Stop all controllers ----------
rep("const ctlOff=d=>!!(UI.ctlOff&&UI.ctlOff[d.name]);",
    "const ctlOff=d=>!!(UI.ctlStop||(d&&d.halt)||(UI.ctlOff&&UI.ctlOff[d.name]));/* task HF1: also off while all controllers are stopped, or a loop was found on the device */")
rep("function ctlAttach(d,re){const p=CTL.profs.find(x=>x.match(d))||CTL.profs[CTL.profs.length-1];if(d.prof===p&&re)return;",
    "function ctlAttach(d,re){let p=CTL.profs.find(x=>x.match(d))||CTL.profs[CTL.profs.length-1];\n  /* task HF1: a control surface profile (Push, Mackie, HUI, Launchpad, APC) only takes a device the user turned on as a surface; until then it is a plain device (notes play, nothing is sent to it) */\n  d.cand=null;if(p.surface&&!ctlSurfOn(d)){d.cand=p;p=CTL.profs.find(x=>x.id==='generic')||p;ctlSurfHint(d)}\n  if(d.prof===p&&re)return;")
rep("function ctlSend(d,bytes){if(!d||!d.out||ctlOff(d))return false;if(bytes[0]===0xF0&&!CTL.sysex)return false;try{d.out.send(bytes);CTL.n.out++;return true}catch(e){return false}}",
    "function ctlSend(d,bytes){if(!d||!d.out||ctlOff(d))return false;if(bytes[0]===0xF0&&!CTL.sysex)return false;try{d.out.send(bytes);ctlEcho(bytes);CTL.n.out++;return true}catch(e){return false}}")
rep("try{d.out.send(a);CTL.n.out++}", "try{d.out.send(a);ctlEcho(a);CTL.n.out++}", 4)
rep("function ctlMsg(d,data){CTL.n.in++;if(ctlOff(d))return;const a=data;",
    "function ctlMsg(d,data){CTL.n.in++;if(ctlOff(d))return;if(ctlGuard(d,data))return;const a=data;")
rep("function ctlDevOf(m){if(m.dev==='*'){for(const d of CTL.devs.values())if(d.out&&d.prof&&d.prof.id==='generic')return d;return null}for(const d of CTL.devs.values())if(d.name===m.dev)return d;return null}",
    "function ctlDevOf(m){/* task HF1: feedback only to a device the user turned on as a control surface (a plain device's output may lead straight back to its input) */\n  if(m.dev==='*'){for(const d of CTL.devs.values())if(d.out&&d.prof&&d.prof.id==='generic'&&ctlSurfOn(d)&&!ctlOff(d))return d;return null}for(const d of CTL.devs.values())if(d.name===m.dev)return d.prof&&d.prof.id==='generic'&&!ctlSurfOn(d)?null:d;return null}")
rep("setTimeout(()=>{if(!navigator.requestMIDIAccess)return;if(window.audiolabDesktop){ctlStart();return}",
    "setTimeout(()=>{if(!navigator.requestMIDIAccess||UI.ctlStop)return;if(window.audiolabDesktop){ctlStart();return}")

HF1 = r"""
/* v0.261 (task HF1): controllers can never drive AudioLab by themselves again. v0.250 reached the user's Mac and, with nothing touched,
   tracks got selected, the playhead moved, mutes and solos switched on, a track was duplicated and quitting froze. The start-up harness
   (tools/release-gate/smoke_electron.js) shows the same only when what AudioLab sends to a controller comes back on its input (a MIDI
   loop: a virtual port, a MIDI thru, a device that echoes): the Push profile lit its buttons (play, stop, duplicate, the track rows...)
   and read its own light messages back as presses, from v0.242 on (Push 1 part 2: the buttons run commands); v0.238 already looped
   without visible effects. Now:
   - every message sent is remembered for 50 ms; one that comes back the same within that time is ignored (ctlGuard);
   - a device whose input keeps returning what was sent to it (a loop), or that floods (over 1500 messages a second), is stopped for
     this session with a notice, and can be turned on again in Controllers;
   - a control surface profile (Push 1, Mackie Control, HUI, Launchpad, APC) takes a device only when the user turned it on as a surface
     in Controllers (or chose it under Works as); until then the device is a plain one: its notes play, nothing is sent to it;
   - mapping feedback goes only to devices turned on as surfaces;
   - Stop all controllers (Controllers page and the command list) switches all MIDI control and feedback off, kept across restarts. */
const HF1={win:50,flood:1500,loopN:24};
window.HF1=HF1;
function ctlEK(a){if(!a)return'';const n=a.length;if(n<=3)return((a[0]|0)*65536+((a[1]|0)<<8)+(a[2]|0));let k='x'+n;for(let i=0;i<n&&i<24;i++)k+=','+a[i];return k}
function ctlEcho(a){const E=CTL.echo||(CTL.echo=new Map()),t=performance.now();if(E.size>4096){for(const[k,v]of E)if(t-v>1000)E.delete(k);if(E.size>4096)E.clear()}E.set(ctlEK(a),t)}
/* true when the message must be dropped: an echo of what AudioLab sent, or the device is looping or flooding (then it is stopped) */
function ctlGuard(d,a){const t=performance.now(),r=d.rate||(d.rate={t:t,n:0,e:0});if(t-r.t>1000){r.t=t;r.n=0;r.e=0}r.n++;
  const off=a.length===3&&((a[0]&0xf0)===0x80||((a[0]&0xf0)===0x90&&a[2]===0)||((a[0]&0xf0)===0xE0&&d.prof&&d.prof.id==='mcu')||((a[0]&0xf0)===0xB0&&d.prof&&d.prof.id==='hui'&&(a[1]<8||(a[1]>=0x20&&a[1]<0x28)))),E=CTL.echo,s=off?null:E&&E.get(ctlEK(a)),echo=s!=null&&t-s<=1000;/* never dropped: a note-off (a lost one is a stuck note), and the motor faders of Mackie Control (pitch bend) and HUI (two-byte CCs): a touched fader may send the place it was just sent to */if(echo)r.e++;
  if(r.n>HF1.flood){ctlHalt(d,'flood');return true}
  if(r.e>=HF1.loopN&&r.e>=r.n*.6){ctlHalt(d,'loop');return true}
  if(echo&&t-s<=HF1.win){CTL.n.echo=(CTL.n.echo||0)+1;return true}
  return false}
function ctlHalt(d,why){if(d.halt)return;d.halt=why;CTL.n.halt=(CTL.n.halt||0)+1;try{if(d.prof&&d.prof.detach)d.prof.detach(d)}catch(e){}
  console.warn('AudioLab: controller '+d.name+' stopped ('+why+')');
  toast(why==='loop'?'AudioLab stopped listening to '+d.name+': what it sends there comes straight back (a MIDI loop). Turn it on again in Controllers.':'AudioLab stopped listening to '+d.name+': it sends far too many messages. Turn it on again in Controllers.');
  ctlPagePaint()}
function ctlSurfOn(d){return!!(d&&((UI.ctlOn&&UI.ctlOn[d.name])||(UI.ctlAs&&UI.ctlAs[d.name])))}
function ctlSurfHint(d){HF1.hinted=HF1.hinted||new Set();if(HF1.hinted.has(d.name)||!d.cand)return;HF1.hinted.add(d.name);
  setTimeout(()=>{if(d.cand&&CTL.devs.get(d.id)===d)toast(d.name+' looks like '+(d.cand.id==='grid'?'a Launchpad or APC':'a '+d.cand.name)+'. To let it control AudioLab, open Controllers and tick Control surface.')},1500)}
function ctlSurfSet(name,on){UI.ctlOn=Object.assign({},UI.ctlOn||{});if(on)UI.ctlOn[name]=1;else delete UI.ctlOn[name];saveUI();
  for(const d of CTL.devs.values())if(d.name===name){d.halt=null;ctlAttach(d)}ctlFbCount();ctlPagePaint()}
/* every profile but the generic one is a control surface (profiles added later too) */
for(const p of CTL.profs)if(p.id!=='generic'&&p.surface!==false)p.surface=true;
{const _p=ctlProf;ctlProf=function(p){if(p&&p.id!=='generic'&&p.surface!==false)p.surface=true;return _p.apply(this,arguments)}}
function ctlStopAll(stop){UI.ctlStop=stop?1:0;saveUI();
  for(const d of CTL.devs.values()){if(stop){try{if(d.prof&&d.prof.bye)d.prof.bye(d);else if(d.prof&&d.prof.detach)d.prof.detach(d)}catch(e){}}else{d.halt=null;ctlAttach(d)}}
  if(!stop)ctlStart();ctlFbCount();ctlPagePaint();toast(stop?'All controllers stopped: AudioLab ignores MIDI controllers and sends them nothing, also after a restart. Start them again in Controllers.':'Controllers on again.')}
SCA.push({id:'ctl.stopAll',g:'edit',l:'Stop all controllers (MIDI control off)',d:'',ic:'M5 5h10v10H5z',run:()=>ctlStopAll(!UI.ctlStop)});SCM.set('ctl.stopAll',SCA[SCA.length-1]);
/* the Controllers page: Stop all controllers, and per device a Control surface switch and why a device was stopped */
{const _p=ctlPagePaint;ctlPagePaint=function(){const r=_p.apply(this,arguments);const b=CTL.host;if(!b||!b.isConnected||b.closest('[hidden]'))return r;
  const bar=b.querySelector('.cmbar,.cbar');if(bar&&!bar.querySelector('[data-hf="stop"]')){const x=document.createElement('button');x.dataset.hf='stop';x.title='Switch all MIDI controllers off (nothing is read or sent), also after a restart; press again to start them';bar.appendChild(x)}
  const sb=b.querySelector('[data-hf="stop"]');if(sb){sb.textContent=UI.ctlStop?'Start controllers':'Stop all controllers';sb.classList.toggle('on',!!UI.ctlStop)}
  for(const row of b.querySelectorAll('label.cmdev,label.cdev')){const cb=row.querySelector('input[data-k2="dev"],input[data-ck="dev"]');if(!cb)continue;const name=cb.dataset.d,d=[...CTL.devs.values()].find(x=>x.name===name);if(!d)continue;
    if(!row.nextElementSibling||!row.nextElementSibling.classList.contains('hfsurf')){const w=document.createElement('label');w.className='hfsurf';w.style.cssText='display:flex;align-items:center;gap:6px;margin:-2px 0 4px 26px;opacity:.85';
      w.title='A control surface: AudioLab lights it up, writes its display and lets its buttons run commands (a Push, a Mackie or HUI surface, a Launchpad or APC). Off: it only plays notes and moves what you mapped, and AudioLab sends it nothing.';
      w.innerHTML='<input type="checkbox" data-hf="surf" title="Let this device work as a control surface"> <span>Control surface</span><em style="font-style:normal;opacity:.65"></em>';row.after(w)}
    const w=row.nextElementSibling,c=w.querySelector('input');c.dataset.d=name;c.checked=ctlSurfOn(d);
    w.querySelector('em').textContent=d.halt?(d.halt==='loop'?'Stopped: what AudioLab sent came straight back (a MIDI loop). Tick Use this device again to retry.':'Stopped: far too many messages.'):d.cand&&!ctlSurfOn(d)?'(looks like '+(d.cand.id==='grid'?'a Launchpad or APC':d.cand.name)+')':''}
  if(UI.ctlStop&&!b.querySelector('.hfstop')){const n=document.createElement('div');n.className='hfstop cmnone';n.textContent='All controllers are stopped: AudioLab ignores MIDI controllers and sends them nothing.';(bar||b.firstChild)&&b.insertBefore(n,bar?bar.nextSibling:b.firstChild)}
  else if(!UI.ctlStop){const n=b.querySelector('.hfstop');if(n)n.remove()}
  if(!b._hf){b._hf=1;b.addEventListener('click',e=>{const x=e.target.closest('[data-hf="stop"]');if(x){e.stopPropagation();ctlStopAll(!UI.ctlStop)}},true);
    b.addEventListener('change',e=>{const x=e.target.closest('input[data-hf="surf"]');if(x){e.stopPropagation();ctlSurfSet(x.dataset.d,x.checked);return}
      const u=e.target.closest('input[data-k2="dev"],input[data-ck="dev"]');if(u&&u.checked)for(const d of CTL.devs.values())if(d.name===u.dataset.d&&d.halt){d.halt=null;d.rate=null;ctlAttach(d)}},true)}
  return r}}
"""
rep("FT_HOOKS.gridPaint=()=>lpAll();", "FT_HOOKS.gridPaint=()=>lpAll();" + HF1)

# ---------- 4. the update window: the notes scroll inside a fixed area, the buttons always show; newest first, at most 8 ----------
rep(".uyww{position:relative;width:min(470px,calc(100vw - 32px));max-height:calc(100vh - 48px);overflow:auto;",
    ".uyww{position:relative;width:min(470px,calc(100vw - 32px));max-height:min(640px,calc(100vh - 48px));overflow:hidden;display:flex;flex-direction:column;")
rep(".uywb{display:flex;justify-content:flex-end;gap:8px;margin-top:4px}",
    ".uywbody{display:flex;flex-direction:column;min-height:0;flex:1 1 auto}.uywsc{flex:1 1 auto;min-height:60px;overflow:auto;overscroll-behavior:contain;margin:0 -6px 8px 0;padding-right:6px}\n.uywnl{margin:0;padding:8px 12px 8px 26px;border-radius:10px;font-size:var(--fs2);line-height:1.45;color:#dfe2ea;background:rgba(76,141,255,.1);border:1px solid rgba(76,141,255,.35);display:grid;gap:6px}.uywnl li.more{list-style:none;margin-left:-14px;color:#9ba0ad;font-size:var(--fs1)}\n.uywb{flex:none;display:flex;justify-content:flex-end;gap:8px;margin-top:4px;padding-top:8px;border-top:1px solid rgba(255,255,255,.08)}")
rep("    ${notes?`<div class=\"uywsec\"><h5>What is new</h5><p class=\"uywn\">${esc(notes)}</p></div>`:''}",
    "    <div class=\"uywsc\">${notes?(()=>{/* task HF1: newest first (update-notes.txt has the newest line on top), at most 8 */const L=notes.split(/\\n+/).map(x=>x.trim()).filter(Boolean),sh=L.slice(0,8);return`<div class=\"uywsec\"><h5>What is new</h5><ul class=\"uywnl\">${sh.map(x=>`<li>${esc(x)}</li>`).join('')}${L.length>sh.length?`<li class=\"more\">and ${L.length-sh.length} earlier change${L.length-sh.length>1?'s':''}</li>`:''}</ul></div>`})():''}")
rep("    <div class=\"uywsec\"><h5>What to do</h5><ol class=\"uywst\">${steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol>${note?`<p class=\"uywnote\" title=\"macOS keeps a copy of app icons and sometimes shows the old one until you log in again\">${esc(note)}</p>`:''}</div>\n    <div class=\"uywb\">${btn.join('')}</div>`}",
    "    <div class=\"uywsec\"><h5>What to do</h5><ol class=\"uywst\">${steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol>${note?`<p class=\"uywnote\" title=\"macOS keeps a copy of app icons and sometimes shows the old one until you log in again\">${esc(note)}</p>`:''}</div></div>\n    <div class=\"uywb\">${btn.join('')}</div>`}")

open(P, 'w', encoding='utf-8').write(s)
print('HF1 edits applied to', P)
