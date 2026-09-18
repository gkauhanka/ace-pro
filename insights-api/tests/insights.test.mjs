import { test } from 'node:test';
import assert from 'node:assert/strict';
import { generateInsights } from '../api/insights.mjs';
test('reports disclose simulation and moments stay within short and long videos', () => {
  for (const durationSeconds of [1, 1.5, 60, 21600]) {
    const r = generateInsights({ durationSeconds, sessionType: 'Practice', focus: 'Serve' });
    assert.equal(r.simulated, true); assert.equal(r.insights.length, 3); assert.equal(r.insights[0].category, 'Serve');
    for (const i of r.insights) { assert.ok(i.value >= 0 && i.value <= 100); assert.ok(i.youtubeURL.startsWith('https://www.youtube.com/')); for (const m of i.moments) assert.ok(m.seconds >= 0 && m.seconds < durationSeconds); }
  }
});
test('rejects video, personal data and invalid requests', () => {
  const valid = { durationSeconds: 30, sessionType: 'Match', focus: 'All-round' };
  for (const input of [null, [], 'video', 42, {...valid, video: 'bytes'}, {...valid, email: 'me@example.com'}, {...valid, durationSeconds: 0}, {...valid, durationSeconds: NaN}, {...valid, sessionType: 'bad'}, {...valid, focus: 'bad'}]) assert.throws(() => generateInsights(input));
});

import handler from '../api/insights.mjs';
function response() { return { headers: {}, setHeader(k,v) { this.headers[k]=v; }, status(code) { this.code=code; return this; }, json(body) { this.body=body; return this; } }; }
test('HTTP contract rejects non-JSON bodies, non-POST methods, oversized and malformed data', async () => {
  for (const [req, status] of [
    [{method:'GET',headers:{}},405],
    [{method:'POST',headers:{'content-type':'video/mp4'},body:'video'},415],
    [{method:'POST',headers:{'content-type':'application/jsonx'},body:'{}'},415],
    [{method:'POST',headers:{'content-type':'application/json'},body:'{'},400],
    [{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({large:'a'.repeat(1100)})},413],
    [{method:'POST',headers:{'content-type':'application/json'},body:'null'},400]
  ]) { const res=response(); await handler(req,res); assert.equal(res.code,status); assert.equal(res.headers['Cache-Control'],'no-store'); }
});
test('HTTP handler returns a complete report from only the three metadata fields', async () => {
 const res=response(); await handler({method:'POST',headers:{'content-type':'application/json'},body:{durationSeconds:90,sessionType:'Match',focus:'Technique'}},res);
 assert.equal(res.code,200);assert.equal(res.body.insights[0].key,'contact');assert.equal(res.body.simulated,true);
});
