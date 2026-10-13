const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open();
 const calls=[];
 p.on('request', r => { const u=r.url(); if (u.includes('api.mymarket')||u.includes('tnet.ge/api')) calls.push(r.method()+' '+u+' '+(r.postData()||'')); });
 await p.goto('https://www.mymarket.ge/en/products/used/technic/computers/notebook/',{waitUntil:'domcontentloaded',timeout:90000});
 await p.waitForTimeout(3000);
 const r=await p.evaluate(async()=>{ const res=await fetch('https://api.mymarket.ge/api/en/products',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({CatID:'53',CondTypeID:'0',Limit:100,Page:1})}); return await res.text();});
 fs.writeFileSync('list1.json',r);
 // open product page
 await p.goto('https://www.mymarket.ge/en/pr/36312560/',{waitUntil:'domcontentloaded',timeout:90000});
 await p.waitForTimeout(5000);
 fs.writeFileSync('prod.html',await p.content());
 console.log(calls.join('\n'));
 await b.close();})();
