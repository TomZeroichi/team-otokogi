/* TEAM 狭気：起動時コンセプト表示 */
'use strict';
(function(){
  const copy='勝っても、負けても<br>仲間のために、胸を張って奢る<br><br><span>弱きを助け、強きを挫く</span><br><strong>義理と人情でつながる、TEAM 狭気🔥</strong>';
  function splash(){
    if(document.getElementById('kyoki-splash'))return;
    const el=document.createElement('section');
    el.id='kyoki-splash';
    el.setAttribute('aria-label','TEAM 狭気 コンセプト');
    el.innerHTML='<div class="kyoki-splash-inner"><div class="kyoki-splash-brand"><em>TEAM</em> 狭気</div><div class="kyoki-splash-sub">TEAM OTOKOGI</div><div class="kyoki-splash-copy">'+copy+'</div></div>';
    el.style.cssText='position:fixed;inset:0;z-index:9999;display:grid;place-items:center;padding:28px;background:radial-gradient(circle at 50% 13%,#59261f 0,transparent 34%),linear-gradient(145deg,#071014,#10191b);color:#f5dfad;text-align:center;opacity:1;transition:opacity .55s ease';
    const inner=el.firstElementChild;
    inner.style.cssText='max-width:360px;font-family:serif;line-height:1.9;letter-spacing:.06em';
    el.querySelector('.kyoki-splash-brand').style.cssText='font-size:38px;font-weight:900;color:#eac06b;text-shadow:0 2px 18px #000';
    el.querySelector('.kyoki-splash-sub').style.cssText='font:700 10px sans-serif;letter-spacing:.45em;color:#cfad70;margin-top:-4px';
    el.querySelector('.kyoki-splash-copy').style.cssText='margin-top:34px;font:700 16px sans-serif;line-height:2;color:#f5e6c5';
    document.body.appendChild(el);
    setTimeout(()=>{el.style.opacity='0';setTimeout(()=>el.remove(),600)},2800);
  }
  const apply=()=>{const lead=document.querySelector('.auth-hero p');if(lead&&lead.dataset.kyokiConcept!=='1'){lead.dataset.kyokiConcept='1';lead.innerHTML=copy;}};
  document.addEventListener('DOMContentLoaded',()=>{splash();apply();});
  new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true});
})();