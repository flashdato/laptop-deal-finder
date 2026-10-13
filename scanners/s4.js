const {open}=require('./lib');
(async()=>{ const {b,p}=await open();
 for(const u of ['https://alta.ge/notebooks.html?page=2','https://ee.ge/en/laptops-c58s?page=2']){
 await p.goto(u,{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(6000);
 console.log(u, await p.evaluate(()=>({h2:document.querySelectorAll('h2[title]').length,h2a:document.querySelectorAll('a h2').length,url:location.href, ex:[...document.querySelectorAll('h2,h3')].slice(0,5).map(h=>h.outerHTML.slice(0,200))})));}
 await b.close();})();
