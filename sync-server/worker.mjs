const path = '/api/rubrum-snapshot';
const objectKey = 'current.rubrum';
const methods = 'HEAD, GET, PUT, OPTIONS';
const maxBytes = 90 * 1024 * 1024;
const encoder = new TextEncoder();

async function digest(value) {
  return new Uint8Array(await crypto.subtle.digest('SHA-256', encoder.encode(value)));
}

async function authorized(request, key) {
  const value = request.headers.get('Authorization') ?? '';
  if (!/^[A-Za-z0-9_-]{32,256}$/.test(key ?? '') ||
      !/^Bearer [A-Za-z0-9_-]{32,256}$/.test(value)) return false;
  const [left, right] = await Promise.all([digest(value), digest('Bearer ' + key)]);
  let difference = 0;
  for (let index = 0; index < left.length; index++) difference |= left[index] ^ right[index];
  return difference === 0;
}

async function tagFor(object) {
  const hash = await digest(object.version);
  return '"' + Array.from(hash, value => value.toString(16).padStart(2, '0')).join('') + '"';
}

function responseFor(status, origin, body = null, tag) {
  const headers = new Headers({
    'Cache-Control': 'no-store',
    'Vary': 'Origin',
    'X-Content-Type-Options': 'nosniff',
    'X-Rubrum-Sync': '1'
  });
  if (origin) {
    headers.set('Access-Control-Allow-Origin', origin);
    headers.set('Access-Control-Expose-Headers', 'ETag, X-Rubrum-Sync');
  }
  if (status === 204) {
    headers.set('Access-Control-Allow-Methods', methods);
    headers.set('Access-Control-Allow-Headers', 'Authorization, Content-Type, If-Match, If-None-Match');
    headers.set('Access-Control-Max-Age', '600');
  }
  if (status === 405) headers.set('Allow', methods);
  if (tag) headers.set('ETag', tag);
  if (body) headers.set('Content-Type', 'application/octet-stream');
  return new Response(body, { status, headers });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin');
    if (origin && origin !== env.RUBRUM_ORIGIN) return responseFor(403);
    const reply = (status, body, tag) => responseFor(status, origin, body, tag);
    if (new URL(request.url).pathname !== path) return reply(404);
    if (request.method === 'OPTIONS') return origin ? reply(204) : reply(400);
    if (!['GET', 'HEAD', 'PUT'].includes(request.method)) return reply(405);
    if (!await authorized(request, env.RUBRUM_SYNC_KEY)) return reply(401);

    const bucket = env.SNAPSHOTS;
    const match = request.headers.get('If-Match');
    try {
      if (request.method === 'GET') {
        const object = await bucket.get(objectKey);
        if (!object) return reply(404);
        const tag = await tagFor(object);
        if (match !== tag) {
          await object.body.cancel();
          return reply(match ? 412 : 428);
        }
        return reply(200, object.body, tag);
      }

      const current = await bucket.head(objectKey);
      const tag = current && await tagFor(current);
      if (request.method === 'HEAD') return current ? reply(200, null, tag) : reply(404);

      const createOnly = request.headers.get('If-None-Match') === '*';
      if ((!match && !createOnly) || (match && createOnly)) return reply(428);
      if (createOnly ? current : !current || match !== tag) return reply(412);
      if (request.headers.get('Content-Type') !== 'application/octet-stream') return reply(415);
      const size = Number(request.headers.get('Content-Length'));
      if (!request.body || !Number.isSafeInteger(size) || size < 1) return reply(411);
      if (size > maxBytes) return reply(413);

      const onlyIf = current
        ? new Headers({ 'If-Match': current.httpEtag })
        : new Headers({ 'If-None-Match': '*' });
      const saved = await bucket.put(objectKey, request.body, { onlyIf });
      return saved ? reply(200, null, await tagFor(saved)) : reply(412);
    } catch {
      return reply(503);
    }
  }
};
