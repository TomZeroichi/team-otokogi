/* TEAM 狭気：承認済みロゴと起動時コンセプト */
'use strict';
(function(){
  const LOGO='./static/kyoki-logo-hi-512.webp?v=1';
  const copy='勝っても、負けても<br>仲間のために、胸を張って奢る<br><br><span>弱きを助け、強きを挫く</span><br><strong>義理と人情でつながる、TEAM 狭気🔥</strong>';
  function addStyle(){
    if(document.getElementById('kyoki-brand-style'))return;
    const style=document.createElement('style');
    style.id='kyoki-brand-style';
    style.textContent='.kyoki-header-mark{width:48px;height:48px;object-fit:cover;border-radius:50%;border:1px solid rgba(232,191,99,.8);box-shadow:0 2px 14px #000;display:block}.kyoki-header-copy{margin-left:9px;line-height:1.05;text-align:left}.kyoki-header-copy b{display:block;color:#f3d580;font-size:16px;letter-spacing:.08em}.kyoki-header-copy small{display:block;margin-top:4px;color:#d0ae69;font-size:8px;letter-spacing:.22em}.kyoki-splash-logo{width:min(78vw,330px);aspect-ratio:1;object-fit:cover;border-radius:50%;border:1px solid rgba(232,191,99,.65);box-shadow:0 16px 42px #000}.kyoki-splash-copy{margin-top:19px;font:700 14px/1.85 sans-serif;color:#f5e6c5;text-shadow:0 1px 5px #000}.kyoki-splash-copy span{color:#eac06b}.kyoki-splash-copy strong{display:block;margin-top:5px;color:#f0ca72}@media(max-width:380px){.kyoki-splash-logo{width:64vw}.kyoki-splash-copy{font-size:13px}}';
    document.head.appendChild(style);
  }
  function splash(){
    if(document.getElementById('kyoki-splash'))return;
    const el=document.createElement('section');
    el.id='kyoki-splash';
    el.setAttribute('aria-label','TEAM 狭気 コンセプト');
    el.innerHTML='<div class="kyoki-splash-inner"><img class="kyoki-splash-logo" src="'+LOGO+'" alt="TEAM 狭気"><div class="kyoki-splash-copy">'+copy+'</div></div>';
    el.style.cssText='position:fixed;inset:0;z-index:9999;display:grid;place-items:center;padding:22px;background:radial-gradient(circle at 50% 13%,#55221f 0,transparent 34%),linear-gradient(145deg,#050708,#111719);text-align:center;opacity:1;transition:opacity .55s ease';
    el.firstElementChild.style.cssText='max-width:360px';
    document.body.appendChild(el);
    setTimeout(()=>{el.style.opacity='0';setTimeout(()=>el.remove(),600)},2800);
  }
  function apply(){
    const lead=document.querySelector('.auth-hero p');
    if(lead&&lead.dataset.kyokiConcept!=='1'){lead.dataset.kyokiConcept='1';lead.innerHTML=copy;}
    const title=document.querySelector('.brand');
    if(title&&!title.dataset.kyokiLogo){
      title.dataset.kyokiLogo='1';
      title.style.display='flex';title.style.alignItems='center';title.style.minWidth='0';
      title.innerHTML='<img class="kyoki-header-mark" src="'+LOGO+'" alt="TEAM 狭気"><div class="kyoki-header-copy"><b>狭気</b><small>TEAM OTOKOGI</small></div>';
    }
  }
  document.addEventListener('DOMContentLoaded',()=>{addStyle();splash();apply();});
  new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true});
})();