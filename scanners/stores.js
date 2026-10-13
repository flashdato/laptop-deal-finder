const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open(); const out=[];
 await p.goto('https://zoommer.ge/leptopebi-c531',{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(2000);
 for(let pg=1;pg<=20;pg++){ const d=await p.evaluate(async(pg)=>{const r=await fetch('/api/proxy/v1/Products/v3?CategoryId=531&Page='+pg+'&Limit=100');return await r.json()},pg).catch(e=>null);
   const ps=d?.products||[]; ps.forEach(x=>out.push({store:'Zoommer',name:x.name,price:x.price,url:'https://zoommer.ge/'+(x.route||x.urlName||'')})); console.log('z',pg,ps.length); if(ps.length<100)break; }
 await p.goto('https://ee.ge/en/laptops-c58s',{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(2000);
 for(let pg=1;pg<=20;pg++){ const d=await p.evaluate(async(pg)=>{const r=await fetch('https://ee-api.ee.ge/v1/Products/v3?CategoryId=58&Limit=100&Page='+pg);return await r.json()},pg).catch(e=>null);
   const ps=d?.products||[]; ps.forEach(x=>out.push({store:'EE',name:x.name,price:x.price,url:'https://ee.ge/en/'+(x.route||x.urlName||'')})); console.log('ee',pg,ps.length); if(ps.length<100)break; }
 await p.goto('https://alta.ge/notebooks.html?product_list_limit=100',{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(3000);
 for(let pg=1;pg<=8;pg++){ if(pg>1){await p.goto('https://alta.ge/notebooks.html?product_list_limit=100&p='+pg,{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(2500);}
   const ps=await p.evaluate(()=>[...document.querySelectorAll('.product-item, li.item.product')].map(e=>({name:e.querySelector('.product-item-link, .product-item-name a')?.innerText.trim(),url:e.querySelector('a')?.href,price:(e.querySelector('[data-price-amount]')?.getAttribute('data-price-amount'))})).filter(x=>x.name));
   ps.forEach(x=>out.push({store:'Alta',...x,price:+x.price})); console.log('alta',pg,ps.length); if(ps.length<20)break; }
 fs.writeFileSync('stores.json',JSON.stringify(out)); console.log('total',out.length, JSON.stringify(out.slice(0,2)));
 await b.close();})();
