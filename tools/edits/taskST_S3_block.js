// v0.236 (task ST-S3): settings step S3, what was out of sync is in sync. Mono and L and R swap: every change repaints the master strip buttons
// (Settings used to change the sound but leave the buttons as they were). Follow: Settings shows all six ways the menu offers and the
// "follow again" switch; the command and the menu refresh Settings. Visualizer: its own header (the X and the place select) and Settings
// stay in step. Nothing per frame; the audio path is not touched (monSet is only wrapped to repaint).
const STS3={v:'0.236'};
{const _m3=monSet;monSet=function(){const r=_m3.apply(this,arguments);try{monPaint()}catch(e){}return r}}
{const _v3=vizApply;vizApply=function(){const r=_v3.apply(this,arguments);try{pvSync()}catch(e){}try{vizPaintBtns()}catch(e){}return r}}
{const c=document.getElementById('setFollowRes');if(c){c.checked=UI.followResume!==false;c.onchange=()=>{UI.followResume=c.checked;saveUI()}}
 const g=document.getElementById('setFollowC');if(g)for(const b of g.children){const s=b.querySelector('small'),t=b.querySelector('b');if(s&&t&&!b.title)b.title=t.textContent+': '+s.textContent}}
