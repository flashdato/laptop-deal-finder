const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open();
 await p.goto('https://www.mymarket.ge/en/',{waitUntil:'domcontentloaded',timeout:90000});
 for(const id of ['36205259','36314777']){ const d=await p.evaluate(async(id)=>{ const r=await fetch('https://api.mymarket.ge/api/en/products/'+id); return await r.text();},id); fs.writeFileSync('ex_'+id+'.json',d);}
 await b.close();})();
