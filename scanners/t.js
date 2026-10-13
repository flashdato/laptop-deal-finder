const {open}=require('./lib');
(async()=>{ const {b,p}=await open();
 await p.goto('https://www.mymarket.ge/en/',{waitUntil:'domcontentloaded',timeout:90000});
 const d=await p.evaluate(async()=>{ const r=await fetch('https://api.mymarket.ge/api/ka/products/36257006'); return await r.text();});
 const i=d.indexOf('phone'); console.log(d.slice(0,300)); let k=0; for(const m of d.matchAll(/"[a-z_]*phone[a-z_]*":[^,]{0,40}/gi)){console.log(m[0]); if(++k>8)break;}
 await b.close();})();
