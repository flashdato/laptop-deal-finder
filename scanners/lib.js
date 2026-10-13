const { chromium } = require('playwright');
exports.open = async () => {
  const exe = process.env.HOME + '/.cache/ms-playwright/chromium-1247/chrome-linux64/chrome';
  const b = await chromium.launch({ headless: true, executablePath: exe, args:['--disable-blink-features=AutomationControlled'] });
  const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', locale:'en-US' });
  return { b, ctx, p: await ctx.newPage() };
};
