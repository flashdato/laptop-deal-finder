const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open();
 await p.goto('https://www.mymarket.ge/en/products/used/technic/computers/notebook/',{waitUntil:'domcontentloaded',timeout:90000});
 await p.waitForTimeout(3000);
 const api=async(body)=>p.evaluate(async(body)=>{ const r=await fetch('https://api.mymarket.ge/api/ka/products',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); return await r.json();},body);
 const all={}; const tag=(pr,t)=>{ if(!all[pr.product_id]) all[pr.product_id]={...pr,_tags:[]}; all[pr.product_id]._tags.push(t); };
 for(let pg=1;pg<=12;pg++){ const d=await api({CatID:'53',CondTypeID:'0',Limit:100,Page:pg}); const prs=d.data?.Prs||[]; prs.forEach(x=>tag(x,'used')); console.log('used page',pg,prs.length,d.data?.totalCount); if(prs.length<100) break; }
 const kws=['დაზიანებული','ნაწილებად','ნაწილად','გატეხილი','არ ირთვება','ეკრანი','დედაპლატა','წყალი','წყალში','დეფექტი','broken','for parts','not working','damaged','parts','ბლოკირებული','შესაკეთებელი','разбит','на запчасти'];
 for(const kw of kws){ for(const cat of ['53',null]){ for(let pg=1;pg<=5;pg++){ const body={Keyword:kw,Limit:100,Page:pg}; if(cat) body.CatID=cat; const d=await api(body); const prs=(d.data?.Prs||[]); const lap=prs.filter(x=>x.cat_id==53); lap.forEach(x=>tag(x,'kw:'+kw)); console.log('kw',kw,cat,pg,prs.length,'laptops',lap.length,d.data?.totalCount); if(prs.length<100) break; } } }
 // locations
 const locs=await p.evaluate(async()=>{const r=await fetch('https://api.mymarket.ge/api/en/locations'); return await r.json();});
 fs.writeFileSync('mm_locs.json',JSON.stringify(locs));
 fs.writeFileSync('mm_all.json',JSON.stringify(Object.values(all)));
 console.log('TOTAL',Object.keys(all).length);
 await b.close();})();
