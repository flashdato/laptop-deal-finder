const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open();
 const qs=['ლეპტოპი','ნოუთბუქი','ნოუთბუკი','ლაპტოპი','laptop','notebook','ноутбук','thinkpad','macbook','lenovo','asus','acer','dell','hp ','ნაწილებად','ლეპტოპის'];
 const items={};
 for(const q of qs){ for(let pg=1;pg<=10;pg++){
  await p.goto('https://ss.ge/en/sales/list?Query='+encodeURIComponent(q)+'&Page='+pg,{waitUntil:'domcontentloaded',timeout:60000});
  const got=await p.evaluate(()=>[...document.querySelectorAll('.latest_article_each[data-id]')].map(e=>({id:e.dataset.id,href:e.querySelector('a[href*="/sales/details/"]')?.href,price:e.querySelector('.latest_price')?.innerText.trim(),title:e.querySelector('.item-title')?.innerText.trim(),loc:e.querySelector('.time-loaction span')?.innerText.replace(/-\s*$/,'').trim(),date:e.querySelectorAll('.time-loaction span')[1]?.innerText.trim(),descr:e.querySelector('.DescripTionListB')?.innerText.trim()})));
  got.forEach(g=>{ items[g.id]=items[g.id]||{...g,q:[]}; items[g.id].q.push(q);});
  console.log(q,pg,got.length); if(got.length<20) break; } }
 console.log('unique',Object.keys(items).length);
 for(const it of Object.values(items)){ if(!it.href) continue;
  try{ await p.goto(it.href,{waitUntil:'domcontentloaded',timeout:60000});
   it.detail=await p.evaluate(()=>{ const t=document.body.innerText; return t.slice(0,6000);});
   it.tels=await p.evaluate(()=>[...document.querySelectorAll('a[href^="tel:"]')].map(a=>a.getAttribute('href')).filter(h=>!h.includes('0322121661')));
   it.user=await p.evaluate(()=>{const e=document.querySelector('[class*=author],[class*=user-name],[class*=userName],[class*=UserName]'); return e?e.innerText.trim().slice(0,80):'';});
  }catch(e){it.err=e.message}
 }
 fs.writeFileSync('ss_all.json',JSON.stringify(Object.values(items),null,1));
 await b.close();})();
