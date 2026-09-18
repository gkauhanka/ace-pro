import http from 'node:http';
import { readFile } from 'node:fs/promises';
import handler from './api/insights.mjs';
const root = new URL('./preview/', import.meta.url);
const server = http.createServer(async (req, res) => {
  if (req.url === '/api/insights') {
    let bytes = 0; const chunks = [];
    for await (const chunk of req) { bytes += chunk.length; if (bytes > 1024) { res.writeHead(413); res.end('Metadata exceeds 1 KB'); return; } chunks.push(chunk); }
    req.body = Buffer.concat(chunks).toString();
    res.status = code => { res.statusCode = code; return res; };
    res.json = body => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(body)); };
    return handler(req, res);
  }
  const file = ({ '/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css' })[req.url?.split('?')[0]];
  if (!file) { res.writeHead(404); return res.end('Not found'); }
  try { const data = await readFile(new URL(file, root)); res.setHeader('Content-Type', file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css' : 'text/html'); res.end(data); }
  catch { res.writeHead(500); res.end('Preview unavailable'); }
});
server.listen(8787, '0.0.0.0', () => console.log('Ace Pro: http://localhost:8787'));
