/* TEAM 狭気：冒頭コンセプト表示 */
'use strict';
(function(){
  const copy='勝っても、負けても<br>仲間のために、胸を張って奢る<br><br>弱きを助け、強きを挫く<br><strong>義理と人情でつながる、TEAM 狭気🔥</strong>';
  const apply=()=>{
    const lead=document.querySelector('.auth-hero p');
    if(lead&&lead.dataset.kyokiConcept!=='1'){lead.dataset.kyokiConcept='1';lead.classList.add('kyoki-concept');lead.innerHTML=copy;}
  };
  new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',apply);
})();