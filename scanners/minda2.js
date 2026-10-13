const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open();
 await p.goto('https://minda.city/en/elektro/computers.html',{waitUntil:'domcontentloaded',timeout:60000});
 await p.waitForTimeout(3000);
 const cats=await p.evaluate(()=>[...document.querySelectorAll('a')].filter(a=>/Laptops|Apple Mac/.test(a.innerText)).map(a=>a.href));
 console.log(cats);
 const links=new Set();
 for(const c of [...new Set(cats)]){ for(let pg=1;pg<=4;pg++){ const u=c+(pg>1?(c.includes('?')?'&':'?')+'page='+pg:'');
   await p.goto(u,{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(2000);
   const ls=await p.evaluate(()=>[...document.querySelectorAll('a')].map(a=>a.href).filter(h=>/minda\.city\/.*\d{4,}.*\.html|\/ad\/|item/.test(h)));
   const before=links.size; ls.forEach(l=>links.add(l)); console.log(u,ls.length,links.size); if(links.size==before) break; } }
 const out=[];
 for(const l of links){ try{ await p.goto(l,{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(1200);
   out.push(await p.evaluate(()=>({url:location.href,title:document.querySelector('h1')?.innerText.trim(),text:document.body.innerText.slice(0,5000),tels:[...document.querySelectorAll('a[href^="tel:"],a[href*="wa.me"],a[href*="t.me"]')].map(a=>a.getAttribute('href')),img:document.querySelector('meta[property="og:image"]')?.content||''})));
 }catch(e){} }
 fs.writeFileSync('minda_all.json',JSON.stringify(out,null,1)); console.log('items',out.length);
 await b.close();})();
