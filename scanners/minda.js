const {open}=require('./lib');
(async()=>{ const {b,p}=await open();
 await p.goto('https://minda.city/en/elektro/computers.html',{waitUntil:'domcontentloaded',timeout:60000}).catch(e=>console.log('nav',e.message));
 await p.waitForTimeout(4000);
 const t=await p.evaluate(()=>document.body.innerText); console.log(t.slice(0,2500));
 await b.close();})();
