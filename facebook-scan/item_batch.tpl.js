async (page) => {
  const ids = __IDS__;
  const out = [];
  for (const id of ids) {
    try {
      await page.goto('https://www.facebook.com/marketplace/item/'+id+'/');
      await page.waitForTimeout(2500);
      const sm = page.getByRole('button', {name: 'See more'}).first();
      if (await sm.count()) { try { await sm.click({timeout:1500}); await page.waitForTimeout(400);} catch(e){} }
      const r = await page.evaluate(() => {
        const main = document.querySelector('[role=main]') || document.body;
        const prof = [...main.querySelectorAll('a[href*="/marketplace/profile/"]')];
        const named = prof.find(a => a.innerText.trim() && a.innerText.trim()!=='Seller details');
        const img = [...main.querySelectorAll('img')].find(i=>i.naturalWidth>300 && i.src.includes('fbcdn'));
        let t = main.innerText;
        const cut = t.search(/\nSeller information|\nAds\n|Location is approximate/);
        if (cut>0) t = t.slice(0,cut);
        return {seller: named?named.innerText.trim():'', profile: prof[0]?prof[0].href.split('?')[0]:'', img: img?img.src:'', text: t.slice(0,1800), gone: /no longer available|isn.t available/i.test(document.body.innerText.slice(0,3000)) && !prof.length};
      });
      out.push({id, ...r});
    } catch (e) { out.push({id, err: String(e).slice(0,100)}); }
  }
  await fetch('http://127.0.0.1:8765/__NAME__', {method:'POST', body: JSON.stringify(out)});
  return out.length + ' saved to __NAME__';
}
