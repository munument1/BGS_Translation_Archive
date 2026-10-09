#!/usr/bin/env node
"use strict";
/**
 * Offline EPUB chapter extractor for a source that the user may lawfully use.
 * Usage: node tools/extract_eso_epub_local.cjs --epub /path/to/ESO.epub
 *
 * Reads book chapters from a USER-PROVIDED EPUB. Never downloads websites.
 * Writes English reference text ONLY into work/ (ignored by Git). Never
 * publishes copyrighted English texts to docs/, sources/, or GitHub Pages.
 * This utility does not grant redistribution rights.
 */
const fs = require("node:fs");
const path = require("node:path");
const zlib = require("node:zlib");
const crypto = require("node:crypto");

function args(argv) {
  const a = { catalog: "docs/books/imperial_game_books_catalog.json",
    output: "work/imperial_library_originals/eso", overwrite: false };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === "--overwrite") { a.overwrite = true; continue; }
    if (!["--epub", "--catalog", "--output"].includes(k) || !argv[i + 1])
      throw Error("Unknown or missing option: " + k);
    a[k.slice(2)] = argv[++i];
  }
  if (!a.epub) throw Error("Usage: node tools/extract_eso_epub_local.cjs --epub /path/to/reference.epub");
  return a;
}
function zipFiles(file) {
  const data = fs.readFileSync(file);
  // ZIP End of Central Directory: search backwards over max comment length.
  let eocd = -1;
  for (let pos = data.length - 22; pos >= Math.max(0, data.length - 65557); --pos) {
    if (data.readUInt32LE(pos) === 0x06054b50) { eocd = pos; break; }
  }
  if (eocd < 0) throw Error("Missing ZIP end-of-directory");
  const entries = data.readUInt16LE(eocd + 10);
  let pos = data.readUInt32LE(eocd + 16);
  if (pos === 0xffffffff) throw Error("ZIP64 not supported");
  const names = new Map();
  for (let i = 0; i < entries; i++) {
    if (data.readUInt32LE(pos) !== 0x02014b50) throw Error("Bad ZIP central entry");
    const method = data.readUInt16LE(pos + 10);
    const packed = data.readUInt32LE(pos + 20);
    const unpacked = data.readUInt32LE(pos + 24);
    const nlen = data.readUInt16LE(pos + 28);
    const elen = data.readUInt16LE(pos + 30);
    const clen = data.readUInt16LE(pos + 32);
    const local = data.readUInt32LE(pos + 42);
    const name = data.subarray(pos + 46, pos + 46 + nlen).toString("utf8");
    if (name && !name.endsWith("/")) names.set(name, { method, packed, unpacked, local });
    pos += 46 + nlen + elen + clen;
  }
  function read(name) {
    const x = names.get(name);
    if (!x) throw Error("Missing EPUB chapter: " + name);
    if (x.unpacked > 12_000_000 || x.packed > 12_000_000)
      throw Error("Oversized EPUB chapter: " + name);
    if (data.readUInt32LE(x.local) !== 0x04034b50)
      throw Error("Bad ZIP local entry: " + name);
    const begin = x.local + 30 + data.readUInt16LE(x.local + 26) + data.readUInt16LE(x.local + 28);
    const chunk = data.subarray(begin, begin + x.packed);
    const unpacked = x.method === 0 ? chunk : x.method === 8 ? zlib.inflateRawSync(chunk) : null;
    if (!unpacked || unpacked.length !== x.unpacked) throw Error("Bad EPUB compression: " + name);
    return unpacked.toString("utf8");
  }
  return {names, read};
}
function entityDecode(text) {
  const map = {amp:"&", lt:"<", gt:">", quot:'"', apos:"'", nbsp:" ",
    mdash:"—", ndash:"–", rsquo:"’", lsquo:"‘", ldquo:"“", rdquo:"”",
    hellip:"…", copy:"©", bull:"•"};
  return String(text).replace(/&(#x[0-9a-f]+|#[0-9]+|[a-zA-Z]+);/gi, (all, code) => {
    if (code[0] === "#") {
      const n = code[1]?.toLowerCase() === "x" ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10);
      return n >= 0 && n <= 0x10ffff ? String.fromCodePoint(n) : all;
    }
    return map[code.toLowerCase()] ?? all;
  });
}
function normTitle(v) {
  return entityDecode(v).replace(/<[^>]+>/g, "").normalize("NFKC").replace(/\s+/g, " ").trim().toLowerCase();
}
function toc(zip) {
  const file = [...zip.names.keys()].find(n => /\.ncx$/i.test(n));
  if (!file) throw Error("EPUB NCX missing");
  const xml = zip.read(file);
  const rows = [];
  const points = xml.match(/<navPoint\b[\s\S]*?<\/navPoint>/gi) || [];
  for (const block of points) {
    const title = block.match(/<navLabel\b[^>]*>[\s\S]*?<text\b[^>]*>([\s\S]*?)<\/text>/i)?.[1];
    const src = block.match(/<content\b[^>]*\bsrc\s*=\s*["']([^"']+)["']/i)?.[1];
    if (!title || !src) continue;
    const clean = entityDecode(title.replace(/<[^>]*>/g,"")).trim();
    if (["title page","cover"].includes(clean.toLowerCase())) continue;
    const target = path.posix.normalize(path.posix.join(path.posix.dirname(file),
      entityDecode(src.split("#")[0])));
    if (target.startsWith("../") || target.startsWith("/") || target.includes("\0"))
      throw Error("Invalid EPUB file path: " + target);
    rows.push({ title:clean, chapter:target });
  }
  return rows;
}
function extractBody(html) {
  const open = /<div\b[^>]*\bclass\s*=\s*["'][^"']*\bbook-content\b[^"']*["'][^>]*>/i.exec(html);
  if (!open) return "";
  const start = open.index + open[0].length;
  const tags = /<\/?div\b[^>]*>/gi;
  tags.lastIndex = start;
  let depth = 1, end = -1, match;
  while ((match = tags.exec(html))) {
    depth += /^<\/div/i.test(match[0]) ? -1 : 1;
    if (depth === 0) { end = match.index; break; }
  }
  // Some archived pages contain malformed nested DIV markup. In that case
  // preserve the page body through its closing tag rather than discard text.
  if (end < 0) end = html.toLowerCase().lastIndexOf("</body>");
  if (end < start) throw Error("Book body DIV not closed and BODY missing");
  return entityDecode(html.slice(start,end)
    .replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi,"")
    .replace(/<br\s*\/?>/gi,"\n")
    .replace(/<\/(p|h[1-6]|div|li|blockquote|tr)>/gi,"\n\n")
    .replace(/<li\b[^>]*>/gi,"\n• ")
    .replace(/<\/?(strong|b|em|i)\b[^>]*>/gi,"")
    .replace(/<[^>]+>/g,"")
    .replace(/\r\n?/g,"\n"))
    .replace(/[ \t]+\n/g,"\n")
    .replace(/\n{3,}/g,"\n\n")
    .trim();
}
function run() {
  const options = args(process.argv.slice(2));
  const root = process.cwd(), output = path.resolve(root, options.output);
  const privateRoot = path.resolve(root,"work");
  if (!output.startsWith(privateRoot + path.sep))
    throw Error("Output must be inside Git-ignored work/ directory");
  const catalog = JSON.parse(fs.readFileSync(options.catalog,"utf8"));
  const entries = catalog.entries.filter(row => row.game === "eso");
  const zip = zipFiles(options.epub), chapters = toc(zip);
  if (chapters.length !== entries.length)
    throw Error("TOC differs from catalog: " + chapters.length + " vs " + entries.length);
  fs.mkdirSync(output, {recursive:true});
  const result = [], errors = [];
  for (let i=0;i<entries.length;i++) {
    const book = entries[i], ch = chapters[i];
    if (normTitle(book.title_en) !== normTitle(ch.title)) {
      errors.push({i:i+1,title_en:book.title_en,toc_title:ch.title,reason:"title_mismatch"});
      continue;
    }
    const dest = path.join(output,book.uid + ".txt");
    if (fs.existsSync(dest) && !options.overwrite) {
      result.push({uid:book.uid,title:book.title_en,status:"exists",file:path.basename(dest)});
      continue;
    }
    let body;
    try { body = extractBody(zip.read(ch.chapter)); }
    catch (e) { errors.push({i:i+1,title:book.title_en,reason:String(e)});continue; }
    if (!body) {errors.push({i:i+1,title:book.title_en,reason:"empty_body"});continue;}
    fs.writeFileSync(dest,body+"\n","utf8");
    result.push({uid:book.uid,title:book.title_en,status:"written",file:path.basename(dest),
      chars:body.length,sha256:crypto.createHash("sha256").update(body).digest("hex")});
  }
  const report = { schema_version:1, source_file:path.basename(options.epub),
    warning:"PRIVATE LOCAL REFERENCE ONLY — NOT LICENSED FOR PUBLIC REDISTRIBUTION",
    total:entries.length,success:result.length,skipped:errors.length,items:result,errors };
  fs.writeFileSync(path.join(output,"_extraction_manifest.json"),
    JSON.stringify(report,null,2)+"\n","utf8");
  console.log(JSON.stringify({total:entries.length, extracted:result.filter(x=>x.status==="written").length,
    existing:result.filter(x=>x.status==="exists").length,issues:errors.length,local_output:output,
    issue_details:errors.slice(0,30)},null,2));
  if (errors.length) process.exitCode = 2;
}
try { run(); } catch(e) { console.error(e.message); process.exitCode = 1; }
