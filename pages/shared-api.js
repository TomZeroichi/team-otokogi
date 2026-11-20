/* TEAM狭気: GitHub Pages から共有データAPIへ接続する安全な橋渡し。 */
'use strict';
(function(){
  const endpoint='https://oclbjxbmruhelobjrtoo.supabase.co/functions/v1/kyoki-api';
  const storageKey='team-otokogi-session-v1';
  window.KYOKI_SHARED_API=async function(path,method='GET',body){
    let response;
    try{response=await fetch(endpoint,{method:'POST',cache:'no-store',headers:{'content-type':'application/json','x-kyoki-session':localStorage.getItem(storageKey)||''},body:JSON.stringify({path,method,body})});}
    catch{throw Error('サーバーに接続できません。通信状態をご確認ください。');}
    let result;try{result=await response.json();}catch{throw Error('サーバーから正しい応答がありません');}
    if(!response.ok)throw Error(result.error||'通信エラー');
    if(result.session)localStorage.setItem(storageKey,result.session);
    if(path==='/api/logout')localStorage.removeItem(storageKey);
    return result;
  };
  const nativeFetch=window.fetch.bind(window);
  window.fetch=function(input,options={}){
    const raw=typeof input==='string'?input:input.url,url=new URL(raw,location.href);
    if(!url.pathname.startsWith('/api/'))return nativeFetch(input,options);
    let body={};try{body=options.body?JSON.parse(options.body):{};}catch{return Promise.resolve(new Response(JSON.stringify({detail:'入力が不正です'}),{status:400,headers:{'content-type':'application/json'}}));}
    if(url.pathname==='/api/groups'&&location.search.includes('setup='))body.setup=new URLSearchParams(location.search).get('setup');
    return window.KYOKI_SHARED_API(url.pathname,options.method||'GET',body).then(data=>new Response(JSON.stringify(data),{status:200,headers:{'content-type':'application/json'}})).catch(error=>new Response(JSON.stringify({detail:error.message}),{status:/ログイン|有効期限/.test(error.message)?401:400,headers:{'content-type':'application/json'}}));
  };
})();