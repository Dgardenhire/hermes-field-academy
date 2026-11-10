#!/usr/bin/env python3
"""Build docs/concept-brief-nous.html: one self-contained file, images embedded, topo maps generated here.

Run from the repository folder: python3 docs/make_brief.py
"""

import base64
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def img(name):
    return "data:image/jpeg;base64," + base64.b64encode((HERE / "brief-img" / name).read_bytes()).decode()


def height(x, y, peaks):
    return sum(a * math.exp(-(((x - px) / sx) ** 2 + ((y - py) / sy) ** 2)) for a, px, py, sx, sy in peaks)


def contours(w, h, peaks, levels, step=11):
    """Marching squares over a smooth field. Returns one SVG path string per level."""
    nx, ny = int(w / step) + 2, int(h / step) + 2
    grid = [[height(i * step, j * step, peaks) for i in range(nx)] for j in range(ny)]
    paths = []
    for lv in levels:
        d = []
        for j in range(ny - 1):
            for i in range(nx - 1):
                a, b, c, e = grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]
                idx = (a > lv) * 8 + (b > lv) * 4 + (c > lv) * 2 + (e > lv)
                if idx in (0, 15):
                    continue
                x, y = i * step, j * step

                def lerp(p, q):
                    return 0.5 if p == q else (lv - p) / (q - p)
                top = (x + step * lerp(a, b), y)
                right = (x + step, y + step * lerp(b, c))
                bottom = (x + step * lerp(e, c), y + step)
                left = (x, y + step * lerp(a, e))
                segs = {1: [(left, bottom)], 2: [(bottom, right)], 3: [(left, right)], 4: [(top, right)],
                        5: [(left, top), (bottom, right)], 6: [(top, bottom)], 7: [(left, top)], 8: [(left, top)],
                        9: [(top, bottom)], 10: [(left, bottom), (top, right)], 11: [(top, right)],
                        12: [(left, right)], 13: [(bottom, right)], 14: [(left, bottom)]}[idx]
                for p, q in segs:
                    d.append(f"M{p[0]:.0f} {p[1]:.0f}L{q[0]:.0f} {q[1]:.0f}")
        paths.append((lv, "".join(d)))
    return paths


def topo_svg(w, h, peaks, levels, cls, index_every=5):
    out = [f'<svg class="{cls}" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">']
    for n, (lv, d) in enumerate(contours(w, h, peaks, levels)):
        k = "ci" if n % index_every == 0 else "c"
        out.append(f'<path class="{k}" d="{d}"/>')
    out.append("</svg>")
    return "".join(out)


HERO_PEAKS = [(1.0, 1440, 190, 260, 200), (0.75, 900, 360, 220, 160), (0.55, 1420, 520, 200, 230),
              (0.45, 300, 610, 300, 170), (0.35, 620, 130, 170, 140), (-0.25, 520, 420, 180, 120)]
HERO = topo_svg(1600, 760, HERO_PEAKS, [0.06 + 0.055 * i for i in range(22)], "topo")

PAPER_PEAKS = [(0.9, 260, 120, 260, 180), (0.6, 980, 300, 300, 160), (0.4, 640, 40, 200, 120)]
PAPER = topo_svg(1400, 420, PAPER_PEAKS, [0.08 + 0.07 * i for i in range(14)], "topo-paper", 4)

# The route across the hero: camps sit on rising ground toward the main peak.
ROUTE = [(860, 712), (930, 660), (1000, 628), (1080, 590), (1150, 540), (1220, 480), (1290, 420), (1350, 350),
         (1400, 270), (1440, 190)]
route_d = "M" + " L".join(f"{x} {y}" for x, y in ROUTE)
CAMPS = [(930, 660, "Messenger", ""), (1080, 590, "Traveler", ""), (1220, 480, "Crossroads", ""),
         (1290, 420, "Boundary Keeper", ""), (1350, 350, "Guide", "")]

camp_svg = "".join(
    f'<g class="camp"><circle cx="{x}" cy="{y}" r="7"/><line x1="{x}" y1="{y - 9}" x2="{x}" y2="{y - 46}"/>'
    f'<text x="{x + 10}" y="{y - 36}" class="cl">{name.upper()}</text>'
    f'<text x="{x + 10}" y="{y - 22}" class="ce">CAMP {i + 1}</text></g>'
    for i, (x, y, name, _e) in enumerate(CAMPS))

TICKS = "".join(f'<text x="{x}" y="22" class="tick">{x // 10:03d}</text>' for x in range(200, 1600, 200)) + \
    "".join(f'<text x="14" y="{y}" class="tick">{y // 10:03d}</text>' for y in range(150, 760, 150))

# Elevation profile for the Guide trail: four camps, nine parts, one summit.
PARTS = [("The key in the open", 1), ("The runaway bill", 1), ("Monday after the power cut", 1),
         ("One key for everything", 2), ("A proposal for a three-person firm", 2), ("Nine judgment scenarios", 2),
         ("Run one real service for several days", 3), ("Failure drills", 4), ("Walkthrough and expert review", 4)]
PW, PH = 1100, 300
xs = [70 + i * (PW - 170) / 8 for i in range(9)]
ys = [258 - (i ** 1.18) * 18 for i in range(9)]
prof = "M0 290 L0 262 " + " ".join(f"L{x:.0f} {y:.0f}" for x, y in zip(xs, ys)) + f" L{PW - 30} 24 L{PW} 30 L{PW} 290 Z"
ridge = "M0 262 " + " ".join(f"L{x:.0f} {y:.0f}" for x, y in zip(xs, ys)) + f" L{PW - 30} 24"
dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="6" class="pd"/><text x="{x:.0f}" y="{y + 22:.0f}" class="pn">{i + 1:02d}</text>'
               for i, (x, y) in enumerate(zip(xs, ys)))
camp_bounds = [(0, 2, "AUDIT"), (3, 5, "ARCHITECT"), (6, 6, "BUILD"), (7, 8, "VERIFY")]
bands = "".join(f'<text x="{(xs[a] + xs[b]) / 2:.0f}" y="292" class="pb">CAMP {n + 1} · {label}</text>'
                for n, (a, b, label) in enumerate(camp_bounds))
PROFILE = (f'<svg class="profile" viewBox="0 0 {PW} 310" aria-label="Elevation profile of the Guide trail">'
           f'<defs><linearGradient id="pg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--copper)" stop-opacity=".32"/>'
           f'<stop offset="1" stop-color="var(--copper)" stop-opacity="0"/></linearGradient></defs>'
           + "".join(f'<line x1="0" x2="{PW}" y1="{y}" y2="{y}" class="pg"/>' for y in (60, 120, 180, 240))
           + f'<path d="{prof}" fill="url(#pg)"/><path d="{ridge}" class="pr"/>{dots}'
           f'<g class="flag"><line x1="{PW - 30}" y1="24" x2="{PW - 30}" y2="-8"/><path d="M{PW - 30} -8 l20 7 -20 7z"/></g>{bands}</svg>')

parts_list = "".join(f'<li><span class="pnum">{i + 1:02d}</span><span>{t}</span></li>' for i, (t, _c) in enumerate(PARTS))

HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Field Academy proposal</title>
<style>
:root{{
  --ink:#0b110f; --ink2:#111915; --ink3:#18221d; --line:#24302a;
  --text:#ece6d8; --soft:#cfc8b8; --copper:#de7d3e; --copper2:#f0a46c; --moss:#7f9b78;
  --paper:#efe7d5; --paper2:#e6dcc6; --pink:#1d2420; --psoft:#3a433d; --pcopper:#a8501a;
  --serif:"Iowan Old Style","New York","Palatino Linotype",Palatino,Georgia,serif;
  --sans:-apple-system,"SF Pro Text","Segoe UI",system-ui,sans-serif;
  --mono:"SF Mono",ui-monospace,Menlo,Consolas,monospace;
}}
*{{box-sizing:border-box}}
html{{background:var(--ink)}} body{{overflow-x:hidden}}
body{{margin:0;color:var(--text);font:18px/1.62 var(--serif);-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 32px}}
.label{{font:600 11.5px/1.2 var(--mono);letter-spacing:.2em;text-transform:uppercase;color:var(--copper)}}
p{{margin:0 0 16px}}

/* hero */
.hero{{position:relative;min-height:760px;overflow:hidden;background:radial-gradient(120% 90% at 75% 15%,#16201b 0%,var(--ink) 60%);border-bottom:1px solid var(--line)}}
.topo{{position:absolute;inset:0;width:100%;height:100%}}
.topo .c{{fill:none;stroke:#2a3a31;stroke-width:1;stroke-linecap:round}}
.topo .ci{{fill:none;stroke:#3f5446;stroke-width:1.6;stroke-linecap:round}}
.hero .over{{position:absolute;inset:0;width:100%;height:100%}}
.tick{{font:600 10px var(--mono);fill:#5e7366;letter-spacing:.1em}}
.route{{fill:none;stroke:var(--copper);stroke-width:2.6;stroke-dasharray:2 9;stroke-linecap:round}}
.route-glow{{fill:none;stroke:var(--copper);stroke-opacity:.18;stroke-width:12;stroke-linecap:round}}
.camp circle{{fill:var(--ink);stroke:var(--copper);stroke-width:2.6}}
.camp line{{stroke:var(--copper2);stroke-width:1}}
.cl{{font:700 11px var(--mono);letter-spacing:.18em;fill:var(--text)}}
.ce{{font:600 9.5px var(--mono);letter-spacing:.16em;fill:var(--copper2)}}
.summit circle{{fill:var(--copper)}}
.summit path{{fill:var(--copper)}}
.hero-copy{{position:relative;padding:110px 0 130px;max-width:620px}}
h1{{font:500 62px/1.02 var(--serif);letter-spacing:-.018em;margin:20px 0 26px;color:#f6f1e6}}
h1 em{{font-style:italic;color:var(--copper2)}}
.deck{{font-size:21px;line-height:1.55;color:var(--soft);max-width:600px}}
.byline{{margin-top:34px;display:flex;gap:26px;flex-wrap:wrap;font:600 11px/1 var(--mono);letter-spacing:.16em;text-transform:uppercase;color:#93a497}}
.byline b{{color:var(--text);font-weight:600}}
.legend{{position:absolute;right:32px;bottom:26px;font:600 10px var(--mono);letter-spacing:.14em;color:#6f8476;text-transform:uppercase}}

/* paper section */
.paper{{position:relative;background:var(--paper);color:var(--pink);overflow:hidden}}
.paper .topo-paper{{position:absolute;inset:0;width:100%;height:100%;opacity:.55}}
.topo-paper .c{{fill:none;stroke:#d6c9ac;stroke-width:1}}
.topo-paper .ci{{fill:none;stroke:#c9b892;stroke-width:1.5}}
.paper .wrap{{position:relative;padding:96px 32px}}
.paper .label{{color:var(--pcopper)}}
h2{{font:500 40px/1.12 var(--serif);letter-spacing:-.012em;margin:14px 0 22px;max-width:780px}}
.paper p{{color:#2b332e}}
.lede{{font-size:21px;line-height:1.55;max-width:760px}}
.notes{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:40px 0 30px}}
.note{{background:rgba(255,251,242,.72);border:1px solid #d3c5a6;padding:22px 22px 18px;position:relative}}
.note::before{{content:"";position:absolute;left:0;top:0;width:44px;height:3px;background:var(--pcopper)}}
.note h3{{font:600 19px/1.25 var(--serif);margin:10px 0 8px}}
.note p{{font-size:16px;line-height:1.5;margin:0;color:#3a433d}}
.note .src{{display:block;margin-top:12px;font:600 10.5px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:#7a6a4c}}
.edge{{font:italic 500 26px/1.35 var(--serif);border-left:3px solid var(--pcopper);padding:4px 0 4px 22px;max-width:760px;margin:34px 0 0}}

/* dark sections */
section.dark{{padding:96px 0;border-bottom:1px solid var(--line)}}
section.dark h2{{color:#f4eee2}}
section.dark p{{color:var(--soft)}}
.split{{display:grid;grid-template-columns:5fr 7fr;gap:56px;align-items:start}}
.split.fr{{grid-template-columns:7fr 5fr}}
.plate{{margin:0;background:var(--ink2);border:1px solid var(--line);padding:10px;box-shadow:0 30px 60px -30px rgba(0,0,0,.8)}}
.plate img{{display:block;width:100%;height:auto;border:1px solid #1d2723}}
.plate figcaption{{display:flex;gap:14px;align-items:baseline;padding:12px 4px 2px;font-size:14.5px;color:var(--soft)}}
.plate figcaption b{{font:700 10.5px var(--mono);letter-spacing:.16em;color:var(--copper);white-space:nowrap}}
.wide{{margin-top:44px}}

.profile{{width:100%;height:auto;display:block;margin:28px 0 8px;overflow:visible}}
.pg{{stroke:#1f2a24;stroke-width:1}}
.pr{{fill:none;stroke:var(--copper);stroke-width:2.4}}
.pd{{fill:var(--ink);stroke:var(--copper2);stroke-width:2.4}}
.pn{{font:700 10px var(--mono);fill:#8fa293;text-anchor:middle;letter-spacing:.08em}}
.pb{{font:700 10px var(--mono);fill:var(--copper2);text-anchor:middle;letter-spacing:.16em}}
.flag line{{stroke:var(--copper);stroke-width:2}} .flag path{{fill:var(--copper)}}
.parts{{list-style:none;margin:24px 0 0;padding:0;columns:3;column-gap:28px}}
.parts li{{break-inside:avoid;display:flex;gap:12px;padding:9px 0;border-top:1px solid var(--line);font-size:16px;color:var(--text)}}
.pnum{{font:700 11px/1.9 var(--mono);color:var(--copper);letter-spacing:.08em}}

.report{{background:var(--ink2);border:1px solid var(--line);padding:30px 30px 10px}}
.report .row{{display:grid;grid-template-columns:128px 1fr;gap:20px;padding:14px 0;border-top:1px solid var(--line)}}
.report .row:first-of-type{{border-top:0}}
.report .k{{font:700 10.5px/1.7 var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--copper)}}
.report .v{{font-size:16.5px;color:var(--soft)}}
.quote{{font:italic 21px/1.5 var(--serif);color:#f2ebdd;border-left:3px solid var(--copper);padding-left:20px;margin:6px 0 22px}}

.method{{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin-top:34px}}
.method div{{background:var(--ink);padding:22px 18px}}
.method b{{display:block;font:600 18px/1.25 var(--serif);color:var(--text);margin:10px 0 8px}}
.method p{{font-size:15px;line-height:1.5;margin:0}}

.limits{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:30px}}
.limit{{border:1px solid #d3c5a6;background:rgba(255,251,242,.6);padding:20px 22px}}
.limit p{{margin:0;font-size:16.5px}}
.ask{{counter-reset:a;margin:30px 0 0;padding:0;list-style:none}}
.ask li{{counter-increment:a;display:grid;grid-template-columns:70px 1fr;gap:18px;padding:22px 0;border-top:1px solid #d3c5a6}}
.ask li::before{{content:counter(a,decimal-leading-zero);font:500 40px/1 var(--serif);color:var(--pcopper)}}
.ask b{{display:block;font:600 21px/1.3 var(--serif);margin-bottom:6px;color:var(--pink)}}
.ask p{{margin:0;font-size:17px}}

footer{{padding:48px 0 70px;color:#93a497;font-size:15px}}
footer .label{{color:#93a497}}
footer p{{max-width:820px;color:#aab6ad}}

@media (max-width:860px){{
  h1{{font-size:38px}} h2{{font-size:28px}} .wrap{{padding:0 16px}} .paper .wrap{{padding:64px 16px}} .deck{{font-size:18px}} .hero{{min-height:0}} .hero-copy{{padding:64px 0 240px}}
  .notes,.split,.limits{{grid-template-columns:1fr}} .method{{grid-template-columns:1fr 1fr}} .parts{{columns:1}}
  .report .row{{grid-template-columns:1fr;gap:4px}} .legend{{display:none}}
}}
@media print{{
  html,body{{background:#fff;color:#000}} .hero,.paper,section.dark{{background:#fff!important}} .topo,.topo-paper,.over{{display:none}}
  h1,h2,.note h3,.ask b{{color:#000!important}} p,.deck,.v,td{{color:#222!important}} .plate,.report,.method div{{background:#fff;box-shadow:none}}
  section,.plate,.note,.ask li{{break-inside:avoid}} h2{{break-after:avoid}} p{{orphans:3;widows:3}}
}}
</style>
</head>
<body>

<header class="hero">
  {HERO}
  <svg class="over" viewBox="0 0 1600 760" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    {TICKS}
    <path class="route-glow" d="{route_d}"/><path class="route" d="{route_d}"/>
    {camp_svg}
    <g class="summit"><circle cx="1440" cy="190" r="9"/><line x1="1440" y1="181" x2="1440" y2="133" stroke="var(--copper)" stroke-width="2.4"/><path d="M1440 133 l30 10 -30 10z"/>
    <text x="1456" y="176" class="cl">SUMMIT</text><text x="1456" y="190" class="ce">SIGN-OFF</text></g>
  </svg>
  <div class="wrap">
    <div class="hero-copy">
      <div class="label">Field Academy · A proposal for Nous Research</div>
      <h1>A field test for the people who set up Hermes <em>for a living</em></h1>
      <p class="deck">Search Fiverr for a Hermes setup and you'll find sellers offering to install it on your server. Nothing on the listing tells a buyer which of them can keep it running once a key leaks or the scheduler stops. Field Academy is a working Hermes Desktop plugin that teaches the job, then tests it on client machines we've broken on purpose.</p>
      <div class="byline"><span>By <b>Damon Gardenhire</b></span><span>Prototype <b>0.8.0</b></span><span><b>October 2026</b></span></div>
    </div>
  </div>
  <div class="legend">Contours generated · Route: Messenger to Guide</div>
</header>

<section class="paper">
  {PAPER}
  <div class="wrap">
    <div class="label">The trade that already exists</div>
    <h2>People are paid to set up Hermes today, and buyers have no way to check them</h2>
    <p class="lede">Hermes setup has become a service before anyone has written down what a good one looks like. Three kinds of seller show up when you go looking.</p>
    <div class="notes">
      <div class="note"><div class="label">Marketplaces</div><h3>Gig listings for installs</h3><p>Fiverr and Contra both carry listings for Hermes Agent installation, configuration and troubleshooting on a VPS or a dedicated server.</p><span class="src">fiverr.com · contra.com</span></div>
      <div class="note"><div class="label">Consultants</div><h3>One-to-one architecture sessions</h3><p>Tony Simons, founder of AIowa, books sixty-minute Hermes sessions and works in four phases: deconstruct, architect, build and integrate, then staged verification.</p><span class="src">tonysimons.dev</span></div>
      <div class="note"><div class="label">Platforms</div><h3>Fleets of client computers</h3><p>Orgo's Hermes guide shows agencies how to run every client from one dashboard and clone a tested snapshot for each new client in a niche.</p><span class="src">docs.orgo.ai/guides/hermes</span></div>
    </div>
    <p class="edge">A certificate for finishing videos tells a dental practice nothing about the morning its AI key turns up in a shared backup.</p>
  </div>
</section>

<section class="dark">
  <div class="wrap split">
    <div>
      <div class="label">What it is</div>
      <h2>A trail map inside Hermes Desktop</h2>
      <p>Field Academy installs as a plugin and opens as its own page in the app. A learner picks a trail, climbs three camps from Beginner to Advanced, and ends at a summit. The trails take their names from Hermes's old jobs on Mount Olympus: Messenger (explain Hermes and spot where it fits), Traveler (run Hermes on your own computer), Crossroads (connect Hermes to a client's tools), Boundary Keeper (who owns what, who approves, how it recovers) and Guide (deploy and run Hermes for a client). A new learner starts with Messenger's first mission: give Hermes one small real job and write down what it did and what it got wrong.</p>
      <p>Twenty missions across the four learning trails, each in six steps: the story, a three-line takeaway, a half-done example to finish, a try in their own Hermes, an explanation in their own words, and a check. Practice prompts and scoring open a new chat and send themselves, and reading and video links wait at the end of each mission under Go deeper.</p>
      <p>The check is the part that matters. It reads real work on the learner's machine, like a scheduled job that has actually run or a document with every section filled in, and it can't be ticked by hand.</p>
      <p>The lessons link out to the people already teaching Hermes well: Tonbi's masterclass, Kevin Simback's Hermes Atlas and the Hermes Bible community.</p>
    </div>
    <figure class="plate"><img alt="The Field Academy trail map" src="{img('map.jpg')}"><figcaption><b>PLATE 1</b><span>The trail map: Messenger, Traveler, Crossroads and Boundary Keeper. Four trails for learning Hermes; the fifth, for client work, opens below them.</span></figcaption></figure>
  </div>
</section>

<section class="dark">
  <div class="wrap">
    <div class="label">The proposed credential</div>
    <h2>The Guide trail: four camps, nine parts, one signature</h2>
    <p class="lede" style="color:var(--soft)">The trail follows the order a working consultant uses: look at what's broken, decide the boundaries, build one real thing, then prove it survives. Each part below is graded on what the learner did, never on what they say they did.</p>
    {PROFILE}
    <ul class="parts">{parts_list}</ul>
    <figure class="plate wide"><img alt="The Guide path in Field Academy" src="{img('path.jpg')}"><figcaption><b>PLATE 2</b><span>The Guide path states what it certifies and what it doesn't, side by side, before a learner starts.</span></figcaption></figure>
  </div>
</section>

<section class="dark">
  <div class="wrap split fr">
    <div>
      <div class="label">Field report · Case 4100</div>
      <h2>The key in the open</h2>
      <p class="quote">"The company that runs our AI account sent us an alert about strange traffic on our key."</p>
      <div class="report">
        <div class="row"><div class="k">Client</div><div class="v">Birchwood Dental Partners, a fictional practice. The owner wants it fixed and written down, because the insurance form asks.</div></div>
        <div class="row"><div class="k">What they get</div><div class="v">A folder of 18 files standing in for the client's machine: configuration, logs, a backup script and a key that shouldn't be where it is. Every key in it is made up.</div></div>
        <div class="row"><div class="k">What they hand in</div><div class="v">The repaired files, an incident note saying what leaked, when, who was told and what stops it happening again, and a diagnosis in their own words.</div></div>
        <div class="row"><div class="k">How it's graded</div><div class="v">Scripts check the folder against criteria the learner never sees. Deleting the broken file fails. A half-fix fails. A repair copied from someone else fails, because each learner's case is seeded differently.</div></div>
        <div class="row"><div class="k">When they miss</div><div class="v">They're told what was missing and given one hint. A second miss shows a worked example. They can retry as often as they like.</div></div>
      </div>
      <p style="margin-top:22px">Three more labs follow it: a scheduled job running every minute on an expensive model, an office machine that doesn't come back after a power cut, and one shared key doing the work of five.</p>
    </div>
    <figure class="plate"><img alt="The key in the open lab" src="{img('lab.jpg')}"><figcaption><b>PLATE 3</b><span>The lab as a learner sees it: the client's note, the folder and what to hand in.</span></figcaption></figure>
  </div>
</section>

<section class="dark">
  <div class="wrap">
    <div class="label">How it teaches</div>
    <h2>Built on what the research says makes learning stick</h2>
    <div class="method">
      <div><div class="label">Review</div><b>Spaced recall</b><p>Passed missions come back at two days, a week, three weeks and two months. A miss returns the next day.</p></div>
      <div><div class="label">Support</div><b>Worked examples that fade</b><p>A finished example first, then a half-done one, then the learner alone.</p></div>
      <div><div class="label">Feedback</div><b>A ladder after a miss</b><p>What was missing, then a hint, then a worked example. Never just "not yet."</p></div>
      <div><div class="label">Placement</div><b>Skip what you know</b><p>A short check lets experienced people skip a level. It never skips the proof of real work.</p></div>
      <div><div class="label">Transfer</div><b>Your own problem</b><p>Each trail ends with a capstone on the learner's own work, graded against criteria they write.</p></div>
    </div>
    <p style="margin-top:22px;font-size:15.5px">The sources for each choice are listed in the plugin's notes. The review timings and pass marks are my own settings, and I've marked which citations I couldn't confirm.</p>
  </div>
</section>

<section class="dark">
  <div class="wrap split">
    <figure class="plate"><img alt="A sample Guide certificate" src="{img('cert.jpg')}"><figcaption><b>PLATE 4</b><span>A sample Guide certificate. The reviewer here isn't on a published list, and the certificate says so.</span></figcaption></figure>
    <div>
      <div class="label">The summit</div>
      <h2>A certificate that shows its working</h2>
      <p>The certificate lists the proof behind it: each lab's case number and the fingerprint of the repaired folder, the proposal's score, the drills and what Hermes's own records showed.</p>
      <p>It records the Hermes version it was earned on and asks for a re-check when the series changes, because a skill learned on one release can go stale on the next.</p>
      <p>It can't be fully issued by software alone. A named reviewer reads the learner's packet and signs it. Until then the learner holds "Guide, awaiting review."</p>
    </div>
  </div>
</section>

<section class="paper">
  <div class="wrap">
    <div class="label">What I can't claim yet</div>
    <h2>A prototype, tested by its own test suite and not yet by learners</h2>
    <div class="limits">
      <div class="limit"><p><b>No learner has taken it.</b> I don't know yet whether it teaches better than reading the docs.</p></div>
      <div class="limit"><p><b>It hasn't run on a live Hermes in this version.</b> The labs imitate a Hermes home, and I haven't confirmed where Hermes keeps its run history.</p></div>
      <div class="limit"><p><b>There's no reviewer yet.</b> The published reviewer list is empty, so no certificate can be fully issued.</p></div>
      <div class="limit"><p><b>It isn't a Nous credential,</b> and every certificate says so on its face. The 627 automated tests prove the plugin behaves as designed, nothing more.</p></div>
    </div>
    <div class="label" style="margin-top:64px">What I'm asking Nous for</div>
    <h2>Three things would turn this into something people can trust</h2>
    <ol class="ask">
      <li><div><b>A view on whether a practitioner credential should exist</b><p>And, if it should, who ought to stand behind it.</p></div></li>
      <li><div><b>A decision on who would review, if anyone</b><p>No reviewers have been appointed or approached. If the Guide certificate should exist, who reviews the rubric and signs is Nous's call.</p></div></li>
      <li><div><b>Two facts about Hermes</b><p>How releases are numbered, and where run history lives, so the evidence checks rest on fact.</p></div></li>
    </ol>
  </div>
</section>

<footer>
  <div class="wrap">
    <div class="label">Credits</div>
    <p>Nous Research for Hermes Agent and the Beginner, Intermediate and Advanced level names from its Learning Path page. Tonbi, Kevin Simback and the Hermes Bible community for the lessons the missions link to. Tony Simons for the shape of the deployment lifecycle, read from tonysimons.dev; he hasn't reviewed or endorsed this work. Orgo for its published model of running Hermes for many clients.</p>
    <p>Prepared as a concept document. Nothing here has been published, and Field Academy isn't on a public repository.</p>
  </div>
</footer>
</body>
</html>
"""

(HERE / "concept-brief-nous.html").write_text(HTML)
print("wrote", HERE / "concept-brief-nous.html", len(HTML) // 1024, "KB")
