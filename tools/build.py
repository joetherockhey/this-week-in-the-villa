"""data/trends.json + data/shots.json -> index.html, a frozen copy in archive/<monday>/, and archive/index.html
(all past reports plus each trend's history). Raw data is kept in data/weeks/.

trends.json is kept in rank order: evergreen trends first, then seasonal, each by usage_n (videos made).
"""
import json, html, datetime, pathlib, shutil, urllib.parse, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
trends = json.loads((ROOT / "data/trends.json").read_text("utf-8"))
shots = json.loads((ROOT / "data/shots.json").read_text("utf-8"))
today = datetime.date.today()
monday = today - datetime.timedelta(days=today.weekday())
wk = f"{monday.day} {monday:%B %Y}"
e = lambda s: html.escape(str(s or ""))
STATUS = {"Rising": "rise", "Peaking": "peak", "Steady": "flat", "Past peak": "fade"}
day = lambda d: f"{d.day} {d:%b %Y}"

# Every week each trend was listed. ponytail: matched by exact name, so keep a trend's name the same between weeks.
(ROOT / "data/weeks").mkdir(exist_ok=True)
shutil.copy(ROOT / "data/trends.json", ROOT / f"data/weeks/{monday}.json")
weeks = {datetime.date.fromisoformat(p.stem): json.loads(p.read_text("utf-8")) for p in sorted((ROOT / "data/weeks").glob("*.json"))}
hist = {}
for w, ts in weeks.items():
    for i, t in enumerate(ts, 1):
        hist.setdefault(t["name"], []).append((w, i, t))


def host(u):
    return urllib.parse.urlparse(u).netloc.replace("www.", "")


def who(u):
    """@handle and upload date (TikTok video ids carry their upload time in the top 32 bits)."""
    m = re.search(r"tiktok\.com/@([^/]+)/video/(\d+)", u)
    if not m: return "Instagram reel" if "instagram.com" in u else host(u)
    d = datetime.datetime.fromtimestamp(int(m.group(2)) >> 32, datetime.UTC).date()
    return f"@{m.group(1)}, {d.day} {d:%b %Y}"


def short(n):
    if not n: return ""
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div: return f"{n / div:.1f}".rstrip("0").rstrip(".") + suf
    return str(n)


def examples(t):
    rows = []
    for x in t["examples"]:
        stats = " · ".join(s for s in (f"{short(x.get('plays'))} plays" if x.get("plays") else "",
                                        f"{short(x.get('likes'))} likes" if x.get("likes") else "") if s)
        rows.append(f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener">{e(who(x["url"]).split(",")[0])}</a>'
                    f'<span>{e(stats)}{" · " + e(x["note"]) if x.get("note") else ""}</span></li>')
    return "".join(rows)


def row(i, t):
    return (f'<tr><td class="rk">{i}</td><td><a href="#t{i}">{e(t["name"])}</a></td>'
            f'<td class="st {STATUS.get(t["status"], "flat")}">{e(t["status"])}</td>'
            f'<td class="num">{short(t.get("usage_n")) or "n/a"}</td>'
            f'<td class="when">{"Any week" if t["longevity"] == "evergreen" else "To " + e(re.sub(r" \d{4}$", "", t.get("ends") or ""))}</td></tr>')


def card(i, t):
    shot = shots.get(str(i))
    if shot and shot["kind"] == "ai":
        cap = "AI illustration. No example post could be captured."
    elif shot:
        cap = f'<a href="{e(shot["url"])}" target="_blank" rel="noopener">{e(who(shot["url"]))}</a>'
    img = (f'<figure><img src="img/{i}.jpg?v={today}" alt="{"AI illustration" if shot["kind"] == "ai" else "Example post"} for {e(t["name"])}" loading="lazy">'
           f'<figcaption>{cap}</figcaption></figure>' if shot else '<figure class="noimg"></figure>')
    sound = (f'<a href="{e(t["sound_url"])}" target="_blank" rel="noopener">{e(t["sound"])}</a>' if t.get("sound_url") else e(t.get("sound"))) or "No set sound. It's a format."
    risk = f'<dt>Watch out</dt><dd>{e(t["risk"])}</dd>' if t.get("risk") else ""
    srcs = ", ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(host(u))}</a>' for u in t["sources"])
    first = hist[t["name"]][0]
    was = f", {short(first[2].get('usage_n'))} videos then" if first[2].get("usage_n") else ""
    listed = f"Since the week of {day(first[0])}{was}" if first[0] < monday else "New this week"
    when = "Works any week" if t["longevity"] == "evergreen" else f"Time-bound, runs until {e(t.get('ends'))}"
    return f"""
<article class="trend" id="t{i}">
  {img}
  <div class="body">
    <p class="meta"><span class="rk">{i:02d}</span><span class="st {STATUS.get(t["status"], "flat")}">{e(t["status"])}</span><span>{when}</span><span>{e(" + ".join(t["platforms"]))}</span></p>
    <h3>{e(t["name"])}</h3>
    <p class="what">{e(t["what"])}</p>
    <dl>
      <dt>Usage</dt><dd>{e(t["usage"])}</dd>
      <dt>Origin</dt><dd>{e(t["origin"])}</dd>
      <dt>On this list</dt><dd>{e(listed)}</dd>
      <dt>Sound</dt><dd>{sound}</dd>
      <dt>Brand idea</dt><dd>{e(t["brand_use"])}</dd>
      {risk}
    </dl>
    <ul class="ex">{examples(t)}</ul>
    <p class="src">Sources: {srcs}</p>
  </div>
</article>"""


ever = [(i, t) for i, t in enumerate(trends, 1) if t["longevity"] == "evergreen"]
seas = [(i, t) for i, t in enumerate(trends, 1) if t["longevity"] != "evergreen"]
table = lambda rows: "".join(row(i, t) for i, t in rows)

page = f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trend Report · Week of {wk}</title>
<meta name="description" content="{len(trends)} social trends ranked by how much they're used, for the week of {wk}.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&family=Oswald:wght@600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#fafaf9;--ink:#1c1b1a;--soft:#44423f;--muted:#6f6c68;--line:#e4e2df;--red:#e2361b;--rise:#1f7a4d;--fade:#8a8580}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151413;--ink:#ecebe8;--soft:#c9c7c3;--muted:#99958f;--line:#2e2c2a;--red:#ff5a3c;--rise:#4cc38a;--fade:#8a8580}}}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--ink);font:400 16px/1.55 Geist,system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
a{{color:inherit;text-underline-offset:3px;text-decoration-color:var(--line)}}
a:hover{{color:var(--red);text-decoration-color:currentColor}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 32px}}
header{{display:flex;justify-content:space-between;align-items:center;height:68px;border-bottom:1px solid var(--line)}}
.mark{{font:600 30px/1 Oswald,sans-serif;color:var(--red);letter-spacing:-.02em;text-decoration:none;display:flex;align-items:center;gap:6px}}
.mark i{{width:18px;height:18px;border-radius:50% 50% 50% 6px;background:var(--red)}}
header span,.meta,.ex span,.src,figcaption,th,.num,.when,.rk{{font-family:"Geist Mono",monospace;font-size:12.5px}}
header span{{color:var(--muted)}}
.intro{{padding:56px 0 40px;max-width:720px}}
h1{{font:700 clamp(32px,4.5vw,48px)/1.08 Geist,sans-serif;letter-spacing:-.03em;margin-bottom:16px}}
.intro p{{color:var(--soft);font-size:18px;max-width:60ch}}
h2{{font:600 20px/1.2 Geist,sans-serif;letter-spacing:-.01em;margin:40px 0 4px}}
h2+p{{color:var(--muted);font-size:15px;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;font-weight:400;color:var(--muted);padding:8px 12px 8px 0;border-bottom:1px solid var(--ink)}}
td{{padding:11px 12px 11px 0;border-bottom:1px solid var(--line);vertical-align:baseline}}
td a{{text-decoration:none;font-weight:500}}
.rk{{color:var(--muted);width:3em}} .num{{text-align:right;width:7em}} th.num{{text-align:right}} .when{{color:var(--muted);width:9em;padding-left:24px;white-space:nowrap}}
.st{{font-family:"Geist Mono",monospace;font-size:12.5px;width:7em}}
.st.rise{{color:var(--rise)}} .st.peak{{color:var(--red)}} .st.fade{{color:var(--fade)}} .st.flat{{color:var(--muted)}}
.section-break{{margin-top:80px;padding-top:24px;border-top:1px solid var(--ink)}}
.trend{{display:grid;grid-template-columns:240px 1fr;gap:40px;padding:40px 0;border-bottom:1px solid var(--line);scroll-margin-top:12px}}
figure img{{width:100%;aspect-ratio:9/14;object-fit:cover;object-position:top;border-radius:6px;display:block;background:var(--line)}}
figcaption{{margin-top:8px;color:var(--muted)}}
.noimg{{aspect-ratio:9/14;border-radius:6px;background:var(--line)}}
.meta{{display:flex;flex-wrap:wrap;gap:6px 18px;color:var(--muted)}}
.meta .rk{{color:var(--ink);width:auto}}
h3{{font:600 clamp(24px,3vw,30px)/1.15 Geist,sans-serif;letter-spacing:-.02em;margin:10px 0 10px}}
.what{{font-size:18px;color:var(--soft);max-width:62ch}}
dl{{display:grid;grid-template-columns:7.5em 1fr;gap:10px 16px;margin:22px 0;max-width:68ch;font-size:15.5px}}
dt{{color:var(--muted);font-size:14px}}
.ex{{list-style:none;display:grid;gap:6px;font-size:15px}}
.ex li{{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline}}
.ex a{{font-weight:500}} .ex span{{color:var(--muted)}}
.src{{margin-top:16px;color:var(--muted);font-size:11.5px}}
.intro .past{{margin-top:22px}}
.btn{{display:inline-flex;align-items:center;gap:10px;min-height:44px;padding:0 18px;border-radius:8px;background:var(--ink);color:var(--bg);font-size:15px;font-weight:500;text-decoration:none}}
.btn:hover{{background:var(--red);color:var(--bg)}}
.btn:focus-visible{{outline:2px solid var(--red);outline-offset:2px}}
footer{{padding:40px 0 64px;color:var(--muted);font-size:14px;display:grid;gap:10px;max-width:72ch}}
@media (max-width:760px){{
  .wrap{{padding:0 16px}} .intro{{padding:36px 0 24px}}
  .when,th.whenh{{display:none}}
  .trend{{grid-template-columns:1fr;gap:20px}} figure{{max-width:260px}}
  dl{{grid-template-columns:1fr;gap:2px}} dd{{margin-bottom:10px}}
}}
</style>
</head>
<body>
<div class="wrap">
<header><a class="mark" href="./"><i></i>apparent</a><span>Week of {wk}</span></header>
<section class="intro">
  <h1>Social trend report</h1>
  <p>{len(trends)} TikTok and Reels trends, ranked by how many videos use them. Trends a brand can run any week sit at the top. Ones tied to a date sit lower.</p>
  <p class="past"><a class="btn" href="archive/">Past reports and trend history <span aria-hidden="true">→</span></a></p>
</section>
<h2>Works any week</h2>
<p>Not tied to a date. Ranked by videos made.</p>
<table><thead><tr><th>#</th><th>Trend</th><th>Status</th><th class="num">Videos</th><th class="when whenh">Window</th></tr></thead><tbody>{table(ever)}</tbody></table>
<h2>Time-bound</h2>
<p>Still being made, but they end with the date. Post soon or skip.</p>
<table><thead><tr><th>#</th><th>Trend</th><th>Status</th><th class="num">Videos</th><th class="when whenh">Window</th></tr></thead><tbody>{table(seas)}</tbody></table>
<div class="section-break"></div>
<main>{"".join(card(i, t) for i, t in enumerate(trends, 1))}</main>
<footer id="how">
  <p>How this works: each Monday the latest round-ups (New Engen, SocialPilot, Buffer, Postdom and others) are checked against the live TikTok sound pages. Video counts come from the sound page or the round-up quoting them, as of the date shown. Plays and likes on the examples come from TikTok's own post data at the time of checking.</p>
  <p>Example images are the cover frames of the linked posts, shown for reference. Check a sound's licensing before using it on a brand account.</p>
  <p>Compiled {today.day} {today:%B %Y}.</p>
</footer>
</div>
</body>
</html>
"""
(ROOT / "index.html").write_text(page, "utf-8")

# Freeze this week. Images are numbered and reused every week, so each report keeps its own copy.
snap = ROOT / "archive" / str(monday)
snap.mkdir(parents=True, exist_ok=True)
(snap / "index.html").write_text(page.replace('href="archive/"', 'href="../"').replace('href="./"', 'href="../../"'), "utf-8")
shutil.copytree(ROOT / "img", snap / "img", dirs_exist_ok=True)

# archive/index.html: every report, then every trend with when it first showed up.
reports = "".join(f'<tr><td><a href="{w}/">Week of {w.day} {w:%B %Y}</a></td><td class="num">{len(ts)} trends</td></tr>'
                  for w, ts in sorted(weeks.items(), reverse=True))


def hist_row(seen):
    (w0, _, t0), (w1, i1, t1) = seen[0], seen[-1]
    a, b = short(t0.get("usage_n")) or "n/a", short(t1.get("usage_n")) or "n/a"
    return (f'<tr><td><a href="{w1}/#t{i1}">{e(t1["name"])}</a><span class="origin">{e(t1["origin"])}</span></td>'
            f'<td class="first">{day(w0)}</td><td class="when">{"This week" if w1 == monday else day(w1)}</td>'
            f'<td class="num">{a if w0 == w1 else a + " → " + b}</td></tr>')


rows = "".join(hist_row(s) for s in sorted(hist.values(), key=lambda s: (s[0][0], s[-1][2].get("usage_n") or 0), reverse=True))
style = re.search(r"<style>.*?</style>", page, re.S).group(0).replace("</style>", """.first{font-family:"Geist Mono",monospace;font-size:12.5px;color:var(--muted);white-space:nowrap}
.origin{display:block;color:var(--muted);font-size:14px;margin-top:2px}
.num{width:auto;white-space:nowrap}
th{white-space:nowrap}
@media (max-width:760px){.num{white-space:normal;padding-right:0}.first{white-space:normal}}
</style>""")
fonts = re.search(r'<link rel="preconnect".*?rel="stylesheet">', page, re.S).group(0)
(ROOT / "archive/index.html").write_text(f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Past Trend Reports</title>
{fonts}
{style}
</head>
<body>
<div class="wrap">
<header><a class="mark" href="../"><i></i>apparent</a><span>Past reports</span></header>
<section class="intro">
  <h1>Past reports</h1>
  <p>Every weekly report as it ran, and when each trend first made the list.</p>
</section>
<h2>Weekly reports</h2>
<p>Each one is frozen as it was published.</p>
<table><tbody>{reports}</tbody></table>
<h2>Trend history</h2>
<p>Newest to the list first. The line under each name says when the trend actually began. Videos show the count when first listed, then when last listed.</p>
<table><thead><tr><th>Trend</th><th>First listed</th><th class="when whenh">Last listed</th><th class="num">Videos</th></tr></thead><tbody>{rows}</tbody></table>
<footer></footer>
</div>
</body>
</html>
""", "utf-8")
assert all((ROOT / f"archive/{w}/index.html").exists() for w in weeks), "a week in data/weeks has no archived page"
print("built", len(trends), "trends,", len(weeks), "weeks archived")
