const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open(); const out=JSON.parse(fs.readFileSync('stores.json')).filter(x=>x.store=='Zoommer');
 let resp=null; p.on('response',async r=>{ if(r.url().includes('ee-api.ee.ge/v1/Products/v3')) resp=r.request().headers(); });
 await p.goto('https://ee.ge/en/laptops-c58s',{waitUntil:'networkidle',timeout:60000}); await p.waitForTimeout(2000);
 for(let pg=1;pg<=15;pg++){ const d=await p.evaluate(async([pg,h])=>{const r=await fetch('https://ee-api.ee.ge/v1/Products/v3?CategoryId=58&Limit=16&Page='+pg,{headers:h});return await r.json()},[pg,{'accept':'application/json','langcode':resp?.langcode||'en'}]).catch(e=>({e:String(e)}));
   const ps=d?.products||[]; if(!ps.length) console.log(JSON.stringify(d).slice(0,200));
   ps.forEach(x=>out.push({store:'EE',name:x.name,price:x.price,url:'https://ee.ge/en/'+(x.route||'')})); console.log('ee',pg,ps.length); if(ps.length<16)break; }
 await p.goto('https://alta.ge/notebooks.html',{waitUntil:'networkidle',timeout:60000}).catch(()=>{}); await p.waitForTimeout(3000);
 console.log((await p.evaluate(()=>document.body.innerText)).slice(0,1500));
 const ex=await p.evaluate(()=>{const a=[...document.querySelectorAll('a')].find(a=>/ThinkPad|Victus|Katana|Strix/i.test(a.innerText)); return a?a.closest('div,li').outerHTML.slice(0,800):'none'}); console.log(ex);
 fs.writeFileSync('stores.json',JSON.stringify(out)); console.log('total',out.length);
 await b.close();})();
