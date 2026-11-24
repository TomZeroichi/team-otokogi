/* TEAM 狭気：承認済みロゴと起動時コンセプト */
'use strict';
(function(){
  const LOGO='./static/kyoki-logo-hi-512.png?v=1';
  const COPY='勝っても、負けても<br>仲間のために、胸を張って奢る<br><br><span>弱きを助け、強きを挫く</span><br><strong>義理と人情でつながる、TEAM 狭気🔥</strong>';
  function addStyle(){
    if(document.getElementById('kyoki-brand-style')) return;
    const style=document.createElement('style');
    style.id='kyoki-brand-style';
    style.textContent=`.brand.kyoki-brand{display:flex!important;flex-direction:row!important;align-items:center!important;gap:9px!important;min-width:0!important;max-width:260px!important;text-align:left!important}.kyoki-header-mark{display:block!important;width:43px!important;height:43px!important;min-width:43px!important;object-fit:cover!important;border-radius:50%!important;border:1px solid #e5bd68!important;box-shadow:0 0 0 2px #0a1012,0 2px 11px #000!important;opacity:1!important;visibility:visible!important}.kyoki-header-copy{display:block!important;margin:0!important;line-height:1.05!important;text-align:left!important;white-space:nowrap!important}.kyoki-header-copy b{display:block!important;color:#f5d88d!important;font-family:"Yu Mincho","Hiragino Mincho ProN",serif!important;font-size:19px!important;letter-spacing:.04em!important;text-shadow:0 1px 0 #7e4c1a,0 0 11px rgba(226,165,62,.42)!important}.kyoki-header-copy b:before{content:none!important}.kyoki-header-copy small{display:block!important;margin-top:3px!important;color:#d9b96e!important;font-size:7px!important;letter-spacing:.32em!important}.kyoki-splash-logo{width:min(78vw,330px);aspect-ratio:1;object-fit:cover;border-radius:50%;border:1px solid rgba(232,191,99,.65);box-shadow:0 16px 42px #000}.kyoki-splash-copy{margin-top:19px;font:700 14px/1.85 sans-serif;color:#f5e6c5;text-shadow:0 1px 5px #000}.kyoki-splash-copy span{color:#eac06b}.kyoki-splash-copy strong{display:block;margin-top:5px;color:#f0ca72}@media(max-width:380px){.kyoki-splash-logo{width:64vw}.kyoki-splash-copy{font-size:13px}.kyoki-header-mark{width:38px!important;height:38px!important;min-width:38px!important}.kyoki-header-copy b{font-size:17px!important}}`;
    document.head.appendChild(style);
  }
  function splash(){
    if(document.getElementById('kyoki-splash')) return;
    const el=document.createElement('section');
    el.id='kyoki-splash'; el.setAttribute('aria-label','TEAM 狭気 コンセプト');
    el.innerHTML='<div class="kyoki-splash-inner"><img class="kyoki-splash-logo" src="'+LOGO+'" alt="TEAM 狭気"><div class="kyoki-splash-copy">'+COPY+'</div></div>';
    el.style.cssText='position:fixed;inset:0;z-index:9999;display:grid;place-items:center;padding:22px;background:radial-gradient(circle at 50% 13%,#55221f 0,transparent 34%),linear-gradient(145deg,#050708,#111719);text-align:center;opacity:1;transition:opacity .55s ease;pointer-events:none';
    el.firstElementChild.style.cssText='max-width:360px'; document.body.appendChild(el);
    setTimeout(()=>{el.style.opacity='0';setTimeout(()=>el.remove(),600)},5000);
  }
  function apply(){
    const lead=document.querySelector('.auth-hero p');
    if(lead&&lead.dataset.kyokiConcept!=='1'){lead.dataset.kyokiConcept='1';lead.innerHTML=COPY;}
    const title=document.querySelector('.brand');
    if(title&&!title.dataset.kyokiLogo){
      title.dataset.kyokiLogo='1'; title.classList.add('kyoki-brand');
      title.innerHTML='<img class="kyoki-header-mark" src="'+LOGO+'" alt="TEAM 狭気"><div class="kyoki-header-copy"><b>TEAM 狭気</b><small>TEAM OTOKOGI</small></div>';
    }
  }
  document.addEventListener('DOMContentLoaded',()=>{addStyle();splash();apply();});
  new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true});
})();
