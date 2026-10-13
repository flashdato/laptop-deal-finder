const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open();
 p.on('request', r => { const u=r.url(); if (u.includes('ss.ge') && ['xhr','fetch'].includes(r.resourceType())) console.log('REQ',r.method(),u,(r.postData()||'').slice(0,500)); });
 await p.goto('https://ss.ge/en/sales/list?SaleTypeId=5&CategoryId=231',{waitUntil:'networkidle',timeout:90000}).catch(e=>console.log(e.message));
 await p.waitForTimeout(4000);
 const n=await p.evaluate(()=>document.querySelectorAll('.latest_article_each[data-id]').length); console.log('items',n);
 console.log(await p.evaluate(()=>document.body.innerText.slice(0,1500)));
 fs.writeFileSync('ss231.html',await p.content());
 await b.close();})();
