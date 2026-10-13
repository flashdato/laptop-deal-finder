const {open}=require('./lib'); const fs=require('fs');
(async()=>{ const {b,p}=await open();
 await p.goto('https://www.mymarket.ge/en/products/used/technic/computers/notebook/',{waitUntil:'domcontentloaded',timeout:90000});
 await p.waitForTimeout(3000);
 const ids=JSON.parse(fs.readFileSync(process.argv[2]));
 const out=fs.existsSync('mm_details.json')?JSON.parse(fs.readFileSync('mm_details.json')):{};
 for(const id of ids){ if(out[id]&&out[id].attrs) continue;
  const txt=await p.evaluate(async(id)=>{ const r=await fetch('https://api.mymarket.ge/api/en/products/'+id); return await r.text();},id).catch(e=>'');
  let d=null; try{d=JSON.parse(txt)}catch(e){}
  const ph=(txt.match(/"phone":"([^"]*)"/)||[])[1]||'';
  const pr=d?.data?.Product||d?.data?.product||null;
  if(pr){ out[id]={phone:ph,attrs:(pr.attributes||[]).map(a=>[a.AttrTitle,a.ValTitles||a.AttrValue,a.DimTitle||'']),title:pr.title,brand:pr.brand_title,model:pr.model_title,descr:pr.lang_data?.descr||pr.descr||'',raw:JSON.stringify(pr).slice(0,200)}; }
  else out[id]={err:JSON.stringify(d).slice(0,200)};
  await p.waitForTimeout(250);
 }
 fs.writeFileSync('mm_details.json',JSON.stringify(out)); console.log('details',Object.keys(out).length, Object.values(out).filter(x=>x.phone).length); await b.close();})();
