const { chromium } = require('playwright');
(async () => {
  const exe = process.env.HOME + '/.cache/ms-playwright/chromium-1247/chrome-linux64/chrome';
  const b = await chromium.launch({ headless: true, executablePath: require('fs').existsSync(exe)?exe:undefined, args:['--disable-blink-features=AutomationControlled'] });
  const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', locale:'en-US' });
  const p = await ctx.newPage();
  p.on('request', r => { if (r.url().includes('api')) console.log('REQ', r.method(), r.url(), (r.postData()||'').slice(0,400)); });
  p.on('response', async r => { if (r.url().includes('api2') && r.url().includes('products')) { try { const t = await r.text(); require('fs').writeFileSync(process.argv[2]+'/resp_'+Date.now()+'.json', t); console.log('RESP', r.status(), r.url(), t.length);} catch(e){} } });
  await p.goto('https://www.mymarket.ge/en/products/used/technic/computers/notebook/', { waitUntil: 'networkidle', timeout: 90000 }).catch(e=>console.log('nav', e.message));
  await p.waitForTimeout(8000);
  console.log('TITLE', await p.title());
  await b.close();
})();
