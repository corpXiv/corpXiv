export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const slug = url.pathname.slice(1).toLowerCase().replace(/\/+$/, "");

    // Root path: show directory of all links
    if (!slug) {
      const list = await env.LINKS.list();
      const rows = list.keys
        .map(
          (k) =>
            `<tr><td><code>/${k.name}</code></td><td><a href="/${k.name}">go &rarr;</a></td></tr>`
        )
        .join("");
      const html = `<!DOCTYPE html>
        <html><head><title>corpXiv Short Links</title>
        <style>
          body { font-family: "Palatino Linotype", Palatino, serif; max-width: 600px; margin: 40px auto; padding: 0 1rem; }
          h1 { font-size: 1.4em; color: #1a1a2e; }
          p { color: #666; font-size: 0.9em; }
          table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
          td { padding: 6px 12px 6px 0; border-bottom: 1px solid #eee; }
          code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
          a { color: #4a6fa5; text-decoration: none; }
          a:hover { text-decoration: underline; }
        </style></head>
        <body>
          <h1>corpXiv Short Links</h1>
          <p>${list.keys.length} links registered</p>
          <table>${rows}</table>
        </body></html>`;
      return new Response(html, { headers: { "Content-Type": "text/html" } });
    }

    // Look up the slug in KV
    const dest = await env.LINKS.get(slug);
    if (!dest) {
      return new Response("404 — shortlink not found", {
        status: 404,
        headers: { "Content-Type": "text/plain" },
      });
    }

    return Response.redirect(dest, 301);
  },
};
