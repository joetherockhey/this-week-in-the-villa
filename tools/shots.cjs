// One example picture per trend -> img/<n>.jpg, and data/shots.json saying which post it shows.
// Uses the platforms' public embed pages (no login): tiktok.com/embed/v2/<id>, instagram.com/p/<code>/embed.
// Trends with no capturable example are left out of shots.json; tools/ai_images.py fills those.
// Usage: node tools/shots.cjs [n,n,...]
const fs = require('fs'), path = require('path');
const { chromium } = require(process.env.APPDATA + '/npm/node_modules/@playwright/cli/node_modules/playwright-core');
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36';
const ROOT = path.resolve(__dirname, '..');
const trends = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/trends.json'), 'utf8'));
const only = process.argv[2] ? process.argv[2].split(',').map(Number) : null;
const shotsFile = path.join(ROOT, 'data/shots.json');
const shots = fs.existsSync(shotsFile) ? JSON.parse(fs.readFileSync(shotsFile, 'utf8')) : {};
fs.mkdirSync(path.join(ROOT, 'img'), { recursive: true });

function embedUrl(u) {
  let m = u.match(/tiktok\.com\/@[^/]+\/video\/(\d+)/);
  if (m) return 'https://www.tiktok.com/embed/v2/' + m[1];
  m = u.match(/instagram\.com\/(?:p|reel|reels)\/([\w-]+)/);
  if (m && !/\/audio\//.test(u)) return `https://www.instagram.com/p/${m[1]}/embed/`;
  return null;
}

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', args: ['--mute-audio', '--autoplay-policy=user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 420, height: 900 }, deviceScaleFactor: 2,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36' });
  for (const [i, t] of trends.entries()) {
    const n = i + 1, out = path.join(ROOT, `img/${n}.jpg`);
    if (only ? !only.includes(n) : shots[n]) continue;
    delete shots[n];
    for (const u of t.examples.map(x => x.url || x)) {
      if (/tiktok\.com\/@[^/]+\/video\//.test(u)) {  // the video page ships its cover frame in the HTML
        try {
          const html = await (await fetch(u, { headers: { 'User-Agent': UA } })).text();
          const m = html.match(/"cover":"(https:[^"]+)"/);
          if (m) {
            const img = Buffer.from(await (await fetch(JSON.parse(`"${m[1]}"`))).arrayBuffer());
            if (img.length > 15000) { fs.writeFileSync(out, img); shots[n] = { kind: 'example', url: u }; break; }
          }
        } catch (err) { console.log(n, 'cover fail', u, err.message); }
      }
      if (/instagram\.com\/(p|reels?)\/[\w-]+/.test(u)) {  // the embed loads a clean cover; og:image has a play button baked in
        const page = await ctx.newPage();
        try {
          await page.goto(embedUrl(u), { waitUntil: 'domcontentloaded', timeout: 30000 });
          await page.waitForTimeout(5000);
          const src = await page.evaluate(() => [...document.images].sort((a, b) => b.naturalWidth * b.naturalHeight - a.naturalWidth * a.naturalHeight)[0]?.currentSrc);
          const img = src && Buffer.from(await (await fetch(src)).arrayBuffer());
          if (img && img.length > 15000) { fs.writeFileSync(out, img); shots[n] = { kind: 'example', url: u }; }
        } catch (err) { console.log(n, 'embed cover fail', u, err.message.split('\n')[0]); }
        await page.close();
        if (shots[n]) break;
      }
      const e = embedUrl(u);
      if (!e) continue;
      const page = await ctx.newPage();
      try {
        await page.goto(e, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(6000);
        // crop to the post card; IG embeds sit in .EmbeddedMedia / body, TikTok in the main player
        const box = await page.evaluate(() => {
          const el = document.querySelector('.Embed, [class*=DivVideoContainer], [class*=player], video, img.EmbeddedMediaImage') || document.body;
          const r = (el.closest('.Embed') || el).getBoundingClientRect();
          return { x: r.x, y: r.y, width: Math.min(r.width, 420), height: Math.min(r.height, 900) };
        });
        if (box.width < 100 || box.height < 200) throw new Error('nothing rendered');
        await page.screenshot({ path: out, type: 'jpeg', quality: 85, clip: box });
        if (fs.statSync(out).size < 25000) throw new Error('blank capture');
        shots[n] = { kind: 'example', url: u };
      } catch (err) { console.log(n, 'fail', u, err.message.split('\n')[0]); }
      await page.close();
      if (shots[n]) break;
    }
    console.log(n, shots[n] ? 'ok' : 'NONE', t.name);
  }
  fs.writeFileSync(shotsFile, JSON.stringify(shots, null, 1));
  await browser.close();
})();
