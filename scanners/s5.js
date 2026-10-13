const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,ctx,p}=await open(); const out=JSON.parse(fs.readFileSync('stores.json')).filter(x=>x.store=='Zoommer');
 const cap={};
 p.on('request',r=>{const u=r.url(); if(/\/v1\/Products\/v3\?CategoryId/.test(u)) cap[new URL(u).host]={u,h:r.headers()};});
 await p.goto('https://ee.ge/en/laptops-c58s',{waitUntil:'networkidle',timeout:60000}).catch(()=>{});
 await p.goto('https://alta.ge/notebooks.html',{waitUntil:'networkidle',timeout:60000}).catch(()=>{});
 console.log(Object.entries(cap).map(([k,v])=>k+' '+v.u));
 for(const [host,{u,h}] of Object.entries(cap)){ const store=host.includes('ee')?'EE':'Alta';
  for(let pg=1;pg<=30;pg++){ const url=u.replace(/Page=\d+/,'Page='+pg);
   const r=await ctx.request.get(url,{headers:h}); let d={}; try{d=await r.json()}catch(e){}
   const ps=d.products||[]; ps.forEach(x=>out.push({store,name:x.name,price:x.price,url:(store=='EE'?'https://ee.ge/en/':'https://alta.ge/')+(x.route||'')})); if(pg==1) console.log(store,Object.keys(d), ps[0]&&Object.keys(ps[0]).join(','));
   if(ps.length<16) break; } }
 fs.writeFileSync('stores.json',JSON.stringify(out)); const c={}; out.forEach(x=>c[x.store]=(c[x.store]||0)+1); console.log(c, out.slice(-2));
 await b.close();})();
