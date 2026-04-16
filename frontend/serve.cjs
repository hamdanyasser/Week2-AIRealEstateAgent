// Lightweight production server for the React build.
// Uses only Node built-in modules — no npm install needed.
// Serves static files from ./dist and proxies /predict + /health
// to the backend container (resolved via Docker Compose DNS).

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 80;
const BACKEND_HOST = process.env.BACKEND_HOST || 'backend';
const BACKEND_PORT = process.env.BACKEND_PORT || 8000;
const DIST = path.join(__dirname, 'dist');

const MIME = {
  '.html': 'text/html',
  '.js':   'application/javascript',
  '.css':  'text/css',
  '.json': 'application/json',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.woff': 'font/woff',
  '.woff2':'font/woff2',
};

function proxyToBackend(req, res) {
  const opts = {
    hostname: BACKEND_HOST,
    port: BACKEND_PORT,
    path: req.url,
    method: req.method,
    headers: req.headers,
  };
  const proxy = http.request(opts, (upstream) => {
    res.writeHead(upstream.statusCode, upstream.headers);
    upstream.pipe(res);
  });
  proxy.on('error', () => {
    res.writeHead(502, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ detail: 'Backend unavailable' }));
  });
  req.pipe(proxy);
}

function serveStatic(req, res) {
  let filePath = path.join(DIST, req.url === '/' ? 'index.html' : req.url);
  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      // SPA fallback — serve index.html for any unknown path
      filePath = path.join(DIST, 'index.html');
    }
    const ext = path.extname(filePath);
    const mime = MIME[ext] || 'application/octet-stream';
    fs.readFile(filePath, (readErr, data) => {
      if (readErr) {
        res.writeHead(500);
        res.end('Internal error');
        return;
      }
      res.writeHead(200, { 'Content-Type': mime });
      res.end(data);
    });
  });
}

http.createServer((req, res) => {
  if (req.url.startsWith('/predict') || req.url.startsWith('/health')) {
    proxyToBackend(req, res);
  } else {
    serveStatic(req, res);
  }
}).listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend serving on :${PORT}, proxying API to ${BACKEND_HOST}:${BACKEND_PORT}`);
});
