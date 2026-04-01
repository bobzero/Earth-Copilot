// Static file server + API reverse proxy for Azure App Service
// Serves the Vite-built frontend with SPA fallback to index.html
// Proxies /api/* requests to the backend Container App
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = process.env.PORT || 8080;
const ROOT = __dirname;

// Backend URL from App Service environment variable
// Set via Bicep or az webapp config: VITE_API_BASE_URL=https://ca-web-xxx.azurecontainerapps.io
const BACKEND_URL = process.env.BACKEND_URL || process.env.VITE_API_BASE_URL || '';

if (BACKEND_URL) {
  console.log(`API proxy enabled: /api/* -> ${BACKEND_URL}`);
} else {
  console.warn('WARNING: No BACKEND_URL or VITE_API_BASE_URL set. API proxy disabled.');
}

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.md': 'text/markdown',
};

// Reverse proxy handler for /api/* requests
function proxyRequest(req, res) {
  const targetUrl = BACKEND_URL + req.url;
  const parsed = url.parse(targetUrl);
  const transport = parsed.protocol === 'https:' ? https : http;

  const proxyReq = transport.request(
    {
      hostname: parsed.hostname,
      port: parsed.port,
      path: parsed.path,
      method: req.method,
      headers: {
        ...req.headers,
        host: parsed.hostname,
      },
      timeout: 300000, // 5 min for long-running GEOINT queries
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res, { end: true });
    }
  );

  proxyReq.on('error', (err) => {
    console.error('Proxy error:', err.message);
    res.writeHead(502, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Backend unavailable', detail: err.message }));
  });

  req.pipe(proxyReq, { end: true });
}

const server = http.createServer((req, res) => {
  const pathname = req.url.split('?')[0];

  // Proxy /api/* requests to backend
  if (pathname.startsWith('/api/') && BACKEND_URL) {
    proxyRequest(req, res);
    return;
  }

  // Sanitize path to prevent directory traversal
  const safePath = path.normalize(pathname).replace(/^(\.\.[/\\])+/, '');
  let filePath = path.join(ROOT, safePath);

  // Prevent path traversal outside ROOT
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  // Try to serve the file, fall back to index.html for SPA routing
  fs.stat(filePath, (err, stats) => {
    if (!err && stats.isDirectory()) {
      filePath = path.join(filePath, 'index.html');
    }

    fs.readFile(filePath, (err, data) => {
      if (err) {
        // SPA fallback: serve index.html for any route not found
        fs.readFile(path.join(ROOT, 'index.html'), (err2, indexData) => {
          if (err2) {
            res.writeHead(500);
            res.end('Internal Server Error');
            return;
          }
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(indexData);
        });
        return;
      }

      const ext = path.extname(filePath).toLowerCase();
      const contentType = MIME_TYPES[ext] || 'application/octet-stream';

      // Cache static assets (hashed filenames), no-cache for HTML
      const cacheControl = ext === '.html' || ext === '.json'
        ? 'no-cache, no-store, must-revalidate'
        : 'public, max-age=31536000, immutable';

      res.writeHead(200, {
        'Content-Type': contentType,
        'Cache-Control': cacheControl,
      });
      res.end(data);
    });
  });
});

server.listen(PORT, () => {
  console.log(`Frontend server listening on port ${PORT}`);
});
