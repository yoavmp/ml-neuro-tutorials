// Minimal static file server for end-to-end tests. No dependencies.
//
// Serves the repository's book/_static/widgets/ directory (built Vite app under
// app/, plus configs/ and data/) over real HTTP. The same content is reachable
// two ways so tests can prove the assets survive the GitHub Pages repo subpath:
//
//   http://localhost:PORT/app/index.html                     (site root)
//   http://localhost:PORT/ml-neuro-tutorials/app/index.html   (project subpath)
//
// A leading /ml-neuro-tutorials segment is simply stripped before resolving.

import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const here = fileURLToPath(new URL(".", import.meta.url));
const ROOT = resolve(here, "..", "..", "book", "_static", "widgets");
const PORT = Number(process.env.PORT ?? "4173");
const SUBPATH = "/ml-neuro-tutorials";

const TYPES = new Map([
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".mjs", "text/javascript; charset=utf-8"],
  [".css", "text/css; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".map", "application/json; charset=utf-8"],
  [".svg", "image/svg+xml"],
  [".png", "image/png"],
  [".ico", "image/x-icon"],
]);

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url ?? "/", `http://localhost:${PORT}`);
    let pathname = decodeURIComponent(url.pathname);
    if (pathname === SUBPATH || pathname.startsWith(SUBPATH + "/")) {
      pathname = pathname.slice(SUBPATH.length) || "/";
    }
    if (pathname === "/") pathname = "/app/index.html";

    // Contain the resolved path inside ROOT.
    const target = normalize(join(ROOT, pathname));
    if (target !== ROOT && !target.startsWith(ROOT + sep)) {
      res.writeHead(403).end("Forbidden");
      return;
    }

    let filePath = target;
    const info = await stat(filePath).catch(() => null);
    if (info?.isDirectory()) filePath = join(filePath, "index.html");

    const body = await readFile(filePath);
    const type = TYPES.get(extname(filePath)) ?? "application/octet-stream";
    res.writeHead(200, {
      "content-type": type,
      "cache-control": "no-store",
      "access-control-allow-origin": "http://localhost:" + PORT,
    });
    res.end(body);
  } catch {
    res.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    res.end("Not found");
  }
});

server.listen(PORT, () => {
  process.stdout.write(`serve-static: http://localhost:${PORT}/ (root ${ROOT})\n`);
});
