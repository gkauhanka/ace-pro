import { chromium } from 'playwright';
import { mkdir, copyFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const baseURL = process.env.ACE_PREVIEW_URL || 'http://localhost:8787';
const videoFixture = process.env.ACE_VIDEO_FIXTURE || path.join(here, 'fixtures/court-demo.mp4');
const output = path.join(here, 'raw');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  ...(process.platform === 'darwin' ? { executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' } : {})
});
const context = await browser.newContext({
  viewport: { width: 430, height: 932 }, deviceScaleFactor: 1,
  isMobile: true, hasTouch: true, colorScheme: 'light', reducedMotion: 'no-preference',
  recordVideo: { dir: output, size: { width: 430, height: 932 } }
});
const page = await context.newPage();
const requests = [];
page.on('request', request => {
  if (request.url().endsWith('/api/insights')) requests.push(JSON.parse(request.postData()));
});
const errors = [];
page.on('pageerror', error => errors.push(error.message));
const pause = ms => page.waitForTimeout(ms);
const click = action => page.locator(`[data-action="${action}"]`).click();
const top = () => page.locator('.content').evaluate(el => el.scrollTo({ top: 0, behavior: 'smooth' }));
const scrollTo = selector => page.locator(selector).first().evaluate(el => el.scrollIntoView({ behavior: 'smooth', block: 'center' }));

try {
  await page.goto(baseURL, { waitUntil: 'networkidle' });
  await pause(1600);
  await click('signup');
  await page.locator('#name').fill('Alex');
  await page.locator('#email').fill('alex@example.test');
  await page.locator('#password').fill('DemoOnly-Ace2026!');
  await pause(1400);
  await page.locator('#auth-form button[type="submit"]').click();
  await page.getByText('Good to see you, Alex.').waitFor();
  await pause(1800);
  await click('add');
  await page.locator('#video-file').setInputFiles(videoFixture);
  await page.locator('#session-title').fill('Sunday practice');
  await page.locator('#session-type').selectOption('Practice');
  await page.locator('#focus').selectOption('Footwork');
  await pause(1900);
  await page.locator('#import-form button[type="submit"]').click();
  await page.locator('[data-action="insight"]').first().waitFor({timeout:35000});
  await pause(2400);
  await page.locator('[data-action="insight"][data-key="split-step"]').click();
  await pause(2000);
  await click('save-drill');
  await pause(1200);
  await scrollTo('.moment');
  await pause(1500);
  await page.locator('.moment').nth(1).click();
  await page.locator('video').waitFor();
  await pause(2600);
  await page.screenshot({path:path.join(output,'playback.png')});
  await click('close');
  await scrollTo('#note');
  await page.locator('#note').fill('Next practice: land the split step as my partner makes contact.');
  await click('save-note');
  await pause(1300);
  await click('improve');
  await pause(2300);
  await click('library');
  await pause(1500);
  await click('add');
  await page.locator('#video-file').setInputFiles(videoFixture);
  await page.locator('#session-title').fill('Tuesday match review');
  await page.locator('#session-type').selectOption('Match');
  await page.locator('#focus').selectOption('Footwork');
  await pause(1100);
  await page.locator('#import-form button[type="submit"]').click();
  await page.locator('[data-action="insight"]').first().waitFor({timeout:35000});
  await page.locator('[data-action="insight"][data-key="split-step"]').click();
  await scrollTo('.section-head');
  await pause(1200);
  await page.locator('.content').evaluate(el => el.scrollBy({top:280,behavior:'smooth'}));
  await pause(2400);
  await page.screenshot({path:path.join(output,'cross-video.png')});
  await click('home');
  await top();
  await pause(2200);
  await page.screenshot({path:path.join(root,'docs/media/ace-pro-poster.png')});
  if (errors.length) throw new Error('Browser errors: '+errors.join('; '));
  if (requests.length !== 2 || requests.some(body => Object.keys(body).sort().join(',') !== 'durationSeconds,focus,sessionType')) throw new Error('Unexpected network payload: '+JSON.stringify(requests));
  await writeFile(path.join(output,'verification.json'), JSON.stringify({apiCalls:requests.length,requestFields:['durationSeconds','focus','sessionType'],consoleErrors:errors,flows:['signup','local MP4 import','simulated processing','report','save drill','timestamp playback','save note','practice plan','second session','cross-video moments']},null,2));
} finally {
  await context.close();
  const recording = await page.video().path();
  await copyFile(recording, path.join(output, 'walkthrough.webm'));
  await browser.close();
}
console.log('Recorded walkthrough in '+output);
