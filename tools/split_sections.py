#!/usr/bin/env python3
"""
Split the ExtraaEdge homepage into one standalone, runnable HTML file per section.

Strategy
--------
1. Enumerate every TOP-LEVEL block of the source document (comments, <style>,
   <script>, and the section elements themselves) with exact source offsets.
2. Assign each block to a target using an explicit line-range manifest:
      GLOBAL     -> shared CSS / shared JS used by every section
      HEADLINKS  -> <link>/<script src> tags copied verbatim into every <head>
      DROP       -> page-level SEO/meta/containers that a single section does not need
      S:<slug>   -> that section's own markup + its own scripts
3. Emit:
      assets/global.css      every top-level <style>, in original document order
      sections/<n>-<slug>.html  one runnable page per section
      index.html             a launcher that lists / previews every section

Nothing is paraphrased: every byte of markup, CSS and JS is copied verbatim from
the source. The script asserts full line coverage so no block can be lost.
"""

import json
import os
import re
import shutil
import sys
from html.parser import HTMLParser

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "extraaedge-sections")
# The reference copy inside the output folder is the default source, so the split
# can be reproduced from a clean checkout without the original upload.
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "_original", "full-homepage.html")

if not os.path.isfile(SRC):
    raise SystemExit(f"source homepage not found: {SRC}\n"
                     f"usage: python3 {os.path.basename(__file__)} [path/to/homepage.html]")

src = open(SRC, encoding="utf-8").read()
lines = src.split("\n")
line_start = [0]
for L in lines:
    line_start.append(line_start[-1] + len(L) + 1)

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

# Start lines of the elements that merely WRAP the page flow. Their children are
# the real top-level blocks, so these are transparent to the enumerator.
CONTAINERS = {2, 3, 2076, 2077, 2271}


# --------------------------------------------------------------------------- #
# 1. enumerate top-level blocks                                                #
# --------------------------------------------------------------------------- #
class BlockScanner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []          # [(tag, startline)]
        self.blocks = []
        self.pending = {}        # depth -> (tag, attrs, startoffset, startline)

    def _off(self):
        line, col = self.getpos()
        return line_start[line - 1] + col

    def _in_container(self):
        return (not self.stack) or self.stack[-1][1] in CONTAINERS

    def _add(self, kind, tag, attrs, s, e):
        self.blocks.append(dict(
            kind=kind, tag=tag, attrs=attrs, s=s, e=e,
            sl=src.count("\n", 0, s) + 1,
            el=src.count("\n", 0, e) + 1,
        ))

    def handle_starttag(self, tag, attrs):
        s = self._off()
        if tag in VOID:
            if self._in_container():
                self._add("void", tag, dict(attrs), s, s + len(self.get_starttag_text() or ""))
            return
        if self._in_container():
            self.pending[len(self.stack)] = (tag, dict(attrs), s, self.getpos()[0])
        self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        s = self._off()
        if self._in_container():
            self._add("void", tag, dict(attrs), s, s + len(self.get_starttag_text() or ""))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag not in [t for t, _ in self.stack]:
            return
        while self.stack:
            t, _ = self.stack.pop()
            if t == tag:
                break
        d = len(self.stack)
        p = self.pending.pop(d, None)
        if p and p[0] == tag:
            e = self._off() + len(tag) + 3          # </tag>
            if p[3] not in CONTAINERS:
                self._add("el", tag, p[1], p[2], e)

    def handle_comment(self, data):
        if self._in_container():
            s = self._off()
            self._add("cmt", "#", {"text": data}, s, s + len(data) + 7)

    def handle_decl(self, decl):
        if self._in_container():
            s = self._off()
            self._add("decl", "!", {"text": decl}, s, s + len(decl) + 3)


scanner = BlockScanner()
scanner.feed(src)
blocks = sorted(scanner.blocks, key=lambda b: (b["s"], -b["e"]))

# drop blocks fully nested inside a previously emitted block (belt & braces)
flat, cursor = [], -1
for b in blocks:
    if b["s"] < cursor:
        continue
    flat.append(b)
    cursor = b["e"]
blocks = flat


# --------------------------------------------------------------------------- #
# 2. manifest: source line range -> target                                     #
# --------------------------------------------------------------------------- #
# (first_line, last_line, target)
MANIFEST = [
    (1,     6,    "DROP"),        # doctype, <html>, <head>, page <title>
    (7,     12,   "HEADMETA"),    # charset / viewport / base meta
    (13,    98,   "GLOBAL"),      # site zoom, design tokens, a11y base layer
    (99,    157,  "DROP"),        # SEO / OpenGraph / Twitter / icons / manifest
    (158,   168,  "HEADLINKS"),   # preconnect + dns-prefetch resource hints
    (169,   251,  "DROP"),        # sitewide JSON-LD
    (252,   257,  "HEADLINKS"),   # Google Fonts (Inter)
    (258,   265,  "GLOBAL"),      # inlined Tailwind build
    (266,   266,  "HEADLINKS"),   # Lucide icon library (CDN)
    (267,   707,  "GLOBAL"),      # critical CSS
    (708,   1440, "S:header"),    # site header + full mobile sidebar menu
    (1441,  1574, "GLOBAL"),      # Lucide bootstrap + header-height var + reveal
    (1575,  1872, "S:header"),    # 2026 header skin + its JS
    (1873,  1930, "GLOBAL"),      # global heading scale
    (1931,  2073, "S:header"),    # mega-bar
    (2074,  2077, "DROP"),        # <main> landmarks
    (2078,  2266, "GLOBAL"),      # home heading scale + compact rhythm
    (2267,  2271, "DROP"),        # <div class="ee-home"> wrapper
    (2272,  2297, "S:hero"),      # hero styles
    (2298,  2394, "S:quick-toc"),
    (2395,  2483, "S:hero"),      # <section id="xhero">
    # The Book-a-Demo drawer is driven by the hero's own IIFE (it looks up
    # #admission-form / #eeddBack / #eeddClose), so drawer + hero ship together.
    (2484,  2516, "S:hero"),      # Book-a-Demo drawer markup
    (2517,  2809, "S:hero"),      # hero video + drawer controller + typewriter
    (2810,  3076, "S:trusted-institutions"),
    (3077,  3340, "S:why-extraaedge"),
    (3341,  3620, "S:respond-first-ai"),
    (3621,  5019, "S:platform-live-demo"),
    (5020,  5187, "S:see-real-crm-popup"),
    (5188,  5292, "S:stories"),   # #stories rail script (sits above its markup)
    (5293,  5393, "GLOBAL"),      # shared products/vidya/solutions/industries CSS
    (5394,  6212, "S:vidyaai-powered-by"),
    (6213,  6480, "GLOBAL"),      # shared product-card CSS
    (6481,  6882, "S:vidya-suite"),
    (6883,  6923, "S:architect-mindset"),
    (6924,  7060, "S:stories"),
    (7061,  7084, "S:mid-cta"),
    (7085,  7379, "S:industries"),
    (7380,  7455, "S:cro-roi"),
    (7456,  7571, "S:misc-widgets"),
    (7572,  7844, "S:integrations"),
    (7845,  7863, "S:security"),
    (7864,  7912, "GLOBAL"),      # shared CRO / go-live / pricing CSS
    (7913,  7931, "S:go-live"),
    (7932,  7956, "S:switch-crm"),
    (7957,  8007, "S:pricing"),
    (8008,  8033, "S:faq"),
    (8034,  8291, "S:products"),
    (8292,  8400, "GLOBAL"),      # solutions CSS
    (8401,  8532, "S:solutions"),
    (8533,  8709, "S:resources"),
    (8710,  8781, "S:blog"),
    (8782,  8786, "DROP"),        # </div> ee-home
    (8787,  8978, "GLOBAL"),      # global reveal script + responsive/motion CSS
    (8979,  9054, "S:scroll-progress-cta"),
    (9055,  9361, "GLOBAL"),      # brand / mobile / spatial skins + anchor fixer
    (9362,  9394, "S:trusted-institutions"),   # logo-marquee watchdog
    (9395,  9524, "GLOBAL"),
    (9525,  9534, "S:vidyaai-powered-by"),     # embed reveal script
    (9535,  9667, "GLOBAL"),      # nav-wow / sticky-fix / 2026 skin
    (9668,  9675, "DROP"),        # </main> + footer banner comments
    (9676,  9676, "HEADLINKS"),   # Font Awesome (footer icons)
    (9677,  10036, "S:footer"),
    (10037, 10191, "S:floating-actions"),
    (10192, 10319, "GLOBAL"),     # standard button skin
    (10320, 10322, "DROP"),       # </body></html>
]

# ordered section metadata: slug -> (order, title, wrap_in_ee_home)
SECTIONS = [
    ("header",              "Site Header & Mobile Menu",            False),
    ("quick-toc",           "Quick Table of Contents (floating)",    True),
    ("hero",                "Hero + Book-a-Demo Drawer",             True),
    ("trusted-institutions", "Trusted Institutions Logo Marquee",    True),
    ("why-extraaedge",      "Why Institutes Choose ExtraaEdge",      True),
    ("respond-first-ai",    "Respond First With AI Agents",          True),
    ("platform-live-demo",  "Platform — Live Interactive Demo",      True),
    ("see-real-crm-popup",  "See the Real CRM — Booking Popup",      True),
    ("vidyaai-powered-by",  "Powered by VidyaAI (embed)",            True),
    ("vidya-suite",         "Meet Vidya AI — Suite",                 True),
    ("architect-mindset",   "Architect Mindset",                     True),
    ("stories",             "Customer Stories",                      True),
    ("mid-cta",             "Mid-Page CTA — Book a Demo",            True),
    ("industries",          "Industries We Serve",                   True),
    ("cro-roi",             "Why Teams Choose Us + ROI Calculator",  True),
    ("misc-widgets",        "Scroll Widgets (divider, progress, toast)", True),
    ("integrations",        "Integrations Hub",                      True),
    ("security",            "Security & Compliance",                 True),
    ("go-live",             "Go Live in 7 Days",                     True),
    ("switch-crm",          "Switch From Your Current CRM",          True),
    ("pricing",             "Simple Product-Based Pricing",          True),
    ("faq",                 "FAQ",                                   True),
    ("products",            "Our Products",                          True),
    ("solutions",           "Solutions",                             True),
    ("resources",           "Resources & Events",                    True),
    ("blog",                "Latest From the Blog",                  True),
    ("scroll-progress-cta", "Scroll Progress Bar + Sticky Demo Pill", True),
    ("footer",              "Site Footer",                           False),
    ("floating-actions",    "Floating Actions (WhatsApp / Call / TOC)", False),
]
SECTION_META = {slug: (i + 1, title, wrap) for i, (slug, title, wrap) in enumerate(SECTIONS)}


# Sections whose markup is entirely position:fixed / hidden-until-triggered.
# On their own page they would render as a blank screen, so they get a small,
# clearly fenced preview harness: a note, a scroll spacer, and (where the widget
# only opens from another section) a button that flips the widget's own class.
# slug -> (note, trigger_html)
HARNESS = {
    "header": (
        "The header is <code>position: sticky</code>. Scroll the filler below to "
        "watch it compact and re-skin.", ""),
    "quick-toc": (
        "This section is the floating table-of-contents launcher. Look for the round "
        "button on the left edge and click it to slide the panel open.", ""),
    "see-real-crm-popup": (
        "This overlay normally opens from inside the live platform demo (section 08). "
        "Use the button to show it here.",
        '<button type="button" onclick="document.getElementById(\'eebkOv\')'
        '.classList.toggle(\'on\')">Toggle the popup</button>'),
    "misc-widgets": (
        "Scroll-driven widgets: a section divider, the reading-progress rail and the "
        "toast host. Scroll the filler below to see them react.", ""),
    "scroll-progress-cta": (
        "The scroll-progress bar sits at the very top of the viewport and the sticky "
        "demo pill appears on phones after ~35% scroll. Scroll the filler below "
        "(and try a narrow viewport) to see both.", ""),
    "floating-actions": (
        "Floating WhatsApp / Call / Book-a-Demo bubbles, pinned to the bottom-right "
        "corner of the viewport.", ""),
}

HARNESS_CSS = """
<!-- ══════════ PREVIEW HARNESS · not part of the original page ══════════
     Everything tagged data-preview-harness exists only so this fixed /
     overlay widget is visible when the file is opened on its own.
     Delete the two harness blocks to get the raw section back. -->
<style data-preview-harness>
  .eeph{position:relative;z-index:5;margin:0 auto 26px;max-width:760px;padding:16px 20px;
        border:1px dashed #cbd5e1;border-left:4px solid #DE6E30;border-radius:10px;
        background:#fff;color:#475569;font:14.5px/1.55 Inter,system-ui,sans-serif;}
  .eeph b{display:block;color:#19335D;font-size:12px;letter-spacing:.09em;
          text-transform:uppercase;margin-bottom:5px;}
  .eeph code{background:#f1f5f9;padding:1px 5px;border-radius:4px;}
  .eeph button{margin-top:11px;padding:9px 16px;border:0;border-radius:8px;
               background:#DE6E30;color:#fff;font-weight:650;cursor:pointer;}
  .eeph-fill{max-width:760px;margin:0 auto;padding:0 20px 40px;color:#94a3b8;
             font:14px/2.1 Inter,system-ui,sans-serif;}
  .eeph-fill p{margin:0 0 34px;}
</style>
"""

HARNESS_FILL = (
    '<div class="eeph-fill" data-preview-harness aria-hidden="true">'
    + "".join(
        "<p>Filler paragraph {0} — scroll room so the fixed widget above has "
        "something to react to.</p>".format(i + 1) for i in range(14))
    + "</div>\n<!-- ══════════ /PREVIEW HARNESS ══════════ -->"
)


def target_for(line_no):
    for a, b, t in MANIFEST:
        if a <= line_no <= b:
            return t
    raise SystemExit(f"line {line_no} is not covered by the manifest")


# manifest sanity: contiguous, ordered, covers the whole file
prev_end = 0
for a, b, t in MANIFEST:
    assert a == prev_end + 1, f"manifest gap/overlap at line {a} (previous ended {prev_end})"
    assert b >= a
    prev_end = b
assert prev_end >= len(lines) - 1, f"manifest stops at {prev_end}, file has {len(lines)} lines"


# --------------------------------------------------------------------------- #
# 3. bucket the blocks                                                         #
# --------------------------------------------------------------------------- #
global_css = []      # list of (label, css_text)
head_extra = []      # verbatim <link> / <script src> / <meta> lines
section_parts = {slug: [] for slug, _, _ in SECTIONS}
global_scripts = []  # verbatim <script>...</script> blocks shared by all pages
dropped = []
unassigned = []

STYLE_OPEN = re.compile(r"^<style\b[^>]*>", re.I)
STYLE_CLOSE = re.compile(r"</style\s*>$", re.I)


def raw(b):
    return src[b["s"]:b["e"]]


for b in blocks:
    tgt = target_for(b["sl"])
    text = raw(b)

    if tgt == "DROP":
        dropped.append((b["sl"], b["kind"], b["tag"]))
        continue

    if tgt in ("HEADMETA", "HEADLINKS"):
        if b["kind"] == "cmt":
            continue
        head_extra.append(text)
        continue

    # every top-level <style> becomes part of the shared stylesheet, in order
    if b["kind"] == "el" and b["tag"] == "style":
        inner = STYLE_OPEN.sub("", text)
        inner = STYLE_CLOSE.sub("", inner)
        label = b["attrs"].get("id") or f"line {b['sl']}"
        global_css.append((label, b["sl"], inner))
        continue

    if tgt == "GLOBAL":
        if b["kind"] == "cmt":
            continue
        if b["kind"] == "el" and b["tag"] == "script":
            global_scripts.append(text)
            continue
        unassigned.append((b["sl"], b["kind"], b["tag"], b["attrs"].get("id", "")))
        continue

    if tgt.startswith("S:"):
        slug = tgt[2:]
        if slug not in section_parts:
            raise SystemExit(f"unknown section slug {slug!r} at line {b['sl']}")
        section_parts[slug].append(text)
        continue

    raise SystemExit(f"unhandled target {tgt!r}")

if unassigned:
    print("WARNING: global-range markup that is not CSS/JS:", unassigned, file=sys.stderr)


# --------------------------------------------------------------------------- #
# 4. write the output tree                                                     #
# --------------------------------------------------------------------------- #
# Clear only what this script generates — README.md is hand-written and stays.
for stale in ("sections", "assets"):
    shutil.rmtree(os.path.join(OUT, stale), ignore_errors=True)
for stale in ("index.html", "sections.json"):
    if os.path.isfile(os.path.join(OUT, stale)):
        os.remove(os.path.join(OUT, stale))
os.makedirs(f"{OUT}/assets", exist_ok=True)
os.makedirs(f"{OUT}/sections", exist_ok=True)
os.makedirs(f"{OUT}/_original", exist_ok=True)

# --- shared stylesheet -----------------------------------------------------
css_out = ["/* ==========================================================================",
           "   ExtraaEdge — shared stylesheet",
           "   Every top-level <style> block of the original homepage, concatenated in",
           "   the exact document order so the cascade is identical to the live page.",
           "   Generated by tools/split_sections.py — do not hand-edit.",
           "   ========================================================================== */",
           ""]
for label, sl, inner in global_css:
    css_out.append(f"/* ---- {label}  (source line {sl}) ---- */")
    css_out.append(inner.strip("\n"))
    css_out.append("")
open(f"{OUT}/assets/global.css", "w", encoding="utf-8").write("\n".join(css_out))

# --- shared scripts (inlined per page, one <script> tag each, verbatim) -----
shared_js_html = "\n".join(global_scripts)
open(f"{OUT}/assets/global-scripts.html", "w", encoding="utf-8").write(
    "<!-- Shared <script> blocks from the original homepage. Inlined verbatim at the\n"
    "     bottom of every section page so each block keeps its own top-level scope\n"
    "     and its own error isolation, exactly like the live page. -->\n"
    + shared_js_html + "\n")

head_html = "\n".join("    " + h for h in head_extra)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


PAGE = """<!DOCTYPE html>
<html lang="en-US">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} · ExtraaEdge section</title>
{head}
    <!-- shared stylesheet: every <style> block of the original page, in order -->
    <link rel="stylesheet" href="../assets/global.css">
</head>
<body>
<!-- ══════════════════════════════════════════════════════════════════════════
     SECTION {num:02d} · {title}
     Extracted verbatim from ExtraaEdgeHomepageWithVideoAndOldHeader.html
     (source lines {srclines})
     Open this file with VS Code "Live Server" (or any static server) to run
     this section on its own.
     ══════════════════════════════════════════════════════════════════════════ -->
{open_wrap}
{body}
{close_wrap}

<!-- ── shared page scripts (verbatim from the original homepage) ── -->
{scripts}
</body>
</html>
"""

manifest_rows = []
for slug, title, wrap in SECTIONS:
    num = SECTION_META[slug][0]
    parts = section_parts[slug]
    if not parts:
        raise SystemExit(f"section {slug!r} ended up empty")
    src_ranges = ", ".join(f"{a}-{b}" for a, b, t in MANIFEST if t == f"S:{slug}")
    fname = f"{num:02d}-{slug}.html"
    body = "\n\n".join(parts)
    if slug in HARNESS:
        note, trigger = HARNESS[slug]
        body = (body + "\n\n" + HARNESS_CSS
                + f'<div class="eeph" data-preview-harness>'
                  f'<b>Preview harness</b>{note}{trigger}</div>\n'
                + HARNESS_FILL)
    page = PAGE.format(
        title=title, head=head_html, num=num, srclines=src_ranges,
        open_wrap='<main id="main-content">\n<div class="ee-home">' if wrap else "",
        close_wrap='</div>\n</main>' if wrap else "",
        body=body, scripts=shared_js_html,
    )
    open(f"{OUT}/sections/{fname}", "w", encoding="utf-8").write(page)
    manifest_rows.append((num, slug, title, fname, src_ranges, len(page)))

# --- reference copy of the untouched original -------------------------------
# written from the in-memory source: the default SRC lives inside OUT, which the
# rebuild wipes before regenerating.
open(f"{OUT}/_original/full-homepage.html", "w", encoding="utf-8").write(src)

json.dump(
    [dict(order=n, slug=s, title=t, file=f"sections/{f}", source_lines=r, bytes=b)
     for n, s, t, f, r, b in manifest_rows],
    open(f"{OUT}/sections.json", "w", encoding="utf-8"), indent=2,
)

print(f"sections written : {len(manifest_rows)}")
print(f"global.css       : {os.path.getsize(OUT + '/assets/global.css'):,} bytes "
      f"({len(global_css)} style blocks)")
print(f"shared scripts   : {len(global_scripts)} blocks, {len(shared_js_html):,} bytes")
print(f"dropped blocks   : {len(dropped)} (SEO meta, JSON-LD, wrappers)")
for n, s, t, f, r, b in manifest_rows:
    print(f"  {n:02d} {f:<34} {b:>9,} B   src {r}")


# --------------------------------------------------------------------------- #
# 5. launcher page                                                             #
# --------------------------------------------------------------------------- #
cards = "\n".join(
    f'''      <li class="card">
        <a href="sections/{f}">
          <span class="num">{n:02d}</span>
          <span class="ttl">{esc(t)}</span>
          <span class="meta">{f} · {b // 1024} KB · source lines {r}</span>
        </a>
      </li>''' for n, s, t, f, r, b in manifest_rows)

INDEX = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ExtraaEdge homepage · section index</title>
<style>
  :root {{ --blue:#19335D; --orange:#DE6E30; --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --bg:#f8fafc; --card:#fff; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --ink:#e6edf7; --muted:#93a4bd; --line:#24344d; --bg:#0d1522; --card:#131e2f; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:40px 20px 80px; background:var(--bg); color:var(--ink);
         font:16px/1.5 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  .wrap {{ max-width:1100px; margin:0 auto; }}
  h1 {{ font-size:28px; margin:0 0 6px; letter-spacing:-.02em; }}
  .sub {{ color:var(--muted); margin:0 0 28px; }}
  .hint {{ background:var(--card); border:1px solid var(--line); border-left:4px solid var(--orange);
           border-radius:10px; padding:14px 18px; margin:0 0 28px; color:var(--muted); font-size:14.5px; }}
  .hint code {{ background:rgba(127,127,127,.14); padding:1px 6px; border-radius:5px; color:var(--ink); }}
  ul {{ list-style:none; margin:0; padding:0; display:grid; gap:12px;
        grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); }}
  .card a {{ display:grid; gap:4px; padding:16px 18px; background:var(--card); border:1px solid var(--line);
             border-radius:12px; text-decoration:none; color:inherit; transition:.18s; height:100%; }}
  .card a:hover {{ border-color:var(--orange); transform:translateY(-2px);
                   box-shadow:0 10px 24px -14px rgba(0,0,0,.45); }}
  .num {{ font-size:12px; font-weight:700; color:var(--orange); letter-spacing:.1em; }}
  .ttl {{ font-size:16.5px; font-weight:650; color:var(--blue); }}
  @media (prefers-color-scheme: dark) {{ .ttl {{ color:#cfe0ff; }} }}
  .meta {{ font-size:12.5px; color:var(--muted); }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>ExtraaEdge homepage — {len(manifest_rows)} standalone sections</h1>
    <p class="sub">Each card opens one section as its own runnable page.</p>
    <p class="hint">Open this folder in VS Code and start <strong>Live Server</strong> (right-click &rarr;
       <em>Open with Live Server</em>) on this file, or on any file in <code>sections/</code> to run that
       section on its own. Every page loads the shared stylesheet from
       <code>assets/global.css</code>, so keep the folder structure intact.</p>
    <ul>
{cards}
    </ul>
  </div>
</body>
</html>
"""
open(f"{OUT}/index.html", "w", encoding="utf-8").write(INDEX)
print("index.html written")
