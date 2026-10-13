const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open();
 await p.goto('https://www.mymarket.ge/en/products/used/technic/computers/notebook/',{waitUntil:'domcontentloaded',timeout:90000});
 await p.waitForTimeout(4000);
 const html=await p.content(); fs.writeFileSync('page.html',html);
 const r=await p.evaluate(async()=>{ const out={}; for (const body of [{CatID:53,Page:1,Limit:5},{CatID:'53',Page:1,ConditionTypeID:2}]) { try{ const res=await fetch('https://api.mymarket.ge/api/en/products',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); out[JSON.stringify(body)]=res.status+' '+(await res.text()).slice(0,3000);}catch(e){out[JSON.stringify(body)]='ERR '+e.message} } return out;});
 console.log(JSON.stringify(r,null,1)); await b.close();})();
