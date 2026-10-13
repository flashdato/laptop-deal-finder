const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open();
 p.on('response', async r=>{ const u=r.url(); if(/api/.test(u) && /zoommer|ee\.ge|alta/.test(u) && r.request().resourceType()!='image'){ let t=''; try{t=await r.text()}catch(e){}; if(t.length>500) console.log('API',r.request().method(),u.slice(0,200),t.length,t.slice(0,150).replace(/\n/g,' ')); }});
 for(const u of ['https://zoommer.ge/leptopebi-c531','https://ee.ge/en/laptops-c58s','https://alta.ge/notebooks.html']){
  await p.goto(u,{waitUntil:'networkidle',timeout:60000}).catch(e=>console.log('nav',e.message)); await p.waitForTimeout(2000);
  console.log('PAGE',u,(await p.title()), (await p.evaluate(()=>document.body.innerText.length)));
 }
 await b.close();})();
