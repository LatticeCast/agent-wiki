/* Blob viewer: /viewer/#<doc>/<kind>/<file>[&p=N]. Reads only from BLOB_BASE. */
(function (root) {
  "use strict";

  var IMAGE_EXT = /\.(png|jpe?g|gif|webp|svg|avif)$/i;

  function parseHash(hash) {
    var h = String(hash || "").replace(/^#/, "");
    if (!h) return null;
    var parts = h.split("&");
    var path = decodeURIComponent(parts[0]);
    var segs = path.split("/");
    if (segs.length < 3 || segs.some(function (s) { return !s || s === ".."; })) return null;
    var page = 1;
    for (var i = 1; i < parts.length; i++) {
      var m = /^p=(\d+)$/.exec(parts[i]);
      if (m) page = parseInt(m[1], 10);
    }
    return { path: path, doc: segs[0], kind: segs[1], file: segs.slice(2).join("/"), page: page };
  }

  function kindOf(ref) {
    if (ref.kind === "images" || IMAGE_EXT.test(ref.file)) return "image";
    if (ref.kind === "pdf" || /\.pdf$/i.test(ref.file)) return "pdf";
    if (ref.kind === "md" || /\.md$/i.test(ref.file)) return "md";
    return "download";
  }

  function buildUrl(base, path) {
    var b = String(base || "").replace(/\/+$/, "");
    return b + "/" + path.split("/").map(encodeURIComponent).join("/");
  }

  var api = { parseHash: parseHash, kindOf: kindOf, buildUrl: buildUrl };
  if (typeof module !== "undefined" && module.exports) { module.exports = api; return; }
  root.WikiViewer = api;

  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text) e.textContent = text;
    return e;
  }

  function loadScript(src) {
    return new Promise(function (ok, fail) {
      var s = el("script", { src: src });
      s.onload = ok; s.onerror = fail;
      document.head.appendChild(s);
    });
  }

  async function renderPdf(box, url, page) {
    var pdfjs = await import("/assets/vendor/pdf.min.mjs");
    pdfjs.GlobalWorkerOptions.workerSrc = "/assets/vendor/pdf.worker.min.mjs";
    var doc = await pdfjs.getDocument(url).promise;
    var n = Math.min(Math.max(page, 1), doc.numPages);
    var pg = await doc.getPage(n);
    var vp = pg.getViewport({ scale: 1.4 });
    var canvas = el("canvas", {});
    canvas.width = vp.width; canvas.height = vp.height;
    box.appendChild(canvas);
    await pg.render({ canvasContext: canvas.getContext("2d"), viewport: vp }).promise;
    box.appendChild(el("p", {}, "Page " + n + " / " + doc.numPages));
  }

  async function renderMd(box, url) {
    var res = await fetch(url);
    if (!res.ok) throw new Error("HTTP " + res.status);
    await loadScript("/assets/vendor/marked.min.js");
    var div = el("div", { "class": "viewer-md" });
    div.innerHTML = root.marked.parse(await res.text());
    box.appendChild(div);
  }

  async function main() {
    var box = document.getElementById("viewer");
    if (!box) return;
    var base = box.getAttribute("data-blob-base");
    var ref = parseHash(root.location.hash);
    box.textContent = "";
    if (!ref) { box.textContent = "Open a reference as /viewer/#<doc>/<kind>/<file>."; return; }
    var url = buildUrl(base, ref.path);
    try {
      switch (kindOf(ref)) {
        case "image": box.appendChild(el("img", { src: url, alt: ref.file, style: "max-width:100%" })); break;
        case "pdf": await renderPdf(box, url, ref.page); break;
        case "md": await renderMd(box, url); break;
        default: box.appendChild(el("a", { href: url, download: ref.file }, "Download " + ref.file));
      }
    } catch (e) {
      box.textContent = "Cannot load " + ref.path + ": " + e.message;
    }
  }

  root.addEventListener("hashchange", main);
  root.addEventListener("DOMContentLoaded", main);
})(typeof window !== "undefined" ? window : globalThis);
