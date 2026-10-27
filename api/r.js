// Same-origin proxy to the relay (Vercel edge). Board and coin answers are cached for 2 s at the CDN, so the free
// relay sees a few requests a second however many people are watching. Uploads and launches go to the relay directly.
export const config = { runtime: 'edge' }
const RELAY = 'https://vetted-relay.vetted-relay.workers.dev/v1/'
const TTL = { board: 5, coin: 4, vamp: 3, rep: 300 }
export default async function handler(req) {
  const u = new URL(req.url), path = u.searchParams.get('path')
  if (!TTL[path]) return new Response('{"error":"unknown"}', { status: 404, headers: { 'content-type': 'application/json' } })
  u.searchParams.delete('path')
  const r = await fetch(RELAY + path + '?' + u.searchParams.toString(), { cache: 'no-store' })
  return new Response(r.body, { status: r.status, headers: { 'content-type': 'application/json', 'cache-control': `public, s-maxage=${TTL[path]}, stale-while-revalidate=${TTL[path] * 2}` } })
}
