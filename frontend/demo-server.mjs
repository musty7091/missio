import http from "node:http"
import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const PORT = 4173
const BACKEND_HOST = "127.0.0.1"
const BACKEND_PORT = 8000
const DIST_DIR = path.join(__dirname, "dist")

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".txt": "text/plain; charset=utf-8",
  ".webmanifest": "application/manifest+json; charset=utf-8",
}

function proxyApiRequest(req, res) {
  const proxyReq = http.request(
    {
      hostname: BACKEND_HOST,
      port: BACKEND_PORT,
      path: req.url,
      method: req.method,
      headers: {
        ...req.headers,
        host: `${BACKEND_HOST}:${BACKEND_PORT}`,
      },
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode ?? 500, proxyRes.headers)
      proxyRes.pipe(res)
    },
  )

  proxyReq.on("error", (error) => {
    res.writeHead(502, { "content-type": "application/json; charset=utf-8" })
    res.end(
      JSON.stringify({
        detail: "Backend bağlantısı kurulamadı.",
        error: error.message,
      }),
    )
  })

  req.pipe(proxyReq)
}

function serveStaticFile(req, res) {
  const requestUrl = new URL(req.url ?? "/", "http://127.0.0.1")
  let pathname = decodeURIComponent(requestUrl.pathname)

  if (pathname === "/") {
    pathname = "/index.html"
  }

  let filePath = path.normalize(path.join(DIST_DIR, pathname))

  if (!filePath.startsWith(DIST_DIR)) {
    res.writeHead(403, { "content-type": "text/plain; charset=utf-8" })
    res.end("Forbidden")
    return
  }

  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    filePath = path.join(DIST_DIR, "index.html")
  }

  const ext = path.extname(filePath).toLowerCase()
  const contentType = mimeTypes[ext] ?? "application/octet-stream"

  res.writeHead(200, {
    "content-type": contentType,
    "cache-control": ext === ".html" ? "no-store" : "public, max-age=31536000",
  })

  fs.createReadStream(filePath).pipe(res)
}

const server = http.createServer((req, res) => {
  if ((req.url ?? "").startsWith("/api/")) {
    proxyApiRequest(req, res)
    return
  }

  serveStaticFile(req, res)
})

server.listen(PORT, "0.0.0.0", () => {
  console.log(`Missio demo server hazır: http://127.0.0.1:${PORT}`)
  console.log(`API proxy: http://${BACKEND_HOST}:${BACKEND_PORT}`)
})
