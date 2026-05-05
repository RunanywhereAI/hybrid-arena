# Cloud-only run — 03-url-shortener

Run at: 2026-04-29T03:04:47.650Z

## Setup

- model: `gpt-5.5-2026-04-23` (single-shot via `router/always-cloud`)
- elapsed: **57.5s**
- prompt tokens: 465
- completion tokens: 4120 (of which reasoning: 2048)
- cost: **$0.1259** (in $0.00233 + out $0.1236)

## Prompt

```
Design and implement a rate-limited URL shortener service in Node + Express.

Functional requirements:
- `POST /shorten` with body `{url}` returns `{code, shortUrl}` where `shortUrl` is `http://localhost:3000/<code>`
- `GET /:code` issues a 302 redirect to the original URL, or 404 if the code is unknown
- Rate limit: 100 requests per 15 minutes per IP, applied to `POST /shorten` only (other routes unlimited). Return 429 with a JSON body when exceeded.
- Input validation on POST: the url must parse with `new URL()` AND start with `http://` or `https://`. Return 400 otherwise.
- Codes: 6-character base62 (`A-Za-z0-9`). On collision, regenerate (max 5 retries, then 500).
- In-memory storage — a single `Map<code, originalUrl>` is fine for the demo.

Files to produce:
- `package.json` (express dep, `start: "node server.js"`)
- `server.js` — wires everything together
- `urlStore.js` — store with `set/get/has` and the collision-aware code generator
- `rateLimiter.js` — middleware factory `rateLimiter({windowMs, max})`. Implement a simple fixed-window counter per IP using a `Map` and `setInterval` to clear it.
- `server.test.js` — one happy-path test (`node:test` + `fetch` against an ephemeral-port server): POST a valid URL, follow the GET redirect, expect the original URL back.
- `README.md` — must include three short sections:
  1. **Data model** — why a single `Map<code, url>` and what changes for production.
  2. **Rate-limiting choice** — fixed-window counter vs token bucket: trade-off, why fixed-window for this demo.
  3. **Production checklist** — what to swap for a real deployment (db, distributed rate limiter, code-collision strategy at scale, redirect caching, monitoring).

Output every file with a `=== FILE: <path> ===` header followed by its full content.
```

## Output

=== FILE: package.json ===
```json
{
  "name": "rate-limited-url-shortener",
  "version": "1.0.0",
  "description": "Demo rate-limited URL shortener built with Node and Express",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "test": "node --test"
  },
  "dependencies": {
    "express": "^4.18.3"
  },
  "engines": {
    "node": ">=18"
  }
}
```

=== FILE: server.js ===
```js
const express = require('express');
const { UrlStore } = require('./urlStore');
const { rateLimiter } = require('./rateLimiter');

const DEFAULT_PORT = 3000;
const SHORT_URL_BASE = 'http://localhost:3000';

function isValidHttpUrl(value) {
  if (typeof value !== 'string') {
    return false;
  }

  if (!value.startsWith('http://') && !value.startsWith('https://')) {
    return false;
  }

  try {
    const parsed = new URL(value);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

function createApp() {
  const app = express();
  const store = new UrlStore();

  const shortenRateLimit = rateLimiter({
    windowMs: 15 * 60 * 1000,
    max: 100
  });

  app.use(express.json());

  app.post('/shorten', shortenRateLimit, (req, res) => {
    const { url } = req.body || {};

    if (!isValidHttpUrl(url)) {
      return res.status(400).json({
        error: 'Invalid url. Expected an absolute http:// or https:// URL.'
      });
    }

    try {
      const code = store.create(url);

      return res.json({
        code,
        shortUrl: `${SHORT_URL_BASE}/${code}`
      });
    } catch {
      return res.status(500).json({
        error: 'Could not generate a unique short code.'
      });
    }
  });

  app.get('/:code', (req, res) => {
    const { code } = req.params;

    if (!store.has(code)) {
      return res.status(404).json({
        error: 'Unknown short code.'
      });
    }

    return res.redirect(302, store.get(code));
  });

  return app;
}

if (require.main === module) {
  const app = createApp();
  const port = process.env.PORT || DEFAULT_PORT;

  app.listen(port, () => {
    console.log(`URL shortener listening at http://localhost:${port}`);
  });
}

module.exports = {
  createApp,
  isValidHttpUrl
};
```

=== FILE: urlStore.js ===
```js
const crypto = require('node:crypto');

const BASE62 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
const DEFAULT_CODE_LENGTH = 6;
const DEFAULT_MAX_RETRIES = 5;

function randomBase62Code(length = DEFAULT_CODE_LENGTH) {
  let code = '';

  for (let i = 0; i < length; i += 1) {
    code += BASE62[crypto.randomInt(BASE62.length)];
  }

  return code;
}

class UrlStore {
  constructor() {
    this.urls = new Map();
  }

  set(code, originalUrl) {
    this.urls.set(code, originalUrl);
  }

  get(code) {
    return this.urls.get(code);
  }

  has(code) {
    return this.urls.has(code);
  }

  generateCode({
    length = DEFAULT_CODE_LENGTH,
    maxRetries = DEFAULT_MAX_RETRIES
  } = {}) {
    for (let retry = 0; retry <= maxRetries; retry += 1) {
      const code = randomBase62Code(length);

      if (!this.has(code)) {
        return code;
      }
    }

    throw new Error('Exceeded maximum retries while generating a unique code.');
  }

  create(originalUrl) {
    const code = this.generateCode();
    this.set(code, originalUrl);
    return code;
  }
}

module.exports = {
  UrlStore,
  randomBase62Code,
  BASE62
};
```

=== FILE: rateLimiter.js ===
```js
function rateLimiter({ windowMs, max }) {
  if (!Number.isFinite(windowMs) || windowMs <= 0) {
    throw new Error('rateLimiter requires a positive windowMs value.');
  }

  if (!Number.isInteger(max) || max <= 0) {
    throw new Error('rateLimiter requires a positive integer max value.');
  }

  const counters = new Map();

  const interval = setInterval(() => {
    counters.clear();
  }, windowMs);

  if (typeof interval.unref === 'function') {
    interval.unref();
  }

  return function fixedWindowRateLimiter(req, res, next) {
    const ip = req.ip || req.socket.remoteAddress || 'unknown';
    const count = (counters.get(ip) || 0) + 1;

    counters.set(ip, count);

    if (count > max) {
      return res.status(429).json({
        error: 'Too many requests. Please try again later.'
      });
    }

    return next();
  };
}

module.exports = {
  rateLimiter
};
```

=== FILE: server.test.js ===
```js
const http = require('node:http');
const test = require('node:test');
const assert = require('node:assert/strict');
const { createApp } = require('./server');

function listen(server) {
  return new Promise((resolve, reject) => {
    server.once('error', reject);

    server.listen(0, () => {
      server.off('error', reject);
      resolve(server.address().port);
    });
  });
}

function close(server) {
  return new Promise((resolve, reject) => {
    server.close((err) => {
      if (err) {
        reject(err);
        return;
      }

      resolve();
    });
  });
}

test('POST /shorten creates a code and GET /:code redirects to the original URL', async (t) => {
  const targetServer = http.createServer((req, res) => {
    res.writeHead(200, {
      'content-type': 'text/plain'
    });
    res.end(`reached ${req.url}`);
  });

  const targetPort = await listen(targetServer);
  t.after(() => close(targetServer));

  const originalUrl = `http://127.0.0.1:${targetPort}/destination?x=1`;

  const app = createApp();
  const shortenerServer = http.createServer(app);
  const shortenerPort = await listen(shortenerServer);
  t.after(() => close(shortenerServer));

  const shortenResponse = await fetch(`http://127.0.0.1:${shortenerPort}/shorten`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json'
    },
    body: JSON.stringify({
      url: originalUrl
    })
  });

  assert.equal(shortenResponse.status, 200);

  const body = await shortenResponse.json();

  assert.match(body.code, /^[A-Za-z0-9]{6}$/);
  assert.equal(body.shortUrl, `http://localhost:3000/${body.code}`);

  const redirectResponse = await fetch(`http://127.0.0.1:${shortenerPort}/${body.code}`);

  assert.equal(redirectResponse.status, 200);
  assert.equal(redirectResponse.url, originalUrl);
  assert.equal(await redirectResponse.text(), 'reached /destination?x=1');
});
```

=== FILE: README.md ===
```md
# Rate-limited URL shortener

A small Node + Express demo service.

## Data model

This demo uses one in-memory `Map<code, url>`, where the 6-character short code is the key and the original URL is the value. That is enough for a single-process demo because lookups are fast, writes are simple, and no persistence is required.

For production, this should move to durable storage such as PostgreSQL, MySQL, DynamoDB, Redis with persistence, or another database. The production schema would typically include the short code, original URL, creation time, owner/user metadata, expiration time, click counters, and indexes/constraints to enforce code uniqueness.

## Rate-limiting choice

The service uses a simple fixed-window counter per IP for `POST /shorten`: each IP can make 100 shorten requests per 15-minute window, and all counters are cleared on an interval.

A fixed-window limiter is easy to implement and understand, but it can allow bursts around window boundaries. A token bucket or leaky bucket handles bursts more smoothly and provides better traffic shaping. Fixed-window is used here because it is small, dependency-free, and sufficient for a demo.

## Production checklist

For a real deployment, swap or add:

- Persistent database instead of an in-memory `Map`.
- Distributed rate limiter backed by Redis or another shared store so limits work across multiple app instances.
- Stronger code-collision strategy at scale, such as database uniqueness constraints, retry-on-conflict writes, preallocated code ranges, or longer codes.
- Redirect caching with appropriate HTTP cache headers and/or CDN support.
- Monitoring and alerting for request rates, error rates, latency, collision frequency, rate-limit events, and storage health.
- Structured logging and request IDs.
- Abuse prevention, URL safety checks, malware/phishing scanning, and admin takedown tooling.
- Production configuration for `trust proxy` if deployed behind a load balancer, so IP-based rate limiting uses the correct client IP.
```
