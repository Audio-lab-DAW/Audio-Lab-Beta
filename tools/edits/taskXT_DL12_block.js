/* ===================== SCRIPT SANDBOX (v0.000, task XT-DL12) =====================
   The spike of the scripts' sandbox (docs/extensions-plan.md 9.6 e and 9.7 DL12, findings in docs/script-sandbox.md). No user feature: nothing
   calls it yet; step DL13 (scripts, run once) builds on it. User code never runs in the page's own context:
   - each run gets a fresh iframe with sandbox="allow-scripts" (no allow-same-origin: an opaque origin, no access to the page, its storage,
     the desktop bridge or the parent's DOM; no popups, no navigation of the window, no dialogs);
   - the frame's own content security policy is default-src 'none' (only its inline script and blob workers may run), so fetch, XHR,
     WebSocket, EventSource, importScripts, import(), eval and new Function fail at the browser's own level, also inside the worker,
     which inherits the policy;
   - the user's code runs in a Worker inside that frame (never on the page's thread: an endless loop does not stop the window or the sound);
   - the page talks to it through one MessageChannel: only plain data goes in (al.input, a copy) and out (logs, a change list, a value),
     every message is checked and capped; the script never holds a live object of the app;
   - a time limit (2 s; onSlow may ask the user "wait or stop", K9b) and a heartbeat from the frame: no beat for 1.5 s means the frame's
     process died (a script that ate all memory: with site isolation, Chrome's and Electron's default, it has its own process);
   - stopping removes the frame, which ends its worker even inside an endless loop.
   Nothing exists until a run: no frame, no worker, no listener. A finished run leaves nothing behind. */
const XT_SBX={n:0,runs:new Map(),
  CSP:"default-src 'none'; script-src 'unsafe-inline' blob:; worker-src blob:",
  MAXCODE:262144,MAXOUT:1048576,MAXLOG:200,MAXCHG:10000,BEAT:200,DEAD:1500};
/* the frame's own script (runs in the sandboxed frame, never in the page): builds the worker, relays its messages, beats */
const XT_SBX_FRAME='onmessage=function(e){if(e.source!==parent||!e.data||e.data.t!=="xt-sbx-init"||!e.ports[0])return;onmessage=null;'+
 'var p=e.ports[0],d=e.data,w;try{var u=URL.createObjectURL(new Blob([d.src],{type:"text/javascript"}));w=new Worker(u);URL.revokeObjectURL(u)}'+
 'catch(x){p.postMessage({t:"err",v:"the sandbox could not start: "+(x&&x.message||x)});return}'+
 'w.onerror=function(ev){ev.preventDefault();p.postMessage({t:"err",v:String(ev.message||"error"),line:ev.lineno|0})};'+
 'var c=new MessageChannel();c.port1.onmessage=function(ev){p.postMessage(ev.data)};'+
 'p.onmessage=function(ev){if(ev.data&&ev.data.t==="kill"){w.terminate();clearInterval(h)}};'+
 'var h=setInterval(function(){p.postMessage({t:"hb"})},'+XT_SBX.BEAT+');'+
 'w.postMessage({t:"xt-sbx-port",input:d.input},[c.port2])}';
/* the worker's prelude: console and al (input, change); the user's code follows inside an async function */
const XT_SBX_PRE='"use strict";(function(){var P=null,N=0,C=0;'+
 'function out(m){if(P)P.postMessage(m)}'+
 'function str(a){return Array.prototype.map.call(a,function(x){if(typeof x==="string")return x;try{return JSON.stringify(x)}catch(e){return String(x)}}).join(" ").slice(0,500)}'+
 'function lg(k){return function(){if(N++<'+XT_SBX.MAXLOG+')out({t:"log",k:k,v:str(arguments)})}}'+
 'var con={log:lg("log"),info:lg("log"),warn:lg("warn"),error:lg("error")};'+
 'self.onmessage=function(e){if(P||!e.data||e.data.t!=="xt-sbx-port"||!e.ports[0])return;P=e.ports[0];self.onmessage=null;'+
 'var input=e.data.input;(function fr(o){if(o&&typeof o==="object"){Object.freeze(o);for(var k in o)fr(o[k])}})(input);'+
 'var al=Object.freeze({api:"0",input:input,change:function(c){if(C++>='+XT_SBX.MAXCHG+')throw new Error("too many changes");'+
 'out({t:"chg",v:JSON.parse(JSON.stringify(c===undefined?null:c))})}});'+
 'self.__xtGo(al,con).then(function(v){out({t:"done",v:v===undefined?null:JSON.parse(JSON.stringify(v))})},'+
 'function(x){out({t:"err",v:String(x&&x.message||x),stack:String(x&&x.stack||"").slice(0,1000)})})};'+
 '})();\nself.__xtGo=async function(al,console){\n';
const XT_SBX_PRE_LINES=XT_SBX_PRE.split('\n').length-1;
/* run code in the sandbox. opts: input (plain data, copied), limit (ms, 2000), onSlow(ms) -> true or a Promise of true to wait another limit,
   onLog(line). Resolves to {ok, value, changes, logs, error, line, stopped ('time' | 'memory' | 'user' | null), ms}; never rejects. */
function xtSandboxRun(code,opts){opts=opts||{};const id=++XT_SBX.n,t0=performance.now(),lim=Math.max(50,+opts.limit||2000);
  const nl=typeof code==='string'?code.split('\n').length:0,R={id,ok:false,value:null,changes:[],logs:[],error:null,line:0,stopped:null,ms:0};
  return new Promise(res=>{
    if(typeof code!=='string'||code.length>XT_SBX.MAXCODE){R.error='the script is empty or larger than 256 kB';res(R);return}
    let inp=null;try{inp=opts.input===undefined?null:JSON.parse(JSON.stringify(opts.input))}catch(e){R.error='the input is not plain data';res(R);return}
    const f=document.createElement('iframe'),ch=new MessageChannel();let done=false,tm=0,wd=0,beat=performance.now(),bytes=0,asking=false;
    f.setAttribute('sandbox','allow-scripts');f.setAttribute('aria-hidden','true');f.tabIndex=-1;f.dataset.xtSbx=id;
    f.style.cssText='position:fixed;width:0;height:0;border:0;left:-9px;top:-9px;visibility:hidden;pointer-events:none';
    const fin=(why)=>{if(done)return;done=true;clearTimeout(tm);clearInterval(wd);try{ch.port1.postMessage({t:'kill'})}catch(e){}
      ch.port1.onmessage=null;try{ch.port1.close()}catch(e){}f.remove();XT_SBX.runs.delete(id);if(why)R.stopped=why;R.ms=Math.round(performance.now()-t0);res(R)};
    const slow=()=>{if(done)return;if(typeof opts.onSlow!=='function'){R.error='stopped after '+(lim/1000)+' s';fin('time');return}
      asking=true;Promise.resolve().then(()=>opts.onSlow(Math.round(performance.now()-t0))).then(w=>{asking=false;if(done)return;
        if(w===true)tm=setTimeout(slow,lim);else{R.error='stopped by you after '+((performance.now()-t0)/1000).toFixed(1)+' s';fin('user')}},
        ()=>{asking=false;R.error='stopped';fin('user')})};
    ch.port1.onmessage=e=>{if(done)return;const d=e.data;if(!d||typeof d!=='object'||typeof d.t!=='string')return;beat=performance.now();
      if(d.t==='hb')return;
      let sz=0;try{sz=JSON.stringify(d).length}catch(x){sz=XT_SBX.MAXOUT+1}bytes+=sz;
      if(bytes>XT_SBX.MAXOUT){R.error='the script sent more than 1 MB back';fin('size');return}
      if(d.t==='log'){if(R.logs.length<XT_SBX.MAXLOG){const L={k:['log','warn','error'].includes(d.k)?d.k:'log',v:String(d.v).slice(0,500)};R.logs.push(L);
        if(typeof opts.onLog==='function')try{opts.onLog(L)}catch(x){}}}
      else if(d.t==='chg'){if(R.changes.length<XT_SBX.MAXCHG)R.changes.push(d.v)}
      else if(d.t==='done'){R.ok=true;R.value=d.v;fin(null)}
      else if(d.t==='err'){R.error=String(d.v).slice(0,500);R.line=Math.max(0,(d.line|0)-XT_SBX_PRE_LINES);
        if(!R.line&&d.stack){const m=/blob:[^\s)]*?:(\d+):\d+/.exec(String(d.stack));if(m)R.line=Math.max(0,(+m[1])-XT_SBX_PRE_LINES)}if(R.line)R.line=Math.min(R.line,nl);fin(null)}};
    tm=setTimeout(slow,lim);
    wd=setInterval(()=>{if(!done&&!asking&&performance.now()-beat>XT_SBX.DEAD){R.error='the script used too much memory or crashed its sandbox, and was stopped';fin('memory')}},250);
    XT_SBX.runs.set(id,{stop:()=>{R.error='stopped';fin('user')}});
    const src=XT_SBX_PRE+code+'\n};';
    f.srcdoc='<!doctype html><meta http-equiv="Content-Security-Policy" content="'+XT_SBX.CSP.replace(/"/g,'&quot;')+'"><script>'+XT_SBX_FRAME+'<\/script>';
    f.addEventListener('load',()=>{if(done)return;beat=performance.now();try{f.contentWindow.postMessage({t:'xt-sbx-init',src,input:inp},'*',[ch.port2])}catch(e){R.error='the sandbox could not start';fin(null)}},{once:true});
    (document.body||document.documentElement).appendChild(f);
  })}
/* stop one run (id) or all of them */
function xtSandboxStop(id){for(const [k,r] of [...XT_SBX.runs])if(id==null||k===id)r.stop()}
