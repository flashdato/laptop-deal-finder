const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open();
 p.on('request', r => { const u=r.url(); if (u.includes('ss.ge') && ['xhr','fetch'].includes(r.resourceType())) console.log('REQ',r.method(),u,(r.postData()||'').slice(0,200)); });
 await p.goto('https://ss.ge/en/sales/details/--computers-2284953',{waitUntil:'domcontentloaded',timeout:90000});
 await p.waitForTimeout(3000);
 const t=await p.evaluate(()=>document.querySelector('main, .main, body').innerText);
 const i=t.indexOf('Price'); console.log(t.slice(0,3000));
 console.log(await p.evaluate(()=>[...document.querySelectorAll('[class*=phone],[class*=Phone],a[href^="tel:"]')].map(e=>e.className+' | '+e.outerHTML.slice(0,300)).join('\n')));
 await b.close();})();
